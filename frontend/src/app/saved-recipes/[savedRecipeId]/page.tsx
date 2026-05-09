"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { SavedRecipeResponse } from "@/lib/frontend-types";
import { Card } from "@/components/ui/card";
import { getErrorMessage, LoggedInUtilityHeader, PageShell, useRequireAuth } from "@/lib/route-helpers";

type NotesStatus = "idle" | "saving" | "saved" | "error";

export default function SavedRecipeDetailPage() {
  const params = useParams<{ savedRecipeId: string }>();
  const savedRecipeId = params.savedRecipeId;
  const { api } = useAuth();
  const { loading, isAuthenticated } = useRequireAuth();
  const [recipe, setRecipe] = useState<SavedRecipeResponse | null>(null);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notesDraft, setNotesDraft] = useState("");
  const [savedNotes, setSavedNotes] = useState("");
  const [notesStatus, setNotesStatus] = useState<NotesStatus>("idle");

  useEffect(() => {
    if (loading || !isAuthenticated || !savedRecipeId) return;
    const load = async () => {
      setFetching(true);
      setError(null);
      try {
        const data = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${savedRecipeId}`);
        setRecipe(data);
        const initialNotes = data.notes || "";
        setNotesDraft(initialNotes);
        setSavedNotes(initialNotes);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setFetching(false);
      }
    };
    void load();
  }, [api, isAuthenticated, loading, savedRecipeId]);

  // Auto-clear the "Saved" badge after a short delay so it doesn't linger.
  useEffect(() => {
    if (notesStatus !== "saved") return;
    const t = setTimeout(() => setNotesStatus("idle"), 2000);
    return () => clearTimeout(t);
  }, [notesStatus]);

  const handleNotesBlur = async () => {
    if (!recipe) return;
    if (notesDraft === savedNotes) return;
    setNotesStatus("saving");
    try {
      const updated = await api.fetch<SavedRecipeResponse>(`/api/users/me/saved-recipes/${recipe.id}`, {
        method: "PATCH",
        body: JSON.stringify({ notes: notesDraft }),
      });
      setRecipe(updated);
      const next = updated.notes || "";
      setNotesDraft(next);
      setSavedNotes(next);
      setNotesStatus("saved");
    } catch (err) {
      setError(getErrorMessage(err));
      setNotesStatus("error");
    }
  };

  const recipeData = recipe?.converted_recipe ?? null;
  const title = recipeData?.title || (recipe ? `Recipe ${recipe.original_recipe_id}` : "");
  const savedDate = recipe ? new Date(recipe.saved_at) : null;

  return (
    <PageShell showLoggedInHeader={false} maxWidth="6xl">
      <LoggedInUtilityHeader />

      {error ? (
        <Card role="alert" aria-live="polite" className="mb-4 bg-[#B84C2A]">
          <p className="text-sm font-black uppercase tracking-[0.06em] text-black">{error}</p>
        </Card>
      ) : null}

      {loading || fetching ? <RecipeSkeleton /> : null}

      {!fetching && !error && recipe ? (
        <article>
          <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div className="min-w-0">
              <h1 className="text-3xl md:text-4xl">{title}</h1>
              {savedDate ? (
                <p className="mt-1 text-xs font-bold uppercase tracking-[0.04em] text-(--color-primary-text)/70">
                  Saved{" "}
                  {savedDate.toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                  {" \u00b7 "}
                  {savedDate.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}
                </p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2 text-xs font-black uppercase tracking-[0.04em]">
              <MetaPill label="Serves" value={recipeData?.servings ?? "?"} />
              <MetaPill label="Cal" value={recipeData?.nutritional_info?.calories ?? "?"} />
              <MetaPill label="Protein" value={`${recipeData?.nutritional_info?.protein ?? "?"}g`} />
            </div>
          </header>

          {recipeData?.description?.trim() ? (
            <p className="mb-6 max-w-3xl text-base font-semibold leading-relaxed text-(--color-primary-text)/85">
              {recipeData.description.trim()}
            </p>
          ) : null}

          <div className="grid gap-5 md:grid-cols-3">
            <aside className="md:col-span-1 print:col-span-3">
              <div className="md:sticky md:top-20">
                <Card className="p-4">
                  <h2 className="mb-3 text-2xl tracking-[0.06em]">Ingredients</h2>
                  {recipeData?.ingredients?.length ? (
                    <ul className="list-disc space-y-2 pl-5 text-base leading-relaxed">
                      {recipeData.ingredients.map((ingredient, idx) => (
                        <li key={`${ingredient.name}-${idx}`}>
                          <span className="font-black">
                            {ingredient.quantity}
                            {ingredient.unit ? ` ${ingredient.unit}` : ""}
                          </span>{" "}
                          <span className="font-semibold">{ingredient.name}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-(--color-primary-text)/70">
                      No ingredients listed for this recipe.
                    </p>
                  )}
                </Card>
              </div>
            </aside>

            <section className="md:col-span-2 print:col-span-3">
              <Card className="p-4 md:p-5">
                <h2 className="mb-3 text-2xl tracking-[0.06em]">Instructions</h2>
                {recipeData?.instructions?.length ? (
                  <ol className="list-decimal space-y-3 pl-6 text-base leading-relaxed marker:font-black marker:text-(--color-primary-text)">
                    {recipeData.instructions.map((step, idx) => (
                      <li key={`step-${idx}`} className="pl-1">
                        {step}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="text-sm text-(--color-primary-text)/70">
                    No instructions listed for this recipe.
                  </p>
                )}
              </Card>
            </section>
          </div>

          <Card className="mt-5 p-4 print:hidden">
            <div className="mb-2 flex items-baseline justify-between gap-3">
              <label htmlFor="recipe-notes" className="text-sm font-black uppercase tracking-[0.06em]">
                Notes
              </label>
              <span
                aria-live="polite"
                className="text-xs font-bold uppercase tracking-[0.04em] text-(--color-primary-text)/70"
              >
                <NotesStatusText status={notesStatus} dirty={notesDraft !== savedNotes} />
              </span>
            </div>
            <textarea
              id="recipe-notes"
              value={notesDraft}
              onChange={(e) => setNotesDraft(e.target.value)}
              onBlur={() => void handleNotesBlur()}
              rows={4}
              className="w-full border-3 border-black bg-[#2B2B2B] px-3 py-2 text-base font-medium text-[#F5F5F5] outline-none focus:border-(--color-accent)"
              placeholder="Add your notes... (autosaves when you click outside)"
            />
          </Card>
        </article>
      ) : null}
    </PageShell>
  );
}

function MetaPill({ label, value }: { label: string; value: string | number }) {
  return (
    <span className="inline-flex items-baseline gap-1 border-3 border-black bg-[#2B2B2B] px-3 py-1 text-[#F5F5F5]">
      <span className="text-[#BDBDBD]">{label}</span>
      <span>{value}</span>
    </span>
  );
}

function NotesStatusText({ status, dirty }: { status: NotesStatus; dirty: boolean }) {
  if (status === "saving") return <>Saving...</>;
  if (status === "saved") return <>Saved</>;
  if (status === "error") return <span className="text-[#B84C2A]">Save failed</span>;
  if (dirty) return <span className="text-(--color-primary-text)/60">Unsaved</span>;
  return null;
}

function RecipeSkeleton() {
  const bar = "block animate-pulse rounded-none bg-(--color-surface)";
  return (
    <div aria-busy="true" aria-label="Loading recipe">
      <div className={`${bar} mb-3 h-9 w-2/3`} />
      <div className={`${bar} mb-6 h-4 w-1/3`} />
      <div className="grid gap-5 md:grid-cols-3">
        <Card className="p-4">
          <div className={`${bar} mb-4 h-5 w-32`} />
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className={`${bar} h-4 w-full`} />
            ))}
          </div>
        </Card>
        <div className="md:col-span-2">
          <Card className="p-4">
            <div className={`${bar} mb-4 h-5 w-40`} />
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <div className={`${bar} h-4 w-full`} />
                  <div className={`${bar} h-4 w-11/12`} />
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
