"use client";

import { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
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
          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
            <div>
              <Image
                src="/branding/mmp-logo-primary.svg"
                alt="Major Meal Prep logo"
                width={640}
                height={220}
                className="h-auto w-full"
                priority
              />
            </div>

            <div>
              <CardTitle className="text-5xl">Turn Any Recipe Into a Macro-Perfect Meal Prep Plan - In Seconds</CardTitle>
              <CardDescription className="mt-4 max-w-2xl text-base">
                Paste a link from any website or YouTube video. Set your targets. Get a prep-ready recipe calibrated
                to your exact servings, calories, and protein goals.
              </CardDescription>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/sign-up">
                  <Button className="px-6 py-3">Start Free Trial - No Credit Card</Button>
                </Link>
                <Link href="/sign-in">
                  <Button variant="secondary" className="px-6 py-3">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
          </div>

        </Card>

        <Card className="mb-6">
          <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">How It Works</p>
          <CardTitle className="mt-2 text-4xl">From Recipe Link to Meal Prep Plan in 3 Steps</CardTitle>
          <CardDescription className="mt-3 text-sm">
            No manual math. No spreadsheets. Just paste, set, and prep.
          </CardDescription>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div>
              <div className="mb-3 inline-flex border-3 border-black bg-[#7B806A] p-3">
                <svg
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                  className="h-8 w-8 stroke-(--color-primary-text)"
                  fill="none"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11 4.93" />
                  <path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07L13 19.07" />
                </svg>
              </div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
                1. Paste Your Recipe Link
              </p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">
                Drop in any URL from a food blog, cooking site, or YouTube video. Our AI extracts the full recipe
                automatically - no copy-pasting, no reformatting.
              </p>
            </div>
            <div>
              <div className="mb-3 inline-flex border-3 border-black bg-[#7B806A] p-3">
                <svg
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                  className="h-8 w-8 stroke-(--color-primary-text)"
                  fill="none"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="8" />
                  <circle cx="12" cy="12" r="2.5" />
                  <path d="M12 4v2.5" />
                  <path d="M12 17.5V20" />
                  <path d="M4 12h2.5" />
                  <path d="M17.5 12H20" />
                </svg>
              </div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
                2. Set Your Meal Prep Targets
              </p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">
                Tell us how many servings you need, your target calories per portion, and your protein goal. Major
                Meal Prep scales and recalculates everything to match.
              </p>
            </div>
            <div>
              <div className="mb-3 inline-flex border-3 border-black bg-[#7B806A] p-3">
                <svg
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                  className="h-8 w-8 stroke-(--color-primary-text)"
                  fill="none"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M7 3h8l4 4v14H7z" />
                  <path d="M15 3v5h4" />
                  <path d="m10 14 2 2 4-4" />
                </svg>
              </div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
                3. Get Your Prep-Ready Plan
              </p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">
                Receive a fully converted recipe with adjusted ingredients and macros per serving. Save it to your
                personal dashboard and come back anytime.
              </p>
            </div>
          </div>

          <div className="mt-6">
            <Link href="/sign-up">
              <Button className="px-6 py-3">Try It Free - No Credit Card Needed</Button>
            </Link>
          </div>
        </Card>

        <Card className="mb-6">
          <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">Why It Works</p>
          <CardTitle className="mt-2 text-4xl">Stop Wasting Time on Manual Macro Math</CardTitle>
          <CardDescription className="mt-3 text-sm">
            Consistency is what builds results - not perfection. Major Meal Prep removes the friction between finding
            a recipe you love and actually sticking to your nutrition plan week after week.
          </CardDescription>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div>
              <div className="mb-3 border-3 border-dashed border-black bg-[#7B806A] p-3">
                <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">
                  Image Placeholder - Save Hours
                </p>
              </div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
                Save Hours Every Week
              </p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">
                What used to take a calculator, a spreadsheet, and 30 minutes now takes under a minute. Spend that
                time in the gym, not doing nutrition math.
              </p>
            </div>
            <div>
              <div className="mb-3 border-3 border-dashed border-black bg-[#7B806A] p-3">
                <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">
                  Image Placeholder - Hit Macros
                </p>
              </div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
                Hit Your Macros Consistently
              </p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">
                Every recipe is scaled to your exact targets - calories, protein, and servings - so you know precisely
                what you&apos;re eating before you cook a single bite.
              </p>
            </div>
            <div>
              <div className="mb-3 border-3 border-dashed border-black bg-[#7B806A] p-3">
                <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">
                  Image Placeholder - Organized Library
                </p>
              </div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
                Your Recipe Library, Organized
              </p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">
                Save converted recipes to your personal collection. Browse community-published plans for inspiration.
                Build a go-to library you can rely on week after week.
              </p>
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">Social Proof</p>
          <CardTitle className="mt-2 text-4xl">Trusted by Meal Preppers Who Mean Business</CardTitle>
          <CardDescription className="mt-3 text-sm">Real people. Real consistency. Real results.</CardDescription>
          <p className="text-(--color-primary-text)/70 mt-2 text-xs font-bold uppercase tracking-[0.05em]">
            Testimonials below are placeholders - replace with verified user quotes.
          </p>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="space-y-3">
              <p className="text-(--color-primary-text)/85 text-sm">
                &quot;I found a high-protein chicken recipe on YouTube, plugged it in, and had a full 5-day meal plan
                calibrated to my macros in literally one minute. Game changer.&quot;
              </p>
              <p className="text-(--color-primary-text) text-xs font-black uppercase tracking-[0.05em]">
                - Alex R., Competitive Bodybuilder
              </p>
              <div className="border-3 border-dashed border-black bg-[#7B806A] p-3">
                <p className="text-(--color-primary-text) text-xs font-bold uppercase tracking-[0.05em]">
                  Testimonial Image Placeholder
                </p>
              </div>
            </div>
            <div className="space-y-3">
              <p className="text-(--color-primary-text)/85 text-sm">
                &quot;I used to dread Sunday prep because of all the math. Now I just paste the link and it&apos;s done.
                My adherence has never been better.&quot;
              </p>
              <p className="text-(--color-primary-text) text-xs font-black uppercase tracking-[0.05em]">
                - Jamie L., Busy Professional &amp; Macro-Tracker
              </p>
              <div className="border-3 border-dashed border-black bg-[#7B806A] p-3">
                <p className="text-(--color-primary-text) text-xs font-bold uppercase tracking-[0.05em]">
                  Testimonial Image Placeholder
                </p>
              </div>
            </div>
            <div className="space-y-3">
              <p className="text-(--color-primary-text)/85 text-sm">
                &quot;The saved recipe library alone is worth it. I&apos;ve built up a collection of 20+ go-to meals that
                all hit my targets. No more starting from scratch.&quot;
              </p>
              <p className="text-(--color-primary-text) text-xs font-black uppercase tracking-[0.05em]">
                - Morgan T., Gym-Goer &amp; Home Cook
              </p>
              <div className="border-3 border-dashed border-black bg-[#7B806A] p-3">
                <p className="text-(--color-primary-text) text-xs font-bold uppercase tracking-[0.05em]">
                  Testimonial Image Placeholder
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-(--color-primary-text) text-3xl font-black">14 Day Free Trial</p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">Full AI access, no credit card required</p>
            </div>
            <div>
              <p className="text-(--color-primary-text) text-3xl font-black">60s</p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">Average conversion time from paste to plan</p>
            </div>
            <div>
              <p className="text-(--color-primary-text) text-3xl font-black">100%</p>
              <p className="text-(--color-primary-text)/85 mt-2 text-sm">Macro accuracy to your exact targets</p>
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <p className="text-(--color-primary-text)/70 text-xs font-black uppercase tracking-[0.08em]">Pricing</p>
          <CardTitle className="mt-2 text-4xl">Start Free. Stay Because It Works.</CardTitle>
          <CardDescription className="mt-3 text-sm">
            No commitment to get started. Full AI recipe conversion unlocked for 14 days - then choose the plan that
            fits your routine.
          </CardDescription>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">
                Free Account
              </p>
              <ul className="mt-2 space-y-1 text-sm text-(--color-primary-text)/85">
                <li>Browse community-published recipes</li>
                <li>Save recipes to your collection</li>
                <li>No AI recipe generation</li>
              </ul>
              <p className="text-(--color-primary-text) mt-3 text-sm font-black uppercase tracking-[0.05em]">$0 / forever</p>
            </div>
            <div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">Pro - Monthly</p>
              <ul className="mt-2 space-y-1 text-sm text-(--color-primary-text)/85">
                <li>Unlimited AI recipe conversions</li>
                <li>Full macro calibration tools</li>
                <li>Personal recipe library + community access</li>
              </ul>
              <p className="text-(--color-primary-text) mt-3 text-sm font-black uppercase tracking-[0.05em]">
                [Price] / month after 14-day free trial
              </p>
            </div>
            <div>
              <p className="text-(--color-primary-text) text-sm font-black uppercase tracking-[0.05em]">Pro - Annual</p>
              <ul className="mt-2 space-y-1 text-sm text-(--color-primary-text)/85">
                <li>Everything in Pro Monthly</li>
                <li>Best value - save vs. monthly</li>
                <li>Priority support</li>
              </ul>
              <p className="text-(--color-primary-text) mt-3 text-sm font-black uppercase tracking-[0.05em]">
                [Price] / year after 14-day free trial
              </p>
            </div>
          </div>

          <p className="text-(--color-primary-text)/70 mt-4 text-xs font-bold uppercase tracking-[0.05em]">
            All paid plans start with a 14-day free trial. No credit card required to begin. Cancel anytime.
          </p>
        </Card>

        <Card>
          <CardTitle className="text-4xl">Your Macros. Your Meals. On Schedule.</CardTitle>
          <CardDescription className="mt-3 text-sm">
            Stop letting great recipes go to waste because the math is too much. Major Meal Prep does the heavy
            lifting so you can focus on what actually matters - showing up, eating well, and hitting your goals.
          </CardDescription>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/sign-up">
              <Button className="px-8 py-3">Create Your Free Account</Button>
            </Link>
            <Link href="/sign-in">
              <Button variant="secondary" className="px-8 py-3">
                Sign In
              </Button>
            </Link>
          </div>
          <p className="text-(--color-primary-text)/70 mt-4 text-xs font-bold uppercase tracking-[0.05em]">
            14-day free trial - No credit card required - Cancel anytime
          </p>
        </Card>
      </main>
    </div>
  );
}
