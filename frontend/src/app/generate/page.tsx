"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { ApiError } from "@/lib/api-client";
import {
  GenerateResponse,
  GenerationPreferencesResponse,
  SubscriptionStatusResponse,
} from "@/lib/frontend-types";
import { getErrorMessage, LoadingState, LoggedInUtilityHeader, PageShell, useRequireAuth } from "@/lib/route-helpers";
import { TrialStatusBanner } from "@/lib/TrialStatusBanner";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

// Keep in sync with backend/app/services/user_text.py
const RECIPE_TEXT_MAX_CHARS = 50_000;
const PERSONAL_INSTRUCTIONS_MAX_CHARS = 500;

interface WorkflowRequest {
  input_mode: "url" | "text";
  recipe_url?: string;
  recipe_text?: string;
  personal_instructions?: string;
  user_adjustments: {
    target_servings: number;
    target_calories: number;
    target_protein: number;
  };
}

function CharacterCounter({ current, max }: { current: number; max: number }) {
  return (
    <span className="text-(--color-primary-text)/70 mt-1 block text-xs font-semibold normal-case tracking-normal">
      {current.toLocaleString()} / {max.toLocaleString()} characters
    </span>
  );
}

type RecipeSourceMode = "url" | "text";

export default function GeneratePage() {
  const { api } = useAuth();
  const { loading, isAuthenticated } = useRequireAuth();
  const [inputMode, setInputMode] = useState<RecipeSourceMode>("url");
  const [recipeUrl, setRecipeUrl] = useState("");
  const [recipeText, setRecipeText] = useState("");
  const [generationInstructions, setGenerationInstructions] = useState("");
  const [servings, setServings] = useState(4);
  const [calories, setCalories] = useState(500);
  const [protein, setProtein] = useState(30);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subscriptionRequired, setSubscriptionRequired] = useState(false);
  const [subscription, setSubscription] = useState<SubscriptionStatusResponse | null>(null);
  const [loadingSubscription, setLoadingSubscription] = useState(true);
  const [selectingPlan, setSelectingPlan] = useState<"monthly" | "annual" | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [saveNotes, setSaveNotes] = useState("");
  const [savingResult, setSavingResult] = useState(false);
  const [savedResultId, setSavedResultId] = useState<string | null>(null);
  const [hasGlobalInstructions, setHasGlobalInstructions] = useState(false);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    const loadPageData = async () => {
      setLoadingSubscription(true);
      try {
        await api.fetch<SubscriptionStatusResponse>("/api/subscription/start-trial", { method: "POST" });
        const [subData, prefsData] = await Promise.all([
          api.fetch<SubscriptionStatusResponse>("/api/subscription/me"),
          api.fetch<GenerationPreferencesResponse>("/api/users/me/generation-preferences"),
        ]);
        setSubscription(subData);
        setHasGlobalInstructions(!!prefsData.global_instructions.trim());
      } catch {
        setSubscription(null);
        setHasGlobalInstructions(false);
      } finally {
        setLoadingSubscription(false);
      }
    };
    void loadPageData();
  }, [api, isAuthenticated, loading]);

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSubscriptionRequired(false);
    setResult(null);
    setSavedResultId(null);
    try {
      const payload: WorkflowRequest = {
        input_mode: inputMode === "text" ? "text" : "url",
        user_adjustments: {
          target_servings: servings,
          target_calories: calories,
          target_protein: protein,
        },
      };
      if (inputMode === "text") {
        payload.recipe_text = recipeText.trim();
      } else {
        payload.recipe_url = recipeUrl.trim();
      }
      const trimmedInstructions = generationInstructions.trim();
      if (trimmedInstructions) {
        payload.personal_instructions = trimmedInstructions;
      }
      const data = await api.fetch<GenerateResponse>("/api/workflow/generate", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setResult(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setSubscriptionRequired(true);
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const saveGeneratedRecipe = async () => {
    if (!result) return;
    setSavingResult(true);
    setError(null);
    try {
      const data = await api.fetch<{ id: string }>("/api/users/me/saved-recipes/from-generate", {
        method: "POST",
        body: JSON.stringify({
          source_url: result.source_url,
          source_type: result.source_type,
          original_recipe: result.original_recipe,
          notes: saveNotes,
          converted_recipe: result.converted_recipe,
        }),
      });
      setSavedResultId(data.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingResult(false);
    }
  };

  const choosePlan = async (plan: "monthly" | "annual") => {
    setSelectingPlan(plan);
    setError(null);
    try {
      const data = await api.fetch<{ url: string }>("/api/subscription/checkout", {
        method: "POST",
        body: JSON.stringify({ plan }),
      });
      window.location.href = data.url;
    } catch (err) {
      setError(getErrorMessage(err));
      setSelectingPlan(null);
    }
  };

  return (
    <PageShell showLoggedInHeader={false}>
      <LoggedInUtilityHeader />
      <Card className="mb-6">
        <CardTitle className="text-5xl">Generate Recipe</CardTitle>
        <CardDescription className="mt-3 text-base">
          Choose a recipe source, set your targets, and generate a macro-adjusted version. URL and pasted text are supported.
        </CardDescription>
      </Card>

      {loading && !isAuthenticated ? <LoadingState /> : null}
      {!loadingSubscription ? (
        <TrialStatusBanner subscription={subscription} selectingPlan={selectingPlan} onChoosePlan={choosePlan} />
      ) : null}
      {error ? (
        <Card className="mb-4 bg-[#B84C2A]">
          <p className="text-sm font-black uppercase tracking-[0.06em] text-black">{error}</p>
        </Card>
      ) : null}

      <Card className="mb-6">
        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <p className="text-(--color-primary-text) mb-2 text-sm font-bold uppercase tracking-[0.05em]">
              Recipe source
            </p>
            <div
              className="flex flex-wrap gap-2"
              role="group"
              aria-label="Recipe source type"
            >
              <Button
                type="button"
                variant={inputMode === "url" ? "primary" : "secondary"}
                className="text-xs sm:text-sm"
                aria-pressed={inputMode === "url"}
                onClick={() => setInputMode("url")}
              >
                Recipe URL
              </Button>
              <Button
                type="button"
                variant={inputMode === "text" ? "primary" : "secondary"}
                className="text-xs sm:text-sm"
                aria-pressed={inputMode === "text"}
                onClick={() => setInputMode("text")}
              >
                Pasted text
              </Button>
            </div>
            {hasGlobalInstructions ? (
              <p className="text-(--color-primary-text)/75 mt-2 text-xs font-semibold normal-case tracking-normal">
                Your account preferences will apply to this generation.{" "}
                <Link href="/settings" className="font-black text-(--color-primary-text) underline decoration-2 underline-offset-2 hover:text-[#ff6d40]">
                  Edit in Settings
                </Link>
              </p>
            ) : null}
          </div>

          {inputMode === "url" ? (
            <label className="text-(--color-primary-text) block text-sm font-bold uppercase tracking-[0.05em]">
              Link
              <Input
                value={recipeUrl}
                onChange={(e) => setRecipeUrl(e.target.value)}
                required
                placeholder="https://example.com/recipe or YouTube URL"
                className="mt-1 text-sm normal-case tracking-normal"
              />
            </label>
          ) : null}

          {inputMode === "text" ? (
            <label className="text-(--color-primary-text) block text-sm font-bold uppercase tracking-[0.05em]">
              Recipe text
              <textarea
                value={recipeText}
                onChange={(e) => setRecipeText(e.target.value)}
                rows={8}
                required
                maxLength={RECIPE_TEXT_MAX_CHARS}
                placeholder="Paste the full recipe (ingredients and steps)."
                className="mt-1 w-full border-3 border-black bg-[#2B2B2B] px-3 py-2 text-sm font-semibold normal-case tracking-normal text-[#F5F5F5] outline-none placeholder:text-[#F5F5F5]/40 focus:border-(--color-accent)"
              />
              <CharacterCounter current={recipeText.length} max={RECIPE_TEXT_MAX_CHARS} />
            </label>
          ) : null}

          <label className="text-(--color-primary-text) block text-sm font-bold uppercase tracking-[0.05em]">
            Instructions for this generation{" "}
            <span className="font-semibold normal-case text-[#BDBDBD]">(optional)</span>
            <textarea
              value={generationInstructions}
              onChange={(e) => setGenerationInstructions(e.target.value)}
              rows={3}
              maxLength={PERSONAL_INSTRUCTIONS_MAX_CHARS}
              placeholder='e.g. "Use Greek yogurt instead of sour cream" or "make this vegan"'
              className="mt-1 w-full border-3 border-black bg-[#2B2B2B] px-3 py-2 text-sm font-semibold normal-case tracking-normal text-[#F5F5F5] outline-none placeholder:text-[#F5F5F5]/40 focus:border-(--color-accent)"
            />
            <CharacterCounter current={generationInstructions.length} max={PERSONAL_INSTRUCTIONS_MAX_CHARS} />
          </label>

        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-(--color-primary-text) text-sm font-bold uppercase tracking-[0.05em]">
            Servings
            <Input
              type="number"
              min={1}
              value={servings}
              onChange={(e) => setServings(Number(e.target.value))}
              className="mt-1 px-2 py-1"
            />
          </label>
          <label className="text-(--color-primary-text) text-sm font-bold uppercase tracking-[0.05em]">
            Calories
            <Input
              type="number"
              min={1}
              value={calories}
              onChange={(e) => setCalories(Number(e.target.value))}
              className="mt-1 px-2 py-1"
            />
          </label>
          <label className="text-(--color-primary-text) text-sm font-bold uppercase tracking-[0.05em]">
            Protein (g)
            <Input
              type="number"
              min={1}
              value={protein}
              onChange={(e) => setProtein(Number(e.target.value))}
              className="mt-1 px-2 py-1"
            />
          </label>
        </div>
        <Button
          type="submit"
          disabled={submitting}
          className="text-sm"
        >
          {submitting ? "Generating..." : "Generate"}
        </Button>
      </form>
      </Card>

      {subscriptionRequired ? (
        <Card className="mb-6 bg-[#D47A4A]">
          <p className="text-(--color-primary-text) mb-3 text-sm font-black uppercase tracking-[0.06em]">
            Recipe generation is a premium feature. Choose a plan to continue.
          </p>
          <div className="flex gap-3">
            <Button
              onClick={() => void choosePlan("monthly")}
              className="text-sm"
            >
              Choose Monthly Plan
            </Button>
            <Button
              onClick={() => void choosePlan("annual")}
              variant="secondary"
              className="text-sm"
            >
              Choose Annual Plan
            </Button>
          </div>
        </Card>
      ) : null}

      {result ? (
        <Card>
          <CardTitle className="text-4xl">{result.converted_recipe.title}</CardTitle>
          <p className="text-(--color-primary-text)/80 mb-3 mt-2 text-sm font-bold uppercase tracking-[0.04em]">
            {result.converted_recipe.description?.trim() || "No description available for this recipe."}
          </p>
          <div className="mb-4 grid gap-2 border-3 border-black bg-[#2B2B2B] p-3 text-sm text-[#F5F5F5] sm:grid-cols-2">
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Servings:</span>{" "}
              {result.converted_recipe.servings ?? "Unknown"}
            </p>
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Calories:</span>{" "}
              {result.converted_recipe.nutritional_info?.calories ?? "Unknown"}
            </p>
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Protein:</span>{" "}
              {result.converted_recipe.nutritional_info?.protein ?? "Unknown"}g
            </p>
          </div>

          <h2 className="font-heading text-(--color-primary-text) mb-2 text-4xl uppercase tracking-[0.05em]">Ingredients</h2>
          {result.converted_recipe.ingredients?.length ? (
            <div className="mb-4 overflow-hidden border-3 border-black">
              <div className="grid grid-cols-[100px_120px_1fr] bg-[#2B2B2B] px-3 py-2 text-xs font-black uppercase tracking-wide text-[#BDBDBD]">
                <span>Quantity</span>
                <span>Unit</span>
                <span>Ingredient</span>
              </div>
              <ul className="divide-y divide-black">
                {result.converted_recipe.ingredients.map((ingredient, idx) => (
                  <li
                    key={`${ingredient.name}-${idx}`}
                    className="text-(--color-primary-text) grid grid-cols-[100px_120px_1fr] bg-(--color-surface) px-3 py-2 text-sm font-semibold"
                  >
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
          {result.converted_recipe.instructions?.length ? (
            <ol className="text-(--color-primary-text) mb-4 list-decimal space-y-1 pl-6 text-sm font-semibold">
              {result.converted_recipe.instructions.map((step, idx) => (
                <li key={`step-${idx}`}>{step}</li>
              ))}
            </ol>
          ) : (
            <p className="text-(--color-primary-text)/70 mb-4 text-sm font-bold uppercase tracking-[0.04em]">
              No instructions listed for this recipe.
            </p>
          )}

          <label className="text-(--color-primary-text) mb-2 block text-sm font-bold uppercase tracking-[0.05em]">
            Optional notes
            <textarea
              value={saveNotes}
              onChange={(e) => setSaveNotes(e.target.value)}
              rows={3}
              className="mt-1 w-full border-3 border-black bg-[#2B2B2B] px-3 py-2 text-sm font-semibold text-[#F5F5F5] outline-none focus:border-(--color-accent)"
              placeholder="Add notes before saving..."
            />
          </label>
          <Button
            onClick={() => void saveGeneratedRecipe()}
            disabled={savingResult || !!savedResultId}
            className="text-sm"
          >
            {savedResultId ? "Saved To Collection" : savingResult ? "Saving..." : "Save To My Collection"}
          </Button>
        </Card>
      ) : null}
    </PageShell>
  );
}
