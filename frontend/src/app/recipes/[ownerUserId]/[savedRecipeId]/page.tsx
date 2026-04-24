"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { ApiError } from "@/lib/api-client";
import { PublishedRecipeDetail, SavedRecipeResponse } from "@/lib/frontend-types";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { getErrorMessage, LoadingState, LoggedInUtilityHeader, PageShell } from "@/lib/route-helpers";

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
  const [ownRecipe, setOwnRecipe] = useState<SavedRecipeResponse | null>(null);
  const [mySaved, setMySaved] = useState<SavedRecipeResponse[]>([]);
  const [ownerNotes, setOwnerNotes] = useState("");
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [savingPublish, setSavingPublish] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isOwner = !!user && user.uid === ownerUserId;

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
        if (user) {
          const saves = await api.fetch<SavedRecipeResponse[]>("/api/users/me/saved-recipes");
          setMySaved(saves);
        }

        if (isOwner) {
          const mine = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${savedRecipeId}`);
          setOwnRecipe(mine);
          setOwnerNotes(mine.notes || "");
          setNotesDraft(mine.notes || "");
          setRecipe({
            owner_user_id: ownerUserId,
            saved_recipe_id: savedRecipeId,
            saved_at: mine.saved_at,
            converted_recipe: mine.converted_recipe,
            recipe_id: mine.recipe_id,
          });
        } else {
          const detail = await api.fetch<PublishedRecipeDetail>(`/api/published-recipes/${ownerUserId}/${savedRecipeId}`);
          setRecipe(detail);
          setOwnRecipe(null);
          setOwnerNotes("");
          setNotesDraft("");
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 404 && isOwner) {
          setError("Saved recipe not found for your account.");
        } else {
          setError(getErrorMessage(err));
        }
      } finally {
        setFetching(false);
      }
    };
    void load();
  }, [api, isOwner, ownerUserId, savedRecipeId, user]);

  const inMyCollection = useMemo(() => {
    if (!user) return false;
    if (isOwner) return true;
    return mySaved.some(
      (row) => row.copied_from_user_id === ownerUserId && row.copied_from_saved_recipe_id === savedRecipeId
    );
  }, [isOwner, mySaved, ownerUserId, savedRecipeId, user]);

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

  const handleSaveNotes = async () => {
    if (!isOwner) return;
    setSavingNotes(true);
    setError(null);
    setStatusMessage(null);
    try {
      const updated = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${savedRecipeId}`, {
        method: "PATCH",
        body: JSON.stringify({ notes: notesDraft }),
      });
      setOwnRecipe(updated);
      setOwnerNotes(updated.notes || "");
      setNotesDraft(updated.notes || "");
      setIsEditingNotes(false);
      setStatusMessage("Notes updated.");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingNotes(false);
    }
  };

  const handleTogglePublish = async () => {
    if (!isOwner || !ownRecipe) return;
    setSavingPublish(true);
    setError(null);
    setStatusMessage(null);
    try {
      const updated = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${savedRecipeId}`, {
        method: "PATCH",
        body: JSON.stringify({ published: !ownRecipe.published }),
      });
      setOwnRecipe(updated);
      setRecipe((prev) =>
        prev
          ? {
              ...prev,
              converted_recipe: updated.converted_recipe,
            }
          : prev
      );
      setStatusMessage(updated.published ? "Recipe is now published to the community." : "Recipe is now private.");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingPublish(false);
    }
  };

  return (
    <PageShell showLoggedInHeader={false}>
      <LoggedInUtilityHeader />
      {fetching ? <LoadingState label="Loading recipe..." /> : null}
      {error ? (
        <Card className="mb-4 bg-[#B84C2A]">
          <p className="text-sm font-black uppercase tracking-[0.06em] text-black">{error}</p>
        </Card>
      ) : null}

      {recipe ? (
        <Card>
          <CardTitle className="text-5xl">{recipe.converted_recipe?.title || "Recipe Detail"}</CardTitle>
          <p className="text-(--color-primary-text)/80 mb-2 mt-2 text-sm font-bold uppercase tracking-[0.04em]">
            {recipe.converted_recipe?.description?.trim() || "No description available for this recipe."}
          </p>
          <p className="text-(--color-primary-text)/70 mb-4 text-xs font-bold uppercase tracking-[0.04em]">
            Owner: {ownerUserId} {isOwner ? "(You)" : ""}
          </p>
          <div className="mb-4 grid gap-2 border-3 border-black bg-[#2B2B2B] p-3 text-sm text-[#F5F5F5] sm:grid-cols-2">
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Servings:</span>{" "}
              {recipe.converted_recipe?.servings ?? "Unknown"}
            </p>
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Published:</span>{" "}
              {isOwner ? (ownRecipe?.published ? "Yes" : "No") : "Yes"}
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

          {!user ? (
            <CardDescription className="mb-4 text-sm">
              Sign in to save this recipe to your collection.
            </CardDescription>
          ) : null}

          {user && !isOwner ? (
            <Button
              onClick={() => void handleSaveCopy()}
              disabled={saving || inMyCollection}
              className="mb-4 text-sm"
            >
              {inMyCollection ? "In My Collection" : saving ? "Saving..." : "Save To My Collection"}
            </Button>
          ) : null}

          {statusMessage ? (
            <p className="mb-4 text-sm font-black uppercase tracking-[0.05em] text-[#A83E1B]">{statusMessage}</p>
          ) : null}

          <h2 className="font-heading text-(--color-primary-text) mb-2 text-4xl uppercase tracking-[0.05em]">Ingredients</h2>
          {recipe.converted_recipe?.ingredients?.length ? (
            <div className="mb-4 overflow-hidden border-3 border-black">
              <div className="grid grid-cols-[100px_120px_1fr] bg-[#2B2B2B] px-3 py-2 text-xs font-black uppercase tracking-wide text-[#BDBDBD]">
                <span>Quantity</span>
                <span>Unit</span>
                <span>Ingredient</span>
              </div>
              <ul className="divide-y divide-black">
                {recipe.converted_recipe.ingredients.map((ingredient, idx) => (
                  <li key={`${ingredient.name}-${idx}`} className="text-(--color-primary-text) grid grid-cols-[100px_120px_1fr] bg-(--color-surface) px-3 py-2 text-sm font-semibold">
                    <span>{ingredient.quantity}</span>
                    <span>{ingredient.unit || "-"}</span>
                    <span>{ingredient.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-(--color-primary-text)/70 mb-4 text-sm font-bold uppercase tracking-[0.04em]">
              No ingredients listed for this recipe.
            </p>
          )}

          <h2 className="font-heading text-(--color-primary-text) mb-2 text-4xl uppercase tracking-[0.05em]">Instructions</h2>
          <ol className="text-(--color-primary-text) mb-4 list-decimal space-y-1 pl-6 text-sm font-semibold">
            {recipe.converted_recipe?.instructions?.map((step, idx) => (
              <li key={`step-${idx}`}>{step}</li>
            ))}
          </ol>

          {isOwner ? (
            <div className="border-3 border-black bg-[#2B2B2B] p-3">
              <div className="mb-3 flex items-center justify-between gap-2">
                <h3 className="text-sm font-black uppercase tracking-[0.05em] text-[#F5F5F5]">Publishing</h3>
                <Button
                  onClick={() => void handleTogglePublish()}
                  disabled={savingPublish}
                  variant="secondary"
                  className="px-3 py-1 text-xs"
                >
                  {savingPublish
                    ? "Saving..."
                    : ownRecipe?.published
                      ? "Unpublish Recipe"
                      : "Publish Recipe"}
                </Button>
              </div>
              <p className="mb-3 text-xs font-bold uppercase tracking-[0.04em] text-[#BDBDBD]">
                {ownRecipe?.published
                  ? "This recipe is visible in the public collection."
                  : "This recipe is private and only visible in your collection."}
              </p>
              <h3 className="mb-1 text-sm font-black uppercase tracking-[0.05em] text-[#F5F5F5]">Your Notes</h3>
              {!isEditingNotes ? (
                <>
                  <p className="mb-3 text-sm font-semibold text-[#DADADA]">{ownerNotes || "No notes for this saved recipe."}</p>
                  <Button
                    onClick={() => setIsEditingNotes(true)}
                    variant="secondary"
                    className="px-3 py-1 text-xs"
                  >
                    Edit Notes
                  </Button>
                </>
              ) : (
                <>
                  <textarea
                    value={notesDraft}
                    onChange={(e) => setNotesDraft(e.target.value)}
                    rows={4}
                    className="mb-3 w-full border-3 border-black bg-[#1F1F1F] px-3 py-2 text-sm font-semibold text-[#F5F5F5]"
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={() => void handleSaveNotes()}
                      disabled={savingNotes}
                      className="px-3 py-1 text-xs"
                    >
                      {savingNotes ? "Saving..." : "Save Notes"}
                    </Button>
                    <Button
                      onClick={() => {
                        setIsEditingNotes(false);
                        setNotesDraft(ownRecipe?.notes || ownerNotes || "");
                      }}
                      disabled={savingNotes}
                      variant="secondary"
                      className="px-3 py-1 text-xs"
                    >
                      Cancel
                    </Button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <p className="text-(--color-primary-text)/70 text-xs font-bold uppercase tracking-[0.04em]">
              Notes are only visible for your own saved recipes.
            </p>
          )}
        </Card>
      ) : null}
    </PageShell>
  );
}
