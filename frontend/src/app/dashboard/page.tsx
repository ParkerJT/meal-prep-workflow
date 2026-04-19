"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { SavedRecipeResponse } from "@/lib/frontend-types";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { getErrorMessage, LoadingState, PageShell, useRequireAuth } from "@/lib/route-helpers";

export default function DashboardPage() {
  const { api, signOut } = useAuth();
  const { user, loading, isAuthenticated } = useRequireAuth();
  const [recipes, setRecipes] = useState<SavedRecipeResponse[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <PageShell>
      <Card className="mb-6">
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
              Browse Recipes
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
      </Card>

      <Card className="mb-6">
        <CardTitle className="text-4xl">My Saved Collection</CardTitle>
        <p className="text-(--color-primary-text)/70 mt-3 text-sm font-bold uppercase tracking-[0.04em]">
          Your saved collection stays available on the free tier. Only AI recipe generation requires a paid plan.
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
            No saved recipes yet. Try browsing published recipes or generating one.
          </p>
        </Card>
      ) : null}

      <ul className="space-y-3">
        {recipes.map((recipe) => (
          <li key={recipe.id}>
            <Card className="bg-(--color-surface)">
            <div className="mb-1 flex items-center justify-between gap-3">
              <h2 className="text-(--color-primary-text) font-heading text-3xl leading-none tracking-[0.05em] uppercase">
                {recipe.converted_recipe?.title || `Recipe ${recipe.recipe_id}`}
              </h2>
              <span className="text-(--color-primary-text)/70 text-xs font-bold uppercase tracking-[0.04em]">
                {new Date(recipe.saved_at).toLocaleString()}
              </span>
            </div>
            <p className="text-(--color-primary-text)/80 mb-4 text-sm font-bold uppercase tracking-[0.03em]">
              {recipe.notes ? `${recipe.notes.slice(0, 120)}${recipe.notes.length > 120 ? "..." : ""}` : "No notes added."}
            </p>
            <div className="flex items-center gap-3">
              <Link href={`/recipes/${user?.uid}/${recipe.id}`}>
                <Button className="text-sm">Open Detail</Button>
              </Link>
              <span className="text-(--color-primary-text)/70 text-xs font-bold uppercase tracking-[0.04em]">
                {recipe.published ? "Published" : "Private Save"}
              </span>
            </div>
            </Card>
          </li>
        ))}
      </ul>
    </PageShell>
  );
}
