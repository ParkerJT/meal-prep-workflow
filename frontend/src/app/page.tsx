"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, router, user]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-(--color-primary-text) font-bold uppercase tracking-[0.08em]">Loading...</p>
      </div>
    );
  }

  if (user) {
    return null;
  }

  return (
    <div className="bg-background min-h-screen px-4 py-10">
      <main className="mx-auto w-full max-w-5xl">
        <Card className="mb-6">
          <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">
            Logo Placeholder
          </p>
          <div className="mt-2 border-3 border-dashed border-black bg-[#7B806A] p-4">
            <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.07em]">
              Insert brand logo mark + wordmark
            </p>
          </div>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
          <Card>
            <CardTitle className="text-6xl">Meal Prep Workflow</CardTitle>
            <CardDescription className="mt-4 max-w-xl text-base">
              Build practical, macro-aligned meal plans with an interface made for speed and consistency.
            </CardDescription>

            <div className="mt-6 border-3 border-dashed border-black bg-[#7B806A] p-4">
              <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">
                Hero Image Placeholder
              </p>
              <p className="text-(--color-primary-text) mt-2 text-sm font-bold uppercase tracking-[0.05em]">
                Reserve this area for key visual branding or hero illustration.
              </p>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/sign-up">
                <Button className="px-6 py-3">Start Free Trial</Button>
              </Link>
              <Link href="/sign-in">
                <Button variant="secondary" className="px-6 py-3">
                  Sign In
                </Button>
              </Link>
            </div>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardTitle className="text-4xl">Why It Works</CardTitle>
              <ul className="mt-4 space-y-2">
                <li className="text-(--color-primary-text)/85 text-sm font-bold uppercase tracking-[0.04em]">
                  Fast recipe conversion for weekly prep.
                </li>
                <li className="text-(--color-primary-text)/85 text-sm font-bold uppercase tracking-[0.04em]">
                  Macro targets built into generation flow.
                </li>
                <li className="text-(--color-primary-text)/85 text-sm font-bold uppercase tracking-[0.04em]">
                  Saved collection stays organized by account.
                </li>
              </ul>
            </Card>

            <Card>
              <CardTitle className="text-4xl">Trial + Plans</CardTitle>
              <CardDescription className="mt-3 text-sm">
                Start with a free trial, then choose monthly or annual access for continued generation.
              </CardDescription>
              <p className="text-(--color-primary-text)/70 mt-3 text-xs font-bold uppercase tracking-[0.05em]">
                Pricing copy placeholder (final plan details TBD)
              </p>
            </Card>

            <Card>
              <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">
                Secondary Artwork Placeholder
              </p>
              <div className="mt-2 border-3 border-dashed border-black bg-[#7B806A] p-4">
                <p className="text-(--color-primary-text) text-sm font-bold uppercase tracking-[0.05em]">
                  Optional supporting graphic panel.
                </p>
              </div>
            </Card>
          </div>
        </div>

        <Card className="mt-6">
          <CardDescription className="text-center text-sm">
            Ready to build? Start your trial and generate your first structured recipe workflow.
          </CardDescription>
          <div className="mt-4 flex justify-center">
            <Link href="/sign-up">
              <Button className="px-8 py-3">Create Account</Button>
            </Link>
          </div>
        </Card>
      </main>
    </div>
  );
}
