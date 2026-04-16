"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { SavedRecipeResponse } from "@/lib/frontend-types";
import { AppNav, getErrorMessage, LoadingState, PageShell, useRequireAuth } from "@/lib/route-helpers";

export default function DashboardPage() {
  const { api } = useAuth();
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
      <AppNav />
      <h1 className="mb-2 text-3xl font-bold">Dashboard</h1>
      <p className="mb-6 text-neutral-400">Saved recipes for {user?.email || "your account"}.</p>

      {loading || fetching ? <LoadingState label="Loading saved recipes..." /> : null}
      {error ? <p className="mb-4 rounded border border-red-700 bg-red-950 p-3 text-red-300">{error}</p> : null}

      {!fetching && !error && recipes.length === 0 ? (
        <p className="text-neutral-400">No saved recipes yet. Try browsing published recipes or generating one.</p>
      ) : null}

      <ul className="space-y-3">
        {recipes.map((recipe) => (
          <li key={recipe.id} className="rounded border border-neutral-800 bg-neutral-900 p-4">
            <div className="mb-1 flex items-center justify-between gap-3">
              <h2 className="font-semibold text-neutral-100">{recipe.converted_recipe?.title || `Recipe ${recipe.recipe_id}`}</h2>
              <span className="text-xs text-neutral-500">{new Date(recipe.saved_at).toLocaleString()}</span>
            </div>
            <p className="mb-3 text-sm text-neutral-400">{recipe.notes || "No notes added."}</p>
            {recipe.published ? (
              <Link
                href={`/recipes/${user?.uid}/${recipe.id}`}
                className="text-sm font-medium text-lime-400 hover:text-lime-300"
              >
                Open published detail
              </Link>
            ) : (
              <p className="text-xs text-neutral-500">Not published. Publish from your save flow when available.</p>
            )}
          </li>
        ))}
      </ul>
    </PageShell>
  );
}
