"use client";

import Link from "next/link";
import { useAuth } from "@/lib/AuthContext";

export default function HomePage() {
  const { user, loading, signOut } = useAuth();

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
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-black px-4">
      <main className="flex flex-col items-center gap-8 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-neutral-50">
          Meal Prep Workflow
        </h1>
        <p className="text-lg text-neutral-400">
          Signed in as <span className="font-medium text-neutral-50">{user.email}</span>
        </p>
        <button
          onClick={() => signOut()}
          className="rounded-lg border border-neutral-700 px-6 py-3 font-medium text-neutral-50 transition-colors hover:bg-neutral-800"
        >
          Sign Out
        </button>
      </main>
    </div>
  );
}
