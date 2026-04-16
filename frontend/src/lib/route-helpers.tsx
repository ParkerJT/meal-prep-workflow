"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/AuthContext";

export function useRequireAuth() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      const next = encodeURIComponent(pathname || "/");
      router.replace(`/sign-in?next=${next}`);
    }
  }, [loading, pathname, router, user]);

  return { user, loading, isAuthenticated: !!user };
}

export function AppNav() {
  return (
    <nav className="mb-8 flex flex-wrap items-center gap-3 text-sm">
      <Link className="rounded border border-neutral-700 px-3 py-1 text-neutral-200 hover:bg-neutral-800" href="/">
        Home
      </Link>
      <Link className="rounded border border-neutral-700 px-3 py-1 text-neutral-200 hover:bg-neutral-800" href="/dashboard">
        Dashboard
      </Link>
      <Link className="rounded border border-neutral-700 px-3 py-1 text-neutral-200 hover:bg-neutral-800" href="/recipes">
        Recipes
      </Link>
      <Link className="rounded border border-neutral-700 px-3 py-1 text-neutral-200 hover:bg-neutral-800" href="/generate">
        Generate
      </Link>
      <Link className="rounded border border-neutral-700 px-3 py-1 text-neutral-200 hover:bg-neutral-800" href="/settings">
        Settings
      </Link>
    </nav>
  );
}

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-black px-4 py-10 text-neutral-100">
      <main className="mx-auto w-full max-w-4xl">{children}</main>
    </div>
  );
}

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <p className="text-neutral-400">{label}</p>;
}

export function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}
