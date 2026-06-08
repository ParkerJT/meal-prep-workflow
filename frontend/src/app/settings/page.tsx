"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { GenerationPreferencesResponse, SubscriptionStatusResponse } from "@/lib/frontend-types";
import { TrialStatusBanner } from "@/lib/TrialStatusBanner";
import { getErrorMessage, LoadingState, LoggedInUtilityHeader, PageShell, useRequireAuth } from "@/lib/route-helpers";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";

// Keep in sync with backend/app/services/user_text.py
const GLOBAL_INSTRUCTIONS_MAX_CHARS = 1_000;

export default function SettingsPage() {
  const { api, user } = useAuth();
  const { loading, isAuthenticated } = useRequireAuth();
  const [openingPortal, setOpeningPortal] = useState(false);
  const [selectingPlan, setSelectingPlan] = useState<"monthly" | "annual" | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatusResponse | null>(null);
  const [loadingSubscription, setLoadingSubscription] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [globalInstructions, setGlobalInstructions] = useState("");
  const [loadingPreferences, setLoadingPreferences] = useState(true);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [preferencesSaved, setPreferencesSaved] = useState(false);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    const loadPageData = async () => {
      setLoadingSubscription(true);
      setLoadingPreferences(true);
      try {
        await api.fetch<SubscriptionStatusResponse>("/api/subscription/start-trial", { method: "POST" });
        const [subData, prefsData] = await Promise.all([
          api.fetch<SubscriptionStatusResponse>("/api/subscription/me"),
          api.fetch<GenerationPreferencesResponse>("/api/users/me/generation-preferences"),
        ]);
        setSubscription(subData);
        setGlobalInstructions(prefsData.global_instructions);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoadingSubscription(false);
        setLoadingPreferences(false);
      }
    };
    void loadPageData();
  }, [api, isAuthenticated, loading]);

  const saveGlobalInstructions = async () => {
    setSavingPreferences(true);
    setError(null);
    setPreferencesSaved(false);
    try {
      const data = await api.fetch<GenerationPreferencesResponse>(
        "/api/users/me/generation-preferences",
        {
          method: "PATCH",
          body: JSON.stringify({ global_instructions: globalInstructions }),
        },
      );
      setGlobalInstructions(data.global_instructions);
      setPreferencesSaved(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingPreferences(false);
    }
  };

  const openPortal = async () => {
    setOpeningPortal(true);
    setError(null);
    try {
      const data = await api.fetch<{ url: string }>("/api/subscription/portal", { method: "POST" });
      window.location.href = data.url;
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setOpeningPortal(false);
    }
  };

  const status = subscription?.status;
  const isScheduledCancel = status === "active" && !!subscription?.subscription_ends_at;
  const portalOk = subscription?.billing_portal_available === true;
  const showPrimaryBillingPortal =
    portalOk && (status === "active" || status === "past_due");
  const showCanceledBillingLink = portalOk && status === "canceled";

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
      <Card className="mb-5">
        <CardTitle className="text-5xl">Settings</CardTitle>
        <CardDescription className="mt-3 text-base">Account and subscription controls.</CardDescription>
      </Card>
      {loading && !isAuthenticated ? <LoadingState /> : null}
      {error ? (
        <Card className="mb-4 bg-[#B84C2A]">
          <p className="text-sm font-black uppercase tracking-[0.06em] text-black">{error}</p>
        </Card>
      ) : null}

      <Card className="mb-5">
        <CardTitle className="text-4xl">Generation Preferences</CardTitle>
        <CardDescription className="mt-3 text-base">
          Standing instructions applied to every recipe generation unless overridden for a single run.
        </CardDescription>
        {loadingPreferences ? (
          <p className="text-(--color-primary-text)/80 mt-3 text-sm font-bold uppercase tracking-[0.05em]">
            Loading preferences...
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            <label className="text-(--color-primary-text) block text-sm font-bold uppercase tracking-[0.05em]">
              Global instructions
              <textarea
                value={globalInstructions}
                onChange={(e) => {
                  setGlobalInstructions(e.target.value);
                  setPreferencesSaved(false);
                }}
                rows={5}
                maxLength={GLOBAL_INSTRUCTIONS_MAX_CHARS}
                placeholder='e.g. "I am vegetarian. Adapt all recipes accordingly."'
                className="mt-1 w-full border-3 border-black bg-[#2B2B2B] px-3 py-2 text-sm font-semibold normal-case tracking-normal text-[#F5F5F5] outline-none placeholder:text-[#F5F5F5]/40 focus:border-(--color-accent)"
              />
              <span className="text-(--color-primary-text)/70 mt-1 block text-xs font-semibold normal-case tracking-normal">
                {globalInstructions.length.toLocaleString()} / {GLOBAL_INSTRUCTIONS_MAX_CHARS.toLocaleString()} characters
              </span>
            </label>
            <p className="text-(--color-primary-text)/70 text-xs font-semibold normal-case tracking-normal">
              AI-generated recipes are not a substitute for professional dietary or medical advice.
            </p>
            <Button
              onClick={() => void saveGlobalInstructions()}
              disabled={savingPreferences}
              className="text-sm"
            >
              {preferencesSaved ? "Saved" : savingPreferences ? "Saving..." : "Save Preferences"}
            </Button>
          </div>
        )}
      </Card>

      <Card className="mb-5">
        <CardTitle className="text-4xl">Account</CardTitle>
        <p className="text-(--color-primary-text)/80 mt-3 text-sm font-bold uppercase tracking-[0.05em]">
          Email: {user?.email || "Unavailable"}
        </p>
      </Card>

      <Card>
        <CardTitle className="text-4xl">Subscription</CardTitle>
        {loadingSubscription ? (
          <p className="text-(--color-primary-text)/80 mb-3 mt-3 text-sm font-bold uppercase tracking-[0.05em]">
            Loading subscription status...
          </p>
        ) : (
          <TrialStatusBanner subscription={subscription} selectingPlan={selectingPlan} onChoosePlan={choosePlan} className="mb-3" />
        )}

        {!loadingSubscription && subscription ? (
          <div className="mt-4 flex flex-col gap-3">
            {showPrimaryBillingPortal ? (
              <Button
                onClick={() => void openPortal()}
                disabled={openingPortal}
                variant="secondary"
                className="text-sm"
              >
                {openingPortal
                  ? "Opening…"
                  : isScheduledCancel
                    ? "Manage subscription & resume renewal"
                    : "Manage subscription & billing"}
              </Button>
            ) : null}
            {showCanceledBillingLink ? (
              <p className="text-(--color-primary-text)/75 text-xs font-bold uppercase tracking-[0.05em]">
                Need receipts or your card on file?{" "}
                <button
                  type="button"
                  onClick={() => void openPortal()}
                  disabled={openingPortal}
                  className="inline font-black text-(--color-primary-text) underline decoration-2 underline-offset-2 hover:text-[#ff6d40] disabled:opacity-60"
                >
                  {openingPortal ? "Opening…" : "Open Stripe billing portal"}
                </button>
              </p>
            ) : null}
          </div>
        ) : null}
      </Card>
    </PageShell>
  );
}
