"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { ApiError } from "@/lib/api-client";
import { PublishedRecipeDetail, SavedRecipeResponse } from "@/lib/frontend-types";
import { AppNav, getErrorMessage, LoadingState, PageShell } from "@/lib/route-helpers";

interface RecipeDetailPageProps {
  params: Promise<{
    ownerUserId: string;
    savedRecipeId: string;
  }>;
}

export default function RecipeDetailPage({ params }: RecipeDetailPageProps) {
  const { api, user } = useAuth();
  const [ownerUserId, setOwnerUserId] = useState("");
  const [savedRecipeId, setSavedRecipeId] = useState("");
  const [recipe, setRecipe] = useState<PublishedRecipeDetail | null>(null);
  const [mySaved, setMySaved] = useState<SavedRecipeResponse[]>([]);
  const [ownerNotes, setOwnerNotes] = useState<string | null>(null);
  const [fetching, setFetching] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const resolveParams = async () => {
      const resolved = await params;
      setOwnerUserId(resolved.ownerUserId);
      setSavedRecipeId(resolved.savedRecipeId);
    };
    void resolveParams();
  }, [params]);

  useEffect(() => {
    if (!ownerUserId || !savedRecipeId) return;

    const load = async () => {
      setFetching(true);
      setError(null);
      try {
        const detail = await api.fetch<PublishedRecipeDetail>(`/api/published-recipes/${ownerUserId}/${savedRecipeId}`);
        setRecipe(detail);

        if (user) {
          const saves = await api.fetch<SavedRecipeResponse[]>("/api/users/me/saved-recipes");
          setMySaved(saves);

          if (user.uid === ownerUserId) {
            try {
              const ownRecipe = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${savedRecipeId}`);
              setOwnerNotes(ownRecipe.notes || "");
            } catch {
              setOwnerNotes("");
            }
          }
        }
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setFetching(false);
      }
    };
    void load();
  }, [api, ownerUserId, savedRecipeId, user]);

  const inMyCollection = useMemo(() => {
    if (!user) return false;
    if (user.uid === ownerUserId) return true;
    return mySaved.some(
      (row) => row.copied_from_user_id === ownerUserId && row.copied_from_saved_recipe_id === savedRecipeId
    );
  }, [mySaved, ownerUserId, savedRecipeId, user]);

  const handleSaveCopy = async () => {
    setSaving(true);
    setStatusMessage(null);
    setError(null);
    try {
      await api.fetch("/api/users/me/saved-recipes", {
        method: "POST",
        body: JSON.stringify({
          source_owner_user_id: ownerUserId,
          source_saved_recipe_id: savedRecipeId,
          notes: "",
        }),
      });
      setStatusMessage("Saved to your collection.");
      const saves = await api.fetch<SavedRecipeResponse[]>("/api/users/me/saved-recipes");
      setMySaved(saves);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setStatusMessage("Already in your collection.");
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageShell>
      <AppNav />
      {fetching ? <LoadingState label="Loading published recipe..." /> : null}
      {error ? <p className="mb-4 rounded border border-red-700 bg-red-950 p-3 text-red-300">{error}</p> : null}

      {recipe ? (
        <section className="rounded border border-neutral-800 bg-neutral-900 p-5">
          <h1 className="mb-1 text-2xl font-bold">{recipe.converted_recipe?.title || "Published recipe"}</h1>
          <p className="mb-4 text-xs text-neutral-500">Owner: {ownerUserId}</p>

          {!user ? <p className="mb-4 text-sm text-neutral-400">Sign in to save this recipe to your collection.</p> : null}

          {user ? (
            <button
              onClick={() => void handleSaveCopy()}
              disabled={saving || inMyCollection}
              className="mb-4 rounded bg-lime-500 px-4 py-2 text-sm font-semibold text-black hover:bg-lime-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {inMyCollection ? "In my collection" : saving ? "Saving..." : "Save to my collection"}
            </button>
          ) : null}

          {statusMessage ? <p className="mb-4 text-sm text-lime-300">{statusMessage}</p> : null}

          <h2 className="mb-2 text-lg font-semibold">Ingredients</h2>
          <ul className="mb-4 list-disc space-y-1 pl-6 text-sm text-neutral-300">
            {recipe.converted_recipe?.ingredients?.map((ingredient, idx) => (
              <li key={`${ingredient.name}-${idx}`}>
                {ingredient.quantity} {ingredient.unit || ""} {ingredient.name}
              </li>
            ))}
          </ul>

          <h2 className="mb-2 text-lg font-semibold">Instructions</h2>
          <ol className="mb-4 list-decimal space-y-1 pl-6 text-sm text-neutral-300">
            {recipe.converted_recipe?.instructions?.map((step, idx) => (
              <li key={`step-${idx}`}>{step}</li>
            ))}
          </ol>

          {user?.uid === ownerUserId ? (
            <div className="rounded border border-neutral-700 bg-neutral-950 p-3">
              <h3 className="mb-1 text-sm font-semibold text-neutral-200">Your notes</h3>
              <p className="text-sm text-neutral-400">{ownerNotes || "No notes for this saved recipe."}</p>
            </div>
          ) : (
            <p className="text-xs text-neutral-500">Notes are only visible for your own saved recipes.</p>
          )}
        </section>
      ) : null}
    </PageShell>
  );
}
