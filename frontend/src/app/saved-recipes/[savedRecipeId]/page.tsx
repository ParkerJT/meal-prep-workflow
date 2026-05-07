"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { SavedRecipeResponse } from "@/lib/frontend-types";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { getErrorMessage, LoadingState, LoggedInUtilityHeader, PageShell, useRequireAuth } from "@/lib/route-helpers";

export default function SavedRecipeDetailPage() {
  const params = useParams<{ savedRecipeId: string }>();
  const savedRecipeId = params.savedRecipeId;
  const { api } = useAuth();
  const { loading, isAuthenticated } = useRequireAuth();
  const [recipe, setRecipe] = useState<SavedRecipeResponse | null>(null);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notesDraft, setNotesDraft] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);

  useEffect(() => {
    if (loading || !isAuthenticated || !savedRecipeId) return;
    const load = async () => {
      setFetching(true);
      setError(null);
      try {
        const data = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${savedRecipeId}`);
        setRecipe(data);
        setNotesDraft(data.notes || "");
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setFetching(false);
      }
    };
    void load();
  }, [api, isAuthenticated, loading, savedRecipeId]);

  const handleSaveNotes = async () => {
    if (!recipe) return;
    setSavingNotes(true);
    setError(null);
    try {
      const updated = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${recipe.id}`, {
        method: "PATCH",
        body: JSON.stringify({ notes: notesDraft }),
      });
      setRecipe(updated);
      setNotesDraft(updated.notes || "");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingNotes(false);
    }
  };

  return (
    <PageShell showLoggedInHeader={false}>
      <LoggedInUtilityHeader />
      {loading || fetching ? <LoadingState label="Loading recipe..." /> : null}
      {error ? (
        <Card className="mb-4 bg-[#B84C2A]">
          <p className="text-sm font-black uppercase tracking-[0.06em] text-black">{error}</p>
        </Card>
      ) : null}

      {!fetching && !error && recipe ? (
        <Card>
          <CardTitle className="text-4xl">{recipe.converted_recipe?.title || `Recipe ${recipe.original_recipe_id}`}</CardTitle>
          <CardDescription className="mt-2 text-sm">
            Saved on {new Date(recipe.saved_at).toLocaleString()}
          </CardDescription>

          <p className="text-(--color-primary-text)/80 mb-3 mt-4 text-sm font-bold uppercase tracking-[0.04em]">
            {recipe.converted_recipe?.description?.trim() || "No description available for this recipe."}
          </p>

          <div className="mb-4 grid gap-2 border-3 border-black bg-[#2B2B2B] p-3 text-sm text-[#F5F5F5] sm:grid-cols-2">
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Servings:</span>{" "}
              {recipe.converted_recipe?.servings ?? "Unknown"}
            </p>
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Calories:</span>{" "}
              {recipe.converted_recipe?.nutritional_info?.calories ?? "Unknown"}
            </p>
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Protein:</span>{" "}
              {recipe.converted_recipe?.nutritional_info?.protein ?? "Unknown"}g
            </p>
          </div>

          <h2 className="font-heading text-(--color-primary-text) mb-2 text-4xl uppercase tracking-[0.05em]">Ingredients</h2>
          {recipe.converted_recipe?.ingredients?.length ? (
            <ul className="mb-4 list-disc space-y-1 pl-6 text-sm font-semibold text-(--color-primary-text)">
              {recipe.converted_recipe.ingredients.map((ingredient, idx) => (
                <li key={`${ingredient.name}-${idx}`}>
                  {ingredient.quantity} {ingredient.unit || ""} {ingredient.name}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-(--color-primary-text)/70 mb-4 text-sm font-bold uppercase tracking-[0.04em]">
              No ingredients listed for this recipe.
            </p>
          )}

          <h2 className="font-heading text-(--color-primary-text) mb-2 text-4xl uppercase tracking-[0.05em]">Instructions</h2>
          {recipe.converted_recipe?.instructions?.length ? (
            <ol className="text-(--color-primary-text) mb-4 list-decimal space-y-1 pl-6 text-sm font-semibold">
              {recipe.converted_recipe.instructions.map((step, idx) => (
                <li key={`step-${idx}`}>{step}</li>
              ))}
            </ol>
          ) : (
            <p className="text-(--color-primary-text)/70 mb-4 text-sm font-bold uppercase tracking-[0.04em]">
              No instructions listed for this recipe.
            </p>
          )}

          <label className="text-(--color-primary-text) mb-2 block text-sm font-bold uppercase tracking-[0.05em]">
            Notes
            <textarea
              value={notesDraft}
              onChange={(e) => setNotesDraft(e.target.value)}
              rows={4}
              className="mt-1 w-full border-3 border-black bg-[#2B2B2B] px-3 py-2 text-sm font-semibold text-[#F5F5F5] outline-none focus:border-(--color-accent)"
              placeholder="Add your notes..."
            />
          </label>
          <Button onClick={() => void handleSaveNotes()} disabled={savingNotes} className="text-sm">
            {savingNotes ? "Saving..." : "Save Notes"}
          </Button>
        </Card>
      ) : null}
    </PageShell>
  );
}
