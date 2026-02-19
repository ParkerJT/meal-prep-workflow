# Meal Prep Workflow — Build Plan

A phased build plan for deploying the meal prep recipe platform as a micro SaaS product with subscriptions, Firebase auth/database, and Stripe payments.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Assumptions & Decisions](#assumptions--decisions)
4. [Phase 1: Foundation](#phase-1-foundation)
5. [Phase 2: Recipe Database & Collections](#phase-2-recipe-database--collections)
6. [Phase 2.5: Complete AI Workflow](#phase-25-complete-ai-workflow)
7. [Phase 3: Subscriptions & Gating](#phase-3-subscriptions--gating)
8. [Phase 4: Frontend & User Experience](#phase-4-frontend--user-experience)
9. [Phase 5: Deployment & Environments](#phase-5-deployment--environments)
10. [Phase 6: Launch Prep](#phase-6-launch-prep)
11. [Appendix](#appendix)

---

## Project Overview

### Product Model

| User Type | Access |
|-----------|--------|
| **Free** | Sign up for free. Browse public recipe database. Save recipes to personal collection. No AI workflow. |
| **Trial** | 14-day free trial of AI recipe workflow (extract from URLs + convert to meal prep parameters). |
| **Subscriber** | Full access: AI workflow + recipe database + personal collection. Monthly or annual billing. |

### Core Features

- **AI Recipe Workflow**: Extract structured recipes from web URLs and YouTube videos, then convert to user's meal prep parameters (servings, calories per portion, protein per portion). Full workflow completed in Phase 2.5.
- **Recipe Database**: Shared, deduplicated recipe collection. All users can browse.
- **Personal Collection**: Users save recipes to their collection. User-specific notes per recipe.
- **Dashboard**: Logged-in users view their saved recipes and notes.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js (App Router) |
| **Backend** | FastAPI |
| **Auth** | Firebase Auth (client SDK + Admin SDK verification) |
| **Database** | Firebase Firestore |
| **Payments** | Stripe |
| **Deployment** | GCP: Firebase Hosting (Next.js), Cloud Run (FastAPI), Cloud Build (CI/CD) |
| **Secrets** | GCP Secret Manager |

---

## Assumptions & Decisions

- **Auth providers**: Email/password + Google Sign-In (add others later if needed).
- **Recipe conversion**: AI-powered workflow extracts recipes from web-pages or YouTube videos and converts the recipe to the user's meal prep parameters (portion quantity, calories per portion, grams of protein per portion)
- **Environments**: Separate GCP + Firebase projects for staging and production.
- **Branch strategy**: `staging` branch → staging env; `main` branch → production (with approval gate).

---

## Phase 1: Foundation

**Goal**: Firebase Auth working end-to-end. Backend verifies tokens. Frontend can sign up and sign in.

### 1.1 Firebase Project Setup

- [ ] Create Firebase project (do this twice: `meal-prep-staging`, `meal-prep-production`).
- [ ] Enable Authentication: Email/Password, Google.
- [ ] Enable Firestore (start in test mode; we'll add rules in Phase 2).
- [ ] Create a Web App in Firebase Console; note config (apiKey, projectId, etc.).
- [ ] Generate service account key for backend (Project Settings → Service Accounts → Generate new private key).
- [ ] Store service account JSON in Secret Manager (or env var for local dev).

### 1.2 Backend: Firebase Auth Verification

- [ ] Add `firebase-admin` to backend dependencies.
- [ ] Initialize Firebase Admin in FastAPI startup (load credentials from env/Secret Manager).
- [ ] Create dependency `get_current_user` that:
  - Reads `Authorization: Bearer <token>` header.
  - Verifies token with `auth.verify_id_token()`.
  - Returns `uid` (and optionally user record).
- [ ] Add optional dependency `get_current_user_optional` for endpoints that work for both authenticated and anonymous users.
- [ ] Replace or remove existing `ACCESS_TOKEN` auth in `app/dependencies.py`.
- [ ] Update `app/config.py`: remove Cosmos DB vars; add Firebase project ID, path to service account (or Secret Manager ref).

### 1.3 Frontend: Next.js Scaffold

- [ ] Create Next.js app (App Router) in project root or `frontend/` directory.
- [ ] Add Firebase SDK: `firebase`, `firebase/auth`.
- [ ] Create Firebase config module (use env vars for apiKey, projectId, etc.).
- [ ] Create Auth context/provider: sign in, sign out, `onAuthStateChanged`, token refresh.
- [ ] Build minimal UI: Sign Up, Sign In, Sign Out.
- [ ] Ensure frontend sends `Authorization: Bearer <idToken>` on API calls (create API client utility).

### 1.4 CORS & API Client

- [ ] Configure FastAPI CORS with frontend origin (e.g. `http://localhost:3000` for dev).
- [ ] Create frontend API client that attaches Firebase ID token to requests.
- [ ] Handle 401 responses (e.g. redirect to login or trigger token refresh).

**Deliverable**: User can sign up, sign in, and call a protected FastAPI endpoint with a valid token.

---

## Phase 2: Recipe Database & Collections

**Goal**: Firestore schema in place. Users can browse recipes, save to collection, add notes. Backend handles all Firestore access.

### 2.1 Firestore Schema

**`recipes` collection** (canonical, shared):

```
recipes/{recipeId}
  - id: string (hash of source_url for deduplication)
  - source_url: string
  - source_type: "web" | "youtube"
  - title: string
  - description: string | null
  - servings: number
  - ingredients: array
  - instructions: array
  - created_at: timestamp
  - created_by: string | null (optional, Firebase uid of first creator)
```

**`users/{userId}/saved_recipes` subcollection** (user-specific):

```
users/{userId}/saved_recipes/{savedRecipeId}
  - recipe_id: string (reference to recipes collection)
  - saved_at: timestamp
  - notes: string (user's personal notes)
  - converted_recipe: object | null (optional; full ConvertedRecipe when saved from AI workflow—Phase 2.5)
```

**Recipe ID strategy**: Use `hashlib.sha256(normalized_source_url.encode()).hexdigest()[:32]` for deduplication. Same URL → same recipe.

### 2.2 Firestore Security Rules

- [ ] `recipes`: Read allowed for all (authenticated or not). Write only from backend (Admin SDK bypasses rules).
- [ ] `users/{userId}/saved_recipes`: Read/write only if `request.auth.uid == userId`.

*Note: If all Firestore access goes through the backend, rules can be restrictive; backend uses Admin SDK.*

### 2.3 Backend: Recipe & Collection APIs

- [ ] **GET /api/recipes** — List recipes (paginated). Optional filters. Public or authenticated.
- [ ] **GET /api/recipes/{recipeId}** — Get single recipe. Public.
- [ ] **POST /api/recipes** — Create recipe (from AI extraction or manual). Called when user saves a recipe that doesn't exist yet. Auth required.
- [ ] **GET /api/users/me/saved-recipes** — List current user's saved recipes (with notes). Auth required.
- [ ] **POST /api/users/me/saved-recipes** — Save recipe to collection. Body: `{ recipe_id, notes? }`. Creates `saved_recipes` doc. Auth required.
- [ ] **PATCH /api/users/me/saved-recipes/{savedRecipeId}** — Update notes. Auth required.
- [ ] **DELETE /api/users/me/saved-recipes/{savedRecipeId}** — Remove from collection. Auth required.

### 2.4 Save Flow Logic

When user "saves" a recipe (e.g. from AI extraction result):

1. Compute `recipe_id` from `source_url`.
2. Check if `recipes/{recipe_id}` exists. If not, create it.
3. Create `users/{userId}/saved_recipes` doc with `recipe_id`, `saved_at`, `notes`.

### 2.5 Seed Data (Optional)

- [ ] Add script or admin endpoint to seed `recipes` with initial data for browsing (or rely on user-generated content).

**Deliverable**: Users can browse recipes, save to collection, and add/edit notes. All via backend API.

---

## Phase 2.5: Complete AI Workflow

**Goal**: Finish the full AI workflow—extraction (web + YouTube) and conversion to meal prep parameters. This phase must be complete before Phase 3, which gates the workflow behind subscriptions.

### 2.5.1 Complete Web Extraction

- [ ] Implement `extract_recipe_from_web_page()` in `extraction.py` (currently returns early / incomplete).
- [ ] Add system instructions for web page extraction (similar to `SYSTEM_INSTRUCTIONS_YOUTUBE`).
- [ ] Use OpenAI structured output with `OriginalRecipe` schema.
- [ ] Test with various recipe website formats.

### 2.5.2 Build Conversion Agent

- [ ] Create conversion agent/service that takes `OriginalRecipe` + `UserAdjustments` → `ConvertedRecipe`.
- [ ] Conversion logic: adjust ingredient quantities for target servings; use AI to estimate/calculate nutritional info (calories, protein) and apply user targets.
- [ ] Output conforms to `ConvertedRecipe` model (nutritional_info, conversion_metadata).

### 2.5.3 Wire Full Workflow

- [ ] Update `run_workflow()` in `workflow.py` to accept `UserRequest` (recipe_url + user_adjustments).
- [ ] Flow: extract → convert → return `ConvertedRecipe`.
- [ ] Fix current bug: `recipe_extraction_workflow(UserRequest.recipe_url)` should use `user_request.recipe_url`.
- [ ] Create/update API endpoint: `POST /api/workflow/generate` — accepts URL + adjustments, returns `ConvertedRecipe`.

### 2.5.4 Save Flow for Converted Recipes

- [ ] When user saves from AI workflow result: store `OriginalRecipe` in `recipes` (canonical, keyed by source_url hash).
- [ ] Store `ConvertedRecipe` (or conversion params + result) in `users/{uid}/saved_recipes` — add `converted_recipe` field for workflow-originated saves, so user sees their portion-adjusted version with nutritional info.

**Deliverable**: End-to-end AI workflow: user submits URL + meal prep params → receives converted recipe. Ready to be gated in Phase 3.

---

## Phase 3: Subscriptions & Gating

**Goal**: Stripe subscriptions (monthly/annual) with 14-day trial. Backend checks subscription status before allowing AI workflow.

### 3.1 Stripe Setup

- [ ] Create Stripe account. Create products: Monthly Plan, Annual Plan.
- [ ] Create prices with 14-day trial: `trial_period_days: 14`.
- [ ] Store Stripe secret key and webhook secret in Secret Manager.
- [ ] Use Stripe **test mode** for staging; **live mode** for production.

### 3.2 Subscription Status Storage

Store in Firestore: `users/{userId}/subscription` (or `users/{userId}` document with subscription fields):

```
subscription:
  - stripe_customer_id: string
  - stripe_subscription_id: string | null
  - status: "active" | "trialing" | "past_due" | "canceled" | "none"
  - plan: "monthly" | "annual" | null
  - current_period_end: timestamp | null
  - trial_end: timestamp | null
```

### 3.3 Backend: Stripe Integration

- [ ] Add `stripe` to backend dependencies.
- [ ] **POST /api/subscription/checkout** — Create Stripe Checkout session. Redirect user to Stripe. Auth required.
- [ ] **POST /api/subscription/portal** — Create Stripe Customer Portal session. For managing/canceling subscription. Auth required.
- [ ] **POST /api/webhooks/stripe** — Webhook endpoint. Verify signature. Handle:
  - `checkout.session.completed` — New subscription. Create/update Firestore.
  - `customer.subscription.updated` — Status/plan changes.
  - `customer.subscription.deleted` — Cancellation.
  - `invoice.payment_failed` — Optional: notify user, update status.
- [ ] Create `require_subscription` dependency: checks `users/{uid}/subscription` for `active` or `trialing`. Raise 403 if not.
- [ ] Gate AI workflow endpoint with `require_subscription`.

### 3.4 Trial Logic

- [ ] When user starts trial: Create Stripe Checkout with `subscription_data.trial_period_days: 14`.
- [ ] Stripe webhook sets `status: "trialing"` and `trial_end`.
- [ ] `require_subscription` allows access when `status in ["active", "trialing"]`.
- [ ] After trial ends without payment: Stripe sets status to `canceled` or `past_due`; backend denies AI access.

### 3.5 AI Workflow Gating

- [ ] Update workflow endpoint (e.g. `POST /api/workflow/generate`): require `require_subscription`.
- [ ] Return clear error (e.g. `subscription_required`) when user lacks access.
- [ ] Free users can still call `GET /api/recipes`, save recipes, etc.

**Deliverable**: Free users browse and save. Trial/subscribers access the full AI workflow (extraction + conversion). Stripe handles billing and trials.

---

## Phase 4: Frontend & User Experience

**Goal**: Polished UI for auth, dashboard, recipe browsing, AI workflow, and subscription management.

### 4.1 Pages & Routes

- [ ] **/** — Landing page. CTA to sign up or sign in.
- [ ] **/sign-in**, **/sign-up** — Auth pages.
- [ ] **/dashboard** — User's saved recipes. Auth required.
- [ ] **/recipes** — Browse public recipe database. Pagination, search (if implemented).
- [ ] **/recipes/[id]** — Recipe detail. Show "Save to collection" if logged in. Show notes if in user's collection.
- [ ] **/generate** — AI workflow: URL input, loading state, result. Gated for trial/subscribers.
- [ ] **/settings** or **/account** — Subscription management (link to Stripe Customer Portal), account info.

### 4.2 Auth Flow

- [ ] Protected route wrapper (redirect to sign-in if not authenticated).
- [ ] Token refresh: use `onIdTokenChanged` or refresh before API calls.
- [ ] Persist auth state across reloads (Firebase handles this by default).

### 4.3 Subscription UX

- [ ] On `/generate` for free users: show "Start 14-day free trial" CTA. Redirect to Stripe Checkout.
- [ ] For trial/subscribers: show remaining trial days or plan info.
- [ ] Link to Customer Portal for managing subscription.

### 4.4 Recipe UX

- [ ] Dashboard: list saved recipes with notes preview. Link to detail.
- [ ] Recipe detail: edit notes inline or in modal.
- [ ] After AI extraction: "Save to collection" button with optional notes field.

**Deliverable**: Complete user flows for auth, browsing, saving, AI generation, and subscription.

---

## Phase 5: Deployment & Environments

**Goal**: Staging and production on GCP. CI/CD with Cloud Build. Safe deployment workflow.

### 5.1 GCP Projects

- [ ] Create `meal-prep-staging` GCP project.
- [ ] Create `meal-prep-production` GCP project.
- [ ] Link Firebase projects to respective GCP projects (or use Firebase's project creation).

### 5.2 Backend: Docker & Cloud Run

- [ ] Create `Dockerfile` for FastAPI app in `backend/`.
- [ ] Build and run locally to verify.
- [ ] Deploy to Cloud Run (staging): `gcloud run deploy api --source ./backend --project meal-prep-staging`.
- [ ] Configure env vars / Secret Manager for Cloud Run.
- [ ] Deploy to Cloud Run (production) when ready.

### 5.3 Frontend: Firebase Hosting

- [ ] Configure `firebase.json` for Next.js (use `firebase-frameworks` or static export).
- [ ] Set `next.config.js` env for API URL (staging vs production).
- [ ] Deploy to Firebase Hosting: `firebase deploy --project meal-prep-staging`.
- [ ] Custom domain (optional): configure in Firebase Hosting.

### 5.4 Cloud Build CI/CD

- [ ] Create `cloudbuild-staging.yaml`: build backend image, deploy to Cloud Run (staging), deploy frontend to Firebase Hosting (staging).
- [ ] Create `cloudbuild-production.yaml`: same steps for production project.
- [ ] Create Cloud Build trigger: push to `staging` → run staging build.
- [ ] Create Cloud Build trigger: push to `main` → run production build (add manual approval if desired).
- [ ] Store secrets in Secret Manager; reference in Cloud Build.

### 5.5 Environment Configuration

| Variable | Staging | Production |
|----------|---------|------------|
| Firebase project | meal-prep-staging | meal-prep-production |
| Stripe keys | Test mode | Live mode |
| API URL | api-staging-xxx.run.app | api.yourdomain.com |
| Frontend URL | staging.yourdomain.com | yourdomain.com |

**Deliverable**: Push to `staging` deploys to staging. Push to `main` (with approval) deploys to production.

---

## Phase 6: Launch Prep

**Goal**: Production-ready. Legal, security, and operational basics in place.

### 6.1 Security

- [ ] CORS: restrict to production frontend URL(s).
- [ ] Rate limiting on AI endpoint (e.g. per-user limits).
- [ ] Validate and sanitize all inputs (URLs, notes, etc.).
- [ ] Ensure no secrets in frontend or logs.

### 6.2 Legal & Compliance

- [ ] Terms of Service page.
- [ ] Privacy Policy page.
- [ ] Cookie consent (if using analytics/cookies).
- [ ] Account deletion flow: delete user data, cancel Stripe subscription, delete Firebase user.

### 6.3 Operational

- [ ] Health check endpoint (existing `/health`). Configure Cloud Run to use it.
- [ ] Error tracking (e.g. Sentry) for backend and frontend.
- [ ] Logging: structured logs for debugging.
- [ ] Stripe webhook: ensure production URL is configured and verified.

### 6.4 Documentation

- [ ] README with setup instructions for local dev.
- [ ] Env vars documented in `.env.example`.
- [ ] API documentation (FastAPI auto-generates; ensure it's accessible).

**Deliverable**: Production deployment is secure, compliant, and observable.

---

## Appendix

### A. Current Codebase Notes

- **Workflow**: `recipe_extraction_workflow()` in `extraction.py` returns `OriginalRecipe`. YouTube extraction is complete; web extraction is incomplete (`extract_recipe_from_web_page` returns early). Conversion workflow (meal prep adjustments) is not implemented—**to be completed in Phase 2.5**.
- **Models**: `UserRequest`, `UserAdjustments`, `OriginalRecipe`, `ConvertedRecipe` exist. Conversion agent will consume these in Phase 2.5.
- **Auth**: Current `ACCESS_TOKEN` header auth in `dependencies.py` will be replaced by Firebase token verification.
- **Config**: Cosmos DB vars in `config.py` will be removed; Firebase/Stripe vars added.

### B. Firestore Indexes

You may need composite indexes for queries (e.g. recipes by `created_at`, saved_recipes by `saved_at`). Firestore will prompt when you run a query that requires an index.

### C. Branch Strategy Summary

```
main          ──▶  Production (manual approval or auto after merge)
  │
staging       ──▶  Staging (auto on push)
  │
feature/*     ──▶  Local dev only
```

### D. Dependency Checklist

**Backend (add to pyproject.toml)**:
- `firebase-admin`
- `stripe`
- `google-cloud-firestore` (or use firebase-admin's Firestore)

**Frontend**:
- `firebase`
- `stripe` (for Checkout redirects; no secret keys on frontend)

---

*Document version: 1.1*
