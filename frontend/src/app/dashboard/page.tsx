"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { SavedRecipeResponse } from "@/lib/frontend-types";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { getErrorMessage, LoadingState, PageShell, useRequireAuth } from "@/lib/route-helpers";

const RECIPES_PER_PAGE = 16;

function isCommunitySaved(recipe: SavedRecipeResponse): boolean {
  return !!(recipe.copied_from_user_id && recipe.copied_from_saved_recipe_id);
}

type StatusFilter = "all" | "published" | "private" | "community";
type DateFilter = "all" | "30d" | "90d" | "year";
type SortOption = "newest" | "oldest" | "az" | "za";

export default function DashboardPage() {
  const { api, signOut } = useAuth();
  const { user, loading, isAuthenticated } = useRequireAuth();
  const [recipes, setRecipes] = useState<SavedRecipeResponse[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [dateFilter, setDateFilter] = useState<DateFilter>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    const load = async () => {
      setFetching(true);
      setError(null);
      try {
        const data = await api.fetch<SavedRecipeResponse[]>("/api/users/me/saved-recipes");
        setRecipes(data);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setFetching(false);
      }
    };
    void load();
  }, [api, isAuthenticated, loading]);

  useEffect(() => {
    setCurrentPage(1);
  }, [dateFilter, searchQuery, sortBy, statusFilter]);

  const filteredSortedRecipes = useMemo(() => {
    const search = searchQuery.trim().toLowerCase();
    const now = Date.now();
    const dateThresholdByFilter: Record<Exclude<DateFilter, "all">, number> = {
      "30d": now - 30 * 24 * 60 * 60 * 1000,
      "90d": now - 90 * 24 * 60 * 60 * 1000,
      year: now - 365 * 24 * 60 * 60 * 1000,
    };

    const filtered = recipes.filter((recipe) => {
      const community = isCommunitySaved(recipe);
      if (statusFilter === "published" && (!recipe.published || community)) return false;
      if (statusFilter === "private" && (recipe.published || community)) return false;
      if (statusFilter === "community" && !community) return false;

      if (dateFilter !== "all") {
        const savedAt = new Date(recipe.saved_at).getTime();
        if (!Number.isFinite(savedAt) || savedAt < dateThresholdByFilter[dateFilter]) return false;
      }

      if (search) {
        const title = (recipe.converted_recipe?.title || `Recipe ${recipe.recipe_id}`).toLowerCase();
        const notes = (recipe.notes || "").toLowerCase();
        return title.includes(search) || notes.includes(search);
      }

      return true;
    });

    return filtered.sort((a, b) => {
      const aTitle = (a.converted_recipe?.title || `Recipe ${a.recipe_id}`).toLowerCase();
      const bTitle = (b.converted_recipe?.title || `Recipe ${b.recipe_id}`).toLowerCase();
      const aSaved = new Date(a.saved_at).getTime();
      const bSaved = new Date(b.saved_at).getTime();

      switch (sortBy) {
        case "oldest":
          return aSaved - bSaved;
        case "az":
          return aTitle.localeCompare(bTitle);
        case "za":
          return bTitle.localeCompare(aTitle);
        case "newest":
        default:
          return bSaved - aSaved;
      }
    });
  }, [dateFilter, recipes, searchQuery, sortBy, statusFilter]);

  const totalFiltered = filteredSortedRecipes.length;
  const totalPages = Math.max(1, Math.ceil(totalFiltered / RECIPES_PER_PAGE));

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const paginatedRecipes = useMemo(() => {
    const start = (currentPage - 1) * RECIPES_PER_PAGE;
    return filteredSortedRecipes.slice(start, start + RECIPES_PER_PAGE);
  }, [currentPage, filteredSortedRecipes]);

  const visiblePageNumbers = useMemo(() => {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
    if (currentPage <= 4) return [1, 2, 3, 4, 5, totalPages];
    if (currentPage >= totalPages - 3) return [1, totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    return [1, currentPage - 1, currentPage, currentPage + 1, totalPages];
  }, [currentPage, totalPages]);

  return (
    <PageShell showLoggedInHeader={false}>
      <Card className="mb-6">
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <Image
              src="/branding/mmp-logo-primary.svg"
              alt="Major Meal Prep logo"
              width={640}
              height={220}
              className="h-auto w-full"
              priority
            />
          </div>

          <div>
            <CardTitle className="text-5xl">Dashboard</CardTitle>
            <CardDescription className="mt-3 text-base">
              Welcome back. Command center for {user?.email || "your account"}.
            </CardDescription>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/generate">
                <Button className="px-6 py-3 text-base">Generate Recipe</Button>
              </Link>
              <Link href="/recipes">
                <Button variant="secondary" className="px-6 py-3 text-base">
                  Browse Community Recipes
                </Button>
              </Link>
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href="/settings">
                <Button variant="secondary" className="px-4 py-2 text-xs">
                  Account Settings
                </Button>
              </Link>
              <Button variant="secondary" className="px-4 py-2 text-xs" onClick={() => signOut()}>
                Sign Out
              </Button>
            </div>
            <p className="text-(--color-primary-text)/70 mt-6 text-sm font-bold uppercase tracking-[0.04em]">
              Your saved collection stays available on the free tier. Only AI recipe generation requires a paid plan.
            </p>
          </div>
        </div>
      </Card>

      <Card className="mb-6 bg-[#7B806A]">
        <p className="text-(--color-primary-text)/75 text-xs font-black uppercase tracking-[0.08em]">
          Saved Recipes
        </p>
        <CardTitle className="mt-2 text-4xl">Your Recipe Collection</CardTitle>
        <CardDescription className="mt-3 text-sm">
          Open, review, and manage your saved conversions in one place.
        </CardDescription>
      </Card>

      <Card className="mb-6">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="block">
            <span className="mb-1 block text-xs font-black uppercase tracking-[0.08em] text-(--color-primary-text)/75">
              Search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search title or notes..."
              className="w-full border-3 border-black bg-background px-3 py-2 text-sm font-bold uppercase tracking-[0.03em] outline-none"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black uppercase tracking-[0.08em] text-(--color-primary-text)/75">
              Status
            </span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              className="w-full border-3 border-black bg-background px-3 py-2 text-sm font-bold uppercase tracking-[0.03em] outline-none"
            >
              <option value="all">All</option>
              <option value="published">Published</option>
              <option value="private">Private</option>
              <option value="community">Community</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black uppercase tracking-[0.08em] text-(--color-primary-text)/75">
              Date Range
            </span>
            <select
              value={dateFilter}
              onChange={(event) => setDateFilter(event.target.value as DateFilter)}
              className="w-full border-3 border-black bg-background px-3 py-2 text-sm font-bold uppercase tracking-[0.03em] outline-none"
            >
              <option value="all">All Time</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="year">This Year</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-black uppercase tracking-[0.08em] text-(--color-primary-text)/75">
              Sort
            </span>
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as SortOption)}
              className="w-full border-3 border-black bg-background px-3 py-2 text-sm font-bold uppercase tracking-[0.03em] outline-none"
            >
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
              <option value="az">A-Z</option>
              <option value="za">Z-A</option>
            </select>
          </label>
        </div>
        <p className="mt-4 text-xs font-black uppercase tracking-[0.06em] text-(--color-primary-text)/70">
          Showing {totalFiltered} of {recipes.length} recipes
        </p>
      </Card>

      {loading || fetching ? <LoadingState label="Loading saved recipes..." /> : null}
      {error ? (
        <Card className="mb-4 bg-[#B84C2A]">
          <p className="text-sm font-black uppercase tracking-[0.06em] text-black">{error}</p>
        </Card>
      ) : null}

      {!fetching && !error && recipes.length === 0 ? (
        <Card>
          <p className="text-sm font-bold uppercase tracking-[0.04em] text-(--color-primary-text)/80">
            No saved recipes yet. Try browsing the community recipe collection or generating one.
          </p>
        </Card>
      ) : null}

      {!fetching && !error && recipes.length > 0 && totalFiltered === 0 ? (
        <Card className="mb-6">
          <p className="text-sm font-bold uppercase tracking-[0.04em] text-(--color-primary-text)/80">
            No recipes match your current search and filters. Try broadening your criteria.
          </p>
        </Card>
      ) : null}

      {!fetching && !error && totalFiltered > 0 ? (
        <>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {paginatedRecipes.map((recipe) => (
              <li key={recipe.id}>
                <Card className="flex h-full flex-col bg-(--color-surface)">
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <h2 className="max-h-[3.2rem] overflow-hidden text-(--color-primary-text) font-heading text-xl leading-tight tracking-[0.04em] uppercase">
                      {recipe.converted_recipe?.title || `Recipe ${recipe.recipe_id}`}
                    </h2>
                  </div>
                  <span className="mb-3 text-xs font-bold uppercase tracking-[0.04em] text-(--color-primary-text)/65">
                    {new Date(recipe.saved_at).toLocaleString()}
                  </span>
                  <p className="mb-4 max-h-[3.6rem] overflow-hidden text-xs font-bold uppercase tracking-[0.03em] text-(--color-primary-text)/80">
                    {recipe.notes
                      ? `${recipe.notes.slice(0, 150)}${recipe.notes.length > 150 ? "..." : ""}`
                      : "No notes added."}
                  </p>
                  <div className="mt-auto flex items-center justify-between gap-2">
                    <Link href={`/recipes/${user?.uid}/${recipe.id}`}>
                      <Button className="text-xs">View</Button>
                    </Link>
                    <span className="text-[10px] font-black uppercase tracking-[0.08em] text-(--color-primary-text)/70">
                      {isCommunitySaved(recipe) ? "Community" : recipe.published ? "Published" : "Private"}
                    </span>
                  </div>
                </Card>
              </li>
            ))}
          </ul>

          {totalPages > 1 ? (
            <Card className="mt-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs font-black uppercase tracking-[0.06em] text-(--color-primary-text)/70">
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    variant="secondary"
                    className="px-3 py-1.5 text-xs"
                    onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                    disabled={currentPage === 1}
                  >
                    Prev
                  </Button>
                  {visiblePageNumbers.map((pageNum, index) => {
                    const previous = visiblePageNumbers[index - 1];
                    const showGap = index > 0 && previous && pageNum - previous > 1;

                    return (
                      <div key={`page-${pageNum}`} className="flex items-center gap-2">
                        {showGap ? (
                          <span className="text-xs font-black uppercase tracking-[0.06em] text-(--color-primary-text)/60">
                            ...
                          </span>
                        ) : null}
                        <Button
                          variant={currentPage === pageNum ? "default" : "secondary"}
                          className="px-3 py-1.5 text-xs"
                          onClick={() => setCurrentPage(pageNum)}
                        >
                          {pageNum}
                        </Button>
                      </div>
                    );
                  })}
                  <Button
                    variant="secondary"
                    className="px-3 py-1.5 text-xs"
                    onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </Card>
          ) : null}
        </>
      ) : null}
    </PageShell>
  );
}
