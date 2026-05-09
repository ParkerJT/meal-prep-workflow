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

  const status = subscription?.status;
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
                {openingPortal ? "Opening…" : "Manage subscription & billing"}
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
