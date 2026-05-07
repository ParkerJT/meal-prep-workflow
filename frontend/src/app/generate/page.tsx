"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { ApiError } from "@/lib/api-client";
import { ConvertedRecipe, SubscriptionStatusResponse } from "@/lib/frontend-types";
import { getErrorMessage, LoadingState, LoggedInUtilityHeader, PageShell, useRequireAuth } from "@/lib/route-helpers";
import { TrialStatusBanner } from "@/lib/TrialStatusBanner";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface WorkflowRequest {
  recipe_url: string;
  user_adjustments: {
    target_servings: number;
    target_calories: number;
    target_protein: number;
  };
}

export default function GeneratePage() {
  const { api } = useAuth();
  const { loading, isAuthenticated } = useRequireAuth();
  const [recipeUrl, setRecipeUrl] = useState("");
  const [servings, setServings] = useState(4);
  const [calories, setCalories] = useState(500);
  const [protein, setProtein] = useState(30);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subscriptionRequired, setSubscriptionRequired] = useState(false);
  const [subscription, setSubscription] = useState<SubscriptionStatusResponse | null>(null);
  const [loadingSubscription, setLoadingSubscription] = useState(true);
  const [selectingPlan, setSelectingPlan] = useState<"monthly" | "annual" | null>(null);
  const [result, setResult] = useState<ConvertedRecipe | null>(null);
  const [saveNotes, setSaveNotes] = useState("");
  const [savingResult, setSavingResult] = useState(false);
  const [savedResultId, setSavedResultId] = useState<string | null>(null);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    const loadSubscription = async () => {
      setLoadingSubscription(true);
      try {
        await api.fetch<SubscriptionStatusResponse>("/api/subscription/start-trial", { method: "POST" });
        const data = await api.fetch<SubscriptionStatusResponse>("/api/subscription/me");
        setSubscription(data);
      } catch {
        setSubscription(null);
      } finally {
        setLoadingSubscription(false);
      }
    };
    void loadSubscription();
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
        recipe_url: recipeUrl.trim(),
        user_adjustments: {
          target_servings: servings,
          target_calories: calories,
          target_protein: protein,
        },
      };
      const data = await api.fetch<ConvertedRecipe>("/api/workflow/generate", {
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
          source_url: recipeUrl.trim(),
          notes: saveNotes,
          converted_recipe: result,
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
          Paste a recipe URL and generate a macro-adjusted version.
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
          <Input
            value={recipeUrl}
            onChange={(e) => setRecipeUrl(e.target.value)}
            required
            placeholder="https://example.com/recipe or YouTube URL"
            className="text-sm normal-case tracking-normal"
          />
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
          <CardTitle className="text-4xl">{result.title}</CardTitle>
          <p className="text-(--color-primary-text)/80 mb-3 mt-2 text-sm font-bold uppercase tracking-[0.04em]">
            {result.description?.trim() || "No description available for this recipe."}
          </p>
          <div className="mb-4 grid gap-2 border-3 border-black bg-[#2B2B2B] p-3 text-sm text-[#F5F5F5] sm:grid-cols-2">
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Servings:</span>{" "}
              {result.servings ?? "Unknown"}
            </p>
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Calories:</span>{" "}
              {result.nutritional_info?.calories ?? "Unknown"}
            </p>
            <p>
              <span className="font-black uppercase tracking-[0.04em] text-[#BDBDBD]">Protein:</span>{" "}
              {result.nutritional_info?.protein ?? "Unknown"}g
            </p>
          </div>

          <h2 className="font-heading text-(--color-primary-text) mb-2 text-4xl uppercase tracking-[0.05em]">Ingredients</h2>
          {result.ingredients?.length ? (
            <div className="mb-4 overflow-hidden border-3 border-black">
              <div className="grid grid-cols-[100px_120px_1fr] bg-[#2B2B2B] px-3 py-2 text-xs font-black uppercase tracking-wide text-[#BDBDBD]">
                <span>Quantity</span>
                <span>Unit</span>
                <span>Ingredient</span>
              </div>
              <ul className="divide-y divide-black">
                {result.ingredients.map((ingredient, idx) => (
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
          {result.instructions?.length ? (
            <ol className="text-(--color-primary-text) mb-4 list-decimal space-y-1 pl-6 text-sm font-semibold">
              {result.instructions.map((step, idx) => (
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
