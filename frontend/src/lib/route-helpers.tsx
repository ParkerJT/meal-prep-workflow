"use client";

import Link from "next/link";
import Image from "next/image";
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

export function LoggedInUtilityHeader({
  backHref = "/dashboard",
  backLabel = "Back To Dashboard",
}: {
  backHref?: string;
  backLabel?: string;
}) {
  const { signOut } = useAuth();

  return (
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
      <Link href="/dashboard" className="inline-flex">
        <Image
          src="/branding/mmp-icon-full.png"
          alt="Major Meal Prep logo"
          width={72}
          height={72}
          className="h-auto w-16 sm:w-18"
          priority
        />
      </Link>
      <div className="flex flex-wrap items-center gap-2">
        <Link href={backHref} className="inline-flex">
          <Button variant="secondary" className="px-3 py-1.5 text-xs">
            {backLabel}
          </Button>
        </Link>
        <Button variant="secondary" className="px-3 py-1.5 text-xs" onClick={() => signOut()}>
          Sign Out
        </Button>
      </div>
    </div>
  );
}

export function PageShell({
  children,
  showLoggedInHeader = true,
}: {
  children: React.ReactNode;
  showLoggedInHeader?: boolean;
}) {
  const { user } = useAuth();

  return (
    <div className="bg-background min-h-screen px-4 py-10 text-(--color-primary-text)">
      <main className="mx-auto w-full max-w-4xl">
        {user && showLoggedInHeader ? (
          <Card className="mb-6">
            <div className="flex flex-wrap items-center gap-3">
              <Link href="/dashboard" className="inline-flex">
                <Image
                  src="/branding/mmp-logo-primary.svg"
                  alt="Major Meal Prep logo"
                  width={360}
                  height={96}
                  className="h-auto w-full max-w-[240px]"
                  priority
                />
              </Link>
            </div>
          </Card>
        ) : null}
        {children}
      </main>
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
