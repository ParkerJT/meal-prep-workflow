"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { PaginatedPublishedResponse, PublishedRecipeSummary } from "@/lib/frontend-types";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getErrorMessage, LoadingState, LoggedInUtilityHeader, PageShell } from "@/lib/route-helpers";

export default function RecipesPage() {
  const { api } = useAuth();
  const [items, setItems] = useState<PublishedRecipeSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [fetching, setFetching] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const loadPublished = useCallback(async (nextCursor?: string | null) => {
    const isLoadMore = !!nextCursor;
    if (isLoadMore) setLoadingMore(true);
    else setFetching(true);
    setError(null);
    try {
      const query = new URLSearchParams({ limit: "20" });
      if (nextCursor) query.set("cursor", nextCursor);
      const data = await api.fetch<PaginatedPublishedResponse>(`/api/published-recipes?${query.toString()}`);
      setCursor(data.next_cursor);
      setItems((prev) => (isLoadMore ? [...prev, ...data.items] : data.items));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setFetching(false);
      setLoadingMore(false);
    }
  }, [api]);

  useEffect(() => {
    void loadPublished();
  }, [loadPublished]);

  const filteredItems = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return items;
    return items.filter((item) => (item.converted_recipe?.title || "").toLowerCase().includes(term));
  }, [items, search]);

  return (
    <PageShell showLoggedInHeader={false}>
      <LoggedInUtilityHeader />
      <Card className="mb-4">
        <CardTitle className="text-5xl">Published Recipes</CardTitle>
        <CardDescription className="mt-3 text-base">Browse published community recipes.</CardDescription>
      </Card>

      <Input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by recipe title (client-side stub)"
        className="mb-6 text-sm normal-case tracking-normal"
      />

      {fetching ? <LoadingState label="Loading published recipes..." /> : null}
      {error ? (
        <Card className="mb-4 bg-[#B84C2A]">
          <p className="text-sm font-black uppercase tracking-[0.06em] text-black">{error}</p>
        </Card>
      ) : null}

      <ul className="space-y-3">
        {filteredItems.map((item) => (
          <li key={`${item.owner_user_id}-${item.saved_recipe_id}`}>
            <Card>
              <h2 className="text-(--color-primary-text) font-heading text-3xl uppercase tracking-[0.05em]">
                {item.converted_recipe?.title || "Untitled Recipe"}
              </h2>
              <p className="text-(--color-primary-text)/70 mb-3 text-xs font-bold uppercase tracking-[0.04em]">
                Published {new Date(item.saved_at).toLocaleString()}
              </p>
              <Link href={`/recipes/${item.owner_user_id}/${item.saved_recipe_id}`}>
                <Button className="text-sm">View Details</Button>
              </Link>
            </Card>
          </li>
        ))}
      </ul>

      {cursor ? (
        <Button
          onClick={() => void loadPublished(cursor)}
          disabled={loadingMore}
          variant="secondary"
          className="mt-6 text-sm"
        >
          {loadingMore ? "Loading..." : "Load More"}
        </Button>
      ) : null}
    </PageShell>
  );
}
