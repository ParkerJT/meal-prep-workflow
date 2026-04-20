"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { getAuthErrorMessage } from "@/lib/auth-errors";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SignInPage() {
  const { user, loading, signIn, signInWithGoogle } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace(nextPath);
    }
  }, [user, loading, router, nextPath]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(email, password);
      router.replace(nextPath);
    } catch (err) {
      setError(getAuthErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await signInWithGoogle();
      router.replace(nextPath);
    } catch (err) {
      setError(getAuthErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

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
    <div className="bg-background flex min-h-screen flex-col items-center justify-center px-4">
      <main className="w-full max-w-md">
        <Card>
          <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">
            Brand Logo
          </p>
          <div className="mt-2 border-3 border-black bg-[#7B806A] p-3">
            <Image
              src="/branding/mmp-logo-primary.svg"
              alt="Major Meal Prep logo"
              width={420}
              height={120}
              className="h-auto w-full max-w-xs"
              priority
            />
          </div>
          <CardTitle>Sign In</CardTitle>
          <CardDescription>Access your field ration workflow.</CardDescription>

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <div>
              <label htmlFor="email" className="text-(--color-primary-text) mb-1 block text-xs font-black uppercase tracking-widest">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="text-(--color-primary-text) mb-1 block text-xs font-black uppercase tracking-widest">
                Password
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            {error && (
              <p className="text-(--color-error) text-sm font-bold uppercase tracking-[0.06em]">{error}</p>
            )}

            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? "Signing In..." : "Sign In"}
            </Button>
          </form>

          <div className="my-4 flex items-center gap-4">
            <div className="h-[3px] flex-1 bg-black" />
            <span className="text-(--color-primary-text) text-xs font-black uppercase tracking-widest">or</span>
            <div className="h-[3px] flex-1 bg-black" />
          </div>

          <Button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={submitting}
            variant="secondary"
            className="w-full"
          >
            Sign In With Google
          </Button>

          <p className="text-(--color-primary-text) mt-6 text-center text-sm font-bold uppercase tracking-[0.06em]">
            Don&apos;t have an account?{" "}
            <Link href="/sign-up" className="underline decoration-3 underline-offset-2">
              Sign Up
            </Link>
          </p>
        </Card>
      </main>
    </div>
  );
}
