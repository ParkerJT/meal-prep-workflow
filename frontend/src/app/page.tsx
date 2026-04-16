"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/AuthContext";
import { AppNav } from "@/lib/route-helpers";

export default function HomePage() {
  const { user, loading, signOut, api } = useAuth();
  const [validateResult, setValidateResult] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);

  const handleValidate = async () => {
    setValidating(true);
    setValidateResult(null);
    try {
      const data = await api.fetch<{ status: string; message: string; user?: { uid: string; email?: string } }>(
        "/api/auth/validate",
        { method: "POST" }
      );
      setValidateResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setValidateResult(`Error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setValidating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black">
        <p className="text-neutral-50">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-black px-4">
        <main className="flex flex-col items-center gap-8 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-neutral-50">
            Meal Prep Workflow
          </h1>
          <p className="max-w-md text-lg text-neutral-400">
            Sign in to get started.
          </p>
          <div className="flex flex-col items-center gap-4">
            <div className="flex gap-4">
              <Link
                href="/sign-in"
                className="rounded-lg bg-lime-500 px-6 py-3 font-bold text-black transition-colors hover:bg-lime-400"
              >
                Sign In
              </Link>
              <Link
                href="/sign-up"
                className="rounded-lg border border-neutral-700 bg-neutral-900 px-6 py-3 font-bold text-neutral-50 transition-colors hover:bg-neutral-800"
              >
                Sign Up
              </Link>
            </div>
            <div className="mt-4 flex flex-col items-center gap-2">
              <p className="text-sm text-neutral-500">Test API (no token — should fail)</p>
              <button
                onClick={handleValidate}
                disabled={validating}
                className="rounded-lg border border-neutral-600 bg-neutral-800 px-4 py-2 text-sm text-neutral-300 transition-colors hover:bg-neutral-700 disabled:opacity-50"
              >
                {validating ? "Validating..." : "Validate Token"}
              </button>
              {validateResult && (
                <pre className="mt-2 max-w-md overflow-auto rounded bg-neutral-900 p-3 text-left text-xs text-neutral-400">
                  {validateResult}
                </pre>
              )}
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-black px-4">
      <main className="flex flex-col items-center gap-8 text-center">
        <AppNav />
        <h1 className="text-4xl font-extrabold tracking-tight text-neutral-50">
          Meal Prep Workflow
        </h1>
        <p className="text-lg text-neutral-400">
          Signed in as <span className="font-medium text-neutral-50">{user.email}</span>
        </p>
        <div className="flex flex-col items-center gap-4">
          <button
            onClick={() => signOut()}
            className="rounded-lg border border-neutral-700 px-6 py-3 font-medium text-neutral-50 transition-colors hover:bg-neutral-800"
          >
            Sign Out
          </button>
          <div className="flex flex-col items-center gap-2">
            <p className="text-sm text-neutral-500">Test API (with token — should succeed)</p>
            <button
              onClick={handleValidate}
              disabled={validating}
              className="rounded-lg border border-lime-700 bg-lime-950 px-4 py-2 text-sm text-lime-200 transition-colors hover:bg-lime-900 disabled:opacity-50"
            >
              {validating ? "Validating..." : "Validate Token"}
            </button>
            {validateResult && (
              <pre className="mt-2 max-w-md overflow-auto rounded bg-neutral-900 p-3 text-left text-xs text-neutral-400">
                {validateResult}
              </pre>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
