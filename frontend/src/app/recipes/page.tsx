"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { PaginatedPublishedResponse, PublishedRecipeSummary } from "@/lib/frontend-types";
import { AppNav, getErrorMessage, LoadingState, PageShell } from "@/lib/route-helpers";

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
    <PageShell>
      <AppNav />
      <h1 className="mb-2 text-3xl font-bold">Published Recipes</h1>
      <p className="mb-4 text-neutral-400">Browse published community recipes.</p>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by recipe title (client-side stub)"
        className="mb-6 w-full rounded border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 placeholder-neutral-500"
      />

      {fetching ? <LoadingState label="Loading published recipes..." /> : null}
      {error ? <p className="mb-4 rounded border border-red-700 bg-red-950 p-3 text-red-300">{error}</p> : null}

      <ul className="space-y-3">
        {filteredItems.map((item) => (
          <li key={`${item.owner_user_id}-${item.saved_recipe_id}`} className="rounded border border-neutral-800 bg-neutral-900 p-4">
            <h2 className="font-semibold text-neutral-100">{item.converted_recipe?.title || "Untitled recipe"}</h2>
            <p className="mb-2 text-xs text-neutral-500">Published {new Date(item.saved_at).toLocaleString()}</p>
            <Link
              href={`/recipes/${item.owner_user_id}/${item.saved_recipe_id}`}
              className="text-sm font-medium text-lime-400 hover:text-lime-300"
            >
              View details
            </Link>
          </li>
        ))}
      </ul>

      {cursor ? (
        <button
          onClick={() => void loadPublished(cursor)}
          disabled={loadingMore}
          className="mt-6 rounded border border-neutral-700 px-4 py-2 text-sm text-neutral-200 hover:bg-neutral-800 disabled:opacity-50"
        >
          {loadingMore ? "Loading..." : "Load more"}
        </button>
      ) : null}
    </PageShell>
  );
}
