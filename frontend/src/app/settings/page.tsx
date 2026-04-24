"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { SubscriptionStatusResponse } from "@/lib/frontend-types";
import { TrialStatusBanner } from "@/lib/TrialStatusBanner";
import { getErrorMessage, LoadingState, LoggedInUtilityHeader, PageShell, useRequireAuth } from "@/lib/route-helpers";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  const { api, user } = useAuth();
  const { loading, isAuthenticated } = useRequireAuth();
  const [openingPortal, setOpeningPortal] = useState(false);
  const [selectingPlan, setSelectingPlan] = useState<"monthly" | "annual" | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatusResponse | null>(null);
  const [loadingSubscription, setLoadingSubscription] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    const loadSubscription = async () => {
      setLoadingSubscription(true);
      try {
        await api.fetch<SubscriptionStatusResponse>("/api/subscription/start-trial", { method: "POST" });
        const data = await api.fetch<SubscriptionStatusResponse>("/api/subscription/me");
        setSubscription(data);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoadingSubscription(false);
      }
    };
    void loadSubscription();
  }, [api, isAuthenticated, loading]);

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
        <CardTitle className="text-4xl">Account</CardTitle>
        <p className="text-(--color-primary-text)/80 mt-3 text-sm font-bold uppercase tracking-[0.05em]">
          Email: {user?.email || "Unavailable"}
        </p>
        <p className="text-(--color-primary-text)/80 text-sm font-bold uppercase tracking-[0.05em]">
          UID: {user?.uid || "Unavailable"}
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

        <Button
          onClick={() => void openPortal()}
          disabled={openingPortal}
          variant="secondary"
          className="text-sm"
        >
          {openingPortal ? "Opening Portal..." : "Manage Subscription In Stripe Portal"}
        </Button>
      </Card>
    </PageShell>
  );
}
