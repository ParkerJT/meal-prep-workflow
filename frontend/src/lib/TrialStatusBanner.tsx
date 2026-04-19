"use client";

import { SubscriptionStatusResponse } from "@/lib/frontend-types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface TrialStatusBannerProps {
  subscription: SubscriptionStatusResponse | null;
  selectingPlan: "monthly" | "annual" | null;
  onChoosePlan: (plan: "monthly" | "annual") => void | Promise<void>;
  className?: string;
}

function getTrialDaysRemaining(subscription: SubscriptionStatusResponse | null): number | null {
  if (subscription?.status !== "trialing" || !subscription.trial_end) return null;
  const ms = new Date(subscription.trial_end).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)));
}

export function TrialStatusBanner({
  subscription,
  selectingPlan,
  onChoosePlan,
  className = "",
}: TrialStatusBannerProps) {
  const trialDaysRemaining = getTrialDaysRemaining(subscription);
  const isExpiredTrial = subscription?.status === "trialing" && trialDaysRemaining === 0;
  const isPaid = subscription?.status === "active";
  const showUpgradeCta = !isPaid;

  return (
    <Card className={`mb-4 ${className}`.trim()}>
      <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
        Status: {subscription?.status || "none"}
      </p>
      <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
        Plan: {subscription?.plan || "none"}
      </p>
      {subscription?.status === "trialing" ? (
        <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
          Trial days remaining: {trialDaysRemaining ?? "unknown"}
        </p>
      ) : null}
      {isExpiredTrial ? (
        <p className="mt-2 text-sm font-black uppercase tracking-[0.05em] text-[#A83E1B]">
          Your free trial has ended. Choose a plan to keep generating recipes.
        </p>
      ) : null}
      {showUpgradeCta ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            onClick={() => void onChoosePlan("monthly")}
            disabled={!!selectingPlan}
            className="px-3 py-1.5 text-xs"
          >
            {selectingPlan === "monthly" ? "Redirecting..." : "Choose Monthly Plan"}
          </Button>
          <Button
            onClick={() => void onChoosePlan("annual")}
            disabled={!!selectingPlan}
            variant="secondary"
            className="px-3 py-1.5 text-xs"
          >
            {selectingPlan === "annual" ? "Redirecting..." : "Choose Annual Plan"}
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
