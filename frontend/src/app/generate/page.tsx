"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { ApiError } from "@/lib/api-client";
import { ConvertedRecipe } from "@/lib/frontend-types";
import { AppNav, getErrorMessage, LoadingState, PageShell, useRequireAuth } from "@/lib/route-helpers";

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
  const [result, setResult] = useState<ConvertedRecipe | null>(null);

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSubscriptionRequired(false);
    setResult(null);
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

  const startTrial = async (plan: "monthly" | "annual") => {
    setError(null);
    try {
      const data = await api.fetch<{ url: string }>("/api/subscription/checkout", {
        method: "POST",
        body: JSON.stringify({ plan }),
      });
      window.location.href = data.url;
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <PageShell>
      <AppNav />
      <h1 className="mb-2 text-3xl font-bold">Generate Recipe</h1>
      <p className="mb-6 text-neutral-400">Paste a recipe URL and generate a macro-adjusted version.</p>

      {loading && !isAuthenticated ? <LoadingState /> : null}
      {error ? <p className="mb-4 rounded border border-red-700 bg-red-950 p-3 text-red-300">{error}</p> : null}

      <form onSubmit={handleGenerate} className="mb-6 space-y-4 rounded border border-neutral-800 bg-neutral-900 p-4">
        <input
          value={recipeUrl}
          onChange={(e) => setRecipeUrl(e.target.value)}
          required
          placeholder="https://example.com/recipe or YouTube URL"
          className="w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm"
        />
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-sm">
            Servings
            <input
              type="number"
              min={1}
              value={servings}
              onChange={(e) => setServings(Number(e.target.value))}
              className="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-2 py-1"
            />
          </label>
          <label className="text-sm">
            Calories
            <input
              type="number"
              min={1}
              value={calories}
              onChange={(e) => setCalories(Number(e.target.value))}
              className="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-2 py-1"
            />
          </label>
          <label className="text-sm">
            Protein (g)
            <input
              type="number"
              min={1}
              value={protein}
              onChange={(e) => setProtein(Number(e.target.value))}
              className="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-2 py-1"
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-lime-500 px-4 py-2 text-sm font-semibold text-black hover:bg-lime-400 disabled:opacity-50"
        >
          {submitting ? "Generating..." : "Generate"}
        </button>
      </form>

      {subscriptionRequired ? (
        <div className="mb-6 rounded border border-amber-700 bg-amber-950 p-4">
          <p className="mb-3 text-amber-200">A trial or active subscription is required to use recipe generation.</p>
          <div className="flex gap-3">
            <button
              onClick={() => void startTrial("monthly")}
              className="rounded bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400"
            >
              Start 14-day trial (monthly)
            </button>
            <button
              onClick={() => void startTrial("annual")}
              className="rounded border border-amber-500 px-4 py-2 text-sm font-semibold text-amber-300 hover:bg-amber-900"
            >
              Start 14-day trial (annual)
            </button>
          </div>
        </div>
      ) : null}

      {result ? (
        <section className="rounded border border-neutral-800 bg-neutral-900 p-5">
          <h2 className="mb-1 text-xl font-semibold">{result.title}</h2>
          <p className="mb-3 text-sm text-neutral-400">{result.description || "No description"}</p>
          <p className="mb-3 text-sm text-neutral-300">
            {result.servings} servings | {result.nutritional_info.calories} cal | {result.nutritional_info.protein}g protein
          </p>
          <p className="text-xs text-neutral-500">
            Save-to-collection from generate flow will be wired in the next UX phase endpoint integration.
          </p>
        </section>
      ) : null}
    </PageShell>
  );
}
