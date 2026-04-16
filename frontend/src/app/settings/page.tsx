"use client";

import { useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { AppNav, getErrorMessage, LoadingState, PageShell, useRequireAuth } from "@/lib/route-helpers";

export default function SettingsPage() {
  const { api, user } = useAuth();
  const { loading, isAuthenticated } = useRequireAuth();
  const [openingPortal, setOpeningPortal] = useState(false);
  const [startingTrial, setStartingTrial] = useState<"monthly" | "annual" | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const startTrial = async (plan: "monthly" | "annual") => {
    setStartingTrial(plan);
    setError(null);
    try {
      const data = await api.fetch<{ url: string }>("/api/subscription/checkout", {
        method: "POST",
        body: JSON.stringify({ plan }),
      });
      window.location.href = data.url;
    } catch (err) {
      setError(getErrorMessage(err));
      setStartingTrial(null);
    }
  };

  return (
    <PageShell>
      <AppNav />
      <h1 className="mb-2 text-3xl font-bold">Settings</h1>
      {loading && !isAuthenticated ? <LoadingState /> : null}
      {error ? <p className="mb-4 rounded border border-red-700 bg-red-950 p-3 text-red-300">{error}</p> : null}

      <section className="mb-5 rounded border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-2 text-lg font-semibold">Account</h2>
        <p className="text-sm text-neutral-400">Email: {user?.email || "Unavailable"}</p>
        <p className="text-sm text-neutral-400">UID: {user?.uid || "Unavailable"}</p>
      </section>

      <section className="rounded border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-lg font-semibold">Subscription</h2>
        <div className="mb-3 flex flex-wrap gap-3">
          <button
            onClick={() => void startTrial("monthly")}
            disabled={!!startingTrial}
            className="rounded bg-lime-500 px-4 py-2 text-sm font-semibold text-black hover:bg-lime-400 disabled:opacity-50"
          >
            {startingTrial === "monthly" ? "Redirecting..." : "Start trial (monthly)"}
          </button>
          <button
            onClick={() => void startTrial("annual")}
            disabled={!!startingTrial}
            className="rounded border border-lime-500 px-4 py-2 text-sm font-semibold text-lime-300 hover:bg-lime-950 disabled:opacity-50"
          >
            {startingTrial === "annual" ? "Redirecting..." : "Start trial (annual)"}
          </button>
        </div>

        <button
          onClick={() => void openPortal()}
          disabled={openingPortal}
          className="rounded border border-neutral-600 px-4 py-2 text-sm text-neutral-200 hover:bg-neutral-800 disabled:opacity-50"
        >
          {openingPortal ? "Opening portal..." : "Manage subscription in Stripe portal"}
        </button>
      </section>
    </PageShell>
  );
}
