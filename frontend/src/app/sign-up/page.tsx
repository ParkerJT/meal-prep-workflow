"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { getAuthErrorMessage } from "@/lib/auth-errors";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SignUpPage() {
  const { user, loading, signUp } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMismatch, setPasswordMismatch] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/");
    }
  }, [user, loading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPasswordMismatch(false);

    if (password !== confirmPassword) {
      setPasswordMismatch(true);
      return;
    }

    setSubmitting(true);
    try {
      await signUp(email, password);
      router.replace("/");
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
          <CardTitle>Sign Up</CardTitle>
          <CardDescription>Build your prep account and deploy.</CardDescription>

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
                autoComplete="new-password"
                minLength={6}
                placeholder="At least 6 characters"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="text-(--color-primary-text) mb-1 block text-xs font-black uppercase tracking-widest">
                Confirm Password
              </label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  setPasswordMismatch(false);
                }}
                required
                autoComplete="new-password"
                placeholder="Re-enter password"
              />
              {passwordMismatch && (
                <p className="text-(--color-error) mt-1 text-sm font-bold uppercase tracking-[0.06em]">Passwords do not match.</p>
              )}
            </div>

            {error && (
              <p className="text-(--color-error) text-sm font-bold uppercase tracking-[0.06em]">{error}</p>
            )}

            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? "Creating Account..." : "Sign Up"}
            </Button>
          </form>

          <p className="text-(--color-primary-text) mt-6 text-center text-sm font-bold uppercase tracking-[0.06em]">
            Already have an account?{" "}
            <Link href="/sign-in" className="underline decoration-3 underline-offset-2">
              Sign In
            </Link>
          </p>
        </Card>
      </main>
    </div>
  );
}
