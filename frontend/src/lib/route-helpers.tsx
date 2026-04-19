"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/AuthContext";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

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

export function DashboardBackLink() {
  return (
    <Link href="/dashboard" className="mb-5 inline-flex">
      <Button variant="secondary" className="px-3 py-1.5 text-xs">
        Back To Dashboard
      </Button>
    </Link>
  );
}

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-background min-h-screen px-4 py-10 text-(--color-primary-text)">
      <main className="mx-auto w-full max-w-4xl">{children}</main>
    </div>
  );
}

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <Card className="mb-4">
      <p className="text-(--color-primary-text)/80 text-sm font-black uppercase tracking-[0.06em]">{label}</p>
    </Card>
  );
}

export function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}
