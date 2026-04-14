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
| **Free** | Sign up for free. Browse **published** recipes from other users. Save copies to personal collection. No AI workflow. |
| **Trial** | 14-day free trial of AI recipe workflow (extract from URLs + convert to meal prep parameters). |
| **Subscriber** | Full access: AI workflow + browse/save **published** recipes + personal collection. Monthly or annual billing. |

### Core Features

- **AI Recipe Workflow**: Extract structured recipes from web URLs and YouTube videos, then convert to user's meal prep parameters (servings, calories per portion, protein per portion). Full workflow completed in Phase 2.5.
- **Published recipes**: Users can publish saved recipes (converted snapshot) for others to browse. Browsing is via the published-recipes API, not the internal canonical store.
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

- [x] Create Firebase project (do this twice: `meal-prep-staging`, `meal-prep-production`).
- [x] Enable Authentication: Email/Password, Google.
- [x] Enable Firestore (start in test mode; we'll add rules in Phase 2).
- [x] Create a Web App in Firebase Console; note config (apiKey, projectId, etc.).
- [x] Generate service account key for backend (Project Settings → Service Accounts → Generate new private key).
- [x] Store service account JSON in Secret Manager (or env var for local dev).

### 1.2 Backend: Firebase Auth Verification

- [x] Add `firebase-admin` to backend dependencies.
- [x] Initialize Firebase Admin in FastAPI startup (load credentials from env/Secret Manager).
- [x] Create dependency `get_current_user` that:
  - Reads `Authorization: Bearer <token>` header.
  - Verifies token with `auth.verify_id_token()`.
  - Returns `uid` (and optionally user record).
- [x] Add optional dependency `get_current_user_optional` for endpoints that work for both authenticated and anonymous users.
- [x] Replace or remove existing `ACCESS_TOKEN` auth in `app/dependencies.py`.
- [x] Update `app/config.py`: remove Cosmos DB vars; add Firebase project ID, path to service account (or Secret Manager ref).

### 1.3 Frontend: Next.js Scaffold

- [x] Create Next.js app (App Router) in project root or `frontend/` directory.
- [x] Add Firebase SDK: `firebase`, `firebase/auth`.
- [x] Create Firebase config module (use env vars for apiKey, projectId, etc.).
- [x] Create Auth context/provider: sign in, sign out, `onAuthStateChanged`, token refresh.
- [x] Build minimal UI: Sign Up, Sign In, Sign Out.
- [x] Ensure frontend sends `Authorization: Bearer <idToken>` on API calls (create API client utility).

### 1.4 CORS & API Client

- [x] Configure FastAPI CORS with frontend origin (e.g. `http://localhost:3000` for dev).
- [x] Create frontend API client that attaches Firebase ID token to requests.
- [x] Handle 401 responses (e.g. redirect to login or trigger token refresh).

**Deliverable**: User can sign up, sign in, and call a protected FastAPI endpoint with a valid token.

---

## Phase 2: Recipe Database & Collections

**Goal**: Firestore schema in place. Users can browse **published** recipes from others, save copies to their collection, add personal notes, and (later) publish their own saves. Backend handles all Firestore access. The internal **`original_recipes`** store is **not** the public catalog—it exists so the AI workflow can skip re-extraction when a URL was already processed.

**Scope (Phase 2 vs Phase 2.5)**: Phase 2 implements Firestore schema, security rules, and recipe/collection APIs end-to-end. You can validate flows using seeded or manually created **`original_recipes`** data. The **AI extraction + conversion pipeline** and persisting a full **`converted_recipe`** on save are **Phase 2.5**; until then, `converted_recipe` may remain null for workflow-originated saves.

### 2.1 Firestore Schema

**Pydantic source of truth**: Field names and nesting for persisted documents are defined in `backend/app/services/agents/models.py`. Extraction continues to use **`OriginalRecipe`** only (LLM output). The Firestore document for the canonical store uses **`OriginalRecipeDocument`** (subclass of `OriginalRecipe` with app-populated metadata). User saves use **`SavedRecipe`**.

---

**`original_recipes` collection** (internal; not a public catalog):

Purpose: deduplicated cache of extracted **original** recipe text keyed by source URL so the workflow can skip extraction when the same normalized URL was already processed. Clients do not browse this collection; public discovery uses **published** `saved_recipes` (see below).

```
original_recipes/{recipeId}
  - id: string (same as document id; hash of normalized source_url for deduplication)
  - source_url: string
  - source_type: "web" | "youtube"
  - title, description, servings, ingredients, instructions — same as OriginalRecipe / OriginalRecipeDocument
  - created_at: timestamp
  - created_by: string | null (optional, Firebase uid of first writer)
```

**`OriginalRecipeDocument`** (Pydantic): extends **`OriginalRecipe`** with `id`, `source_url`, `source_type`, `created_at`, `created_by`. The repository layer maps Firestore `Timestamp` fields to/from `datetime` when validating these models.

---

**`users/{userId}/saved_recipes` subcollection** (user-specific):

```
users/{userId}/saved_recipes/{savedRecipeId}
  - recipe_id: string (reference to original_recipes/{recipeId})
  - saved_at: timestamp
  - notes: string (personal; not shown to other users when viewing a published recipe)
  - converted_recipe: object | null — full snapshot; matches ConvertedRecipe (Phase 2.5 when workflow persists)
  - published: boolean
  - copied_from_user_id: string | null (set when this doc was created by copying another user's published save)
  - copied_from_saved_recipe_id: string | null (source doc id under copied_from_user_id)
```

**`converted_recipe` shape**: Stored as nested maps/arrays matching the **`ConvertedRecipe`** Pydantic model. It is a **standalone** snapshot for that user (ingredients, instructions, nutrition, etc.); it is not assembled from `original_recipes` at read time. Source of truth: `ConvertedRecipe`, `NutritionalInfo`, `ConversionMetadata`, `Ingredient` in `models.py`. Condensed outline:

- `title`, `description`, `servings`
- `ingredients[]` — `name`, `quantity`, `unit`
- `instructions[]` — strings
- `nutritional_info` — `calories`, `protein` (per serving)
- `conversion_metadata` — `original_recipe_url`, `conversion_notes`

**`SavedRecipe`** (Pydantic): maps to the fields above (see `models.py`).

---

**Published recipes and copy flow**

- **Public browse**: List documents where `published == true` (e.g. **collection group** query on `saved_recipes` with `published == true`, ordered by `saved_at` or similar). Requires a composite index when combined with ordering/filters.
- **Detail URL**: Public API identifies a published recipe by **owner user id** + **`savedRecipeId`**, e.g. `GET /api/published-recipes/{ownerUserId}/{savedRecipeId}` (implementations may use an equivalent encoding).
- **Notes**: `notes` are private to the owner. Published recipe views for other users expose **`converted_recipe`** (and metadata needed for the card/detail), not the author’s `notes`.
- **Copy**: When a user saves someone else’s published recipe, the backend creates a **new** `saved_recipes` document for the current user with duplicated `recipe_id` and `converted_recipe`, `published=false`, empty or user-provided `notes`, and sets **`copied_from_user_id`** and **`copied_from_saved_recipe_id`** to the source. **Publishing is disabled** for such copies (enforce in API: if `copied_from_saved_recipe_id` is set, reject publish) to avoid duplicate listings of the same recipe in the published feed.

---

**Recipe ID strategy**: Use `hashlib.sha256(normalized_source_url.encode()).hexdigest()[:32]` for deduplication. Same normalized URL → same `recipe_id` for the **`original_recipes`** document.

**Design note (deduplication)**:

- **`original_recipes`**: One canonical document per normalized source URL. On save from workflow, **create** `original_recipes/{recipe_id}` if missing; otherwise **reuse** (all user saves reference the same `recipe_id`).
- **Per-user variation** (meal prep output, notes, publish flag): lives on **`users/{userId}/saved_recipes`**, especially **`converted_recipe`**, **`notes`**, and **`published`**.

### 2.2 Firestore Security Rules

- [x] **`original_recipes`**: Deny client reads and writes (backend only via Admin SDK). Not intended for direct client access.
- [x] **`users/{userId}/saved_recipes`**: Owner read/write when `request.auth.uid == userId`. Public reads of **published** rows are typically served **only through the backend** (Admin SDK) so rules can remain owner-only; alternatively add guarded rules if you later allow limited client reads.

Rules live in repo root [`firestore.rules`](firestore.rules); [`firebase.json`](firebase.json) wires rules and [`firestore.indexes.json`](firestore.indexes.json). Deploy to each Firebase project (staging/production) with Firebase CLI: `firebase deploy --only firestore` (from repo root, with CLI logged into the correct project). Composite index for published list queries is defined in `firestore.indexes.json`.

*Note: If all Firestore access goes through the backend, rules can be restrictive; backend uses Admin SDK.*

### 2.3 Backend: Recipe & Collection APIs

- [x] **GET /api/published-recipes** — List published saves (paginated). Public. Backed by collection group (or equivalent) on `saved_recipes` where `published == true`.
- [x] **GET /api/published-recipes/{ownerUserId}/{savedRecipeId}** — Single published recipe by owner uid + saved recipe doc id. Public. Returns data appropriate for non-owners (no author `notes`).
- [x] **PUT /api/original-recipes/{recipeId}** — Upsert **`original_recipes`** (auth). Same as internal service for workflow/dev; `GET /api/original-recipes/{recipeId}` reads canonical doc.
- [x] **GET /api/users/me/saved-recipes** — List current user's saved recipes (includes `notes`, `published`, provenance fields). Auth required.
- [x] **GET /api/users/me/saved-recipes/{savedRecipeId}** — Single saved recipe for the current user. Auth required.
- [x] **POST /api/users/me/saved-recipes** — Create save. Body: `{ recipe_id, notes?, converted_recipe?, published? }` (workflow fills `converted_recipe` in Phase 2.5). For **copy-from-published**, include `source_owner_user_id` + `source_saved_recipe_id`; backend sets `copied_from_*` and `published=false`. Auth required.
- [x] **PATCH /api/users/me/saved-recipes/{savedRecipeId}** — Update `notes`, `converted_recipe`, and/or `published` (reject `published: true` if copy provenance forbids it). Auth required.
- [x] **DELETE /api/users/me/saved-recipes/{savedRecipeId}** — Remove from collection. Auth required.

### 2.4 Save Flow Logic

Implementation (backend):

- [x] **`recipe_id`** — [`backend/app/services/recipe_id.py`](backend/app/services/recipe_id.py): `normalize_source_url()`, `compute_recipe_id()` (SHA-256 digest, first 32 hex chars per schema note).
- [x] **Extraction cache** — [`recipe_extraction_workflow(db, url)`](backend/app/services/agents/extraction.py) reads `original_recipes/{recipe_id}` **before** any page fetch / transcript / LLM; on hit returns `OriginalRecipe` via `original_recipe_from_document()` (no API cost).
- [x] **Save orchestration** — [`save_from_workflow()`](backend/app/services/save_flow.py): ensures `original_recipes` exists (create on miss only, no overwrite on hit), then creates `users/{uid}/saved_recipes`. After **Phase 2.5.3**, the primary moment canonical **`original_recipes`** is populated from a **new** extraction is the **generate** workflow (see §2.5.3); user save still uses create-on-miss for edge cases (e.g. save API used without a prior generate).
- [x] **API** — `POST /api/users/me/saved-recipes/from-workflow` (auth): body [`WorkflowSaveCreate`](backend/app/schemas/recipes.py) — `source_url`, `source_type` (`web` | `youtube`), `original_recipe`, optional `converted_recipe`, `notes`, `published`.

When user saves from the AI workflow (Phase 2.5) or creates a save:

1. Compute `recipe_id` from `source_url`.
2. Check if `original_recipes/{recipe_id}` exists. If not, create it from extracted **`OriginalRecipe`** plus metadata into **`OriginalRecipeDocument`** (usually redundant once **generate** persists the canonical doc—see §2.5.3).
3. Create `users/{userId}/saved_recipes` with **`SavedRecipe`** fields: `recipe_id`, `saved_at`, `notes`, optional **`converted_recipe`**, `published` (default false), provenance null unless copying. **Only this step adds the user’s row**; persisting **`original_recipes`** on save is for misses only.

**Persistence split (Phase 2.5):** Running **generate** (§2.5.3) should **write canonical `original_recipes`** whenever extraction runs (after an LLM extraction miss) so extraction cost is not lost and any user can reuse the cache. **User save** (§2.5.4 / `from-workflow`) **only creates `saved_recipes`**—the user-specific snapshot (`converted_recipe`, notes, publish flag). It does not re-store the canonical original except via create-on-miss if the doc is still missing.

When a user **copies a published recipe**:

1. Create a new `saved_recipes` doc for the current user with copied `recipe_id` and **`converted_recipe`**, `published=false`, `notes` empty or user-supplied, and **`copied_from_user_id` / `copied_from_saved_recipe_id`** set. Do not allow publishing this doc.

**Deliverable**: Schema and API plan aligned: internal **`original_recipes`**, user **`saved_recipes`** with **`ConvertedRecipe`** snapshots, **published** discovery, and copy semantics. All via backend API.

**Phase 2.5 handoff:** [`run_workflow()`](backend/app/services/agents/workflow.py) — extract via `recipe_extraction_workflow`, [`ensure_canonical_original_recipe()`](backend/app/services/save_flow.py) on cache miss, then [`convert_recipe()`](backend/app/services/agents/conversion.py) → **`ConvertedRecipe`**. **`POST /api/workflow/generate`** ([`routes/workflow.py`](backend/app/routes/workflow.py)). Persist user library: **`POST /api/users/me/saved-recipes/from-workflow`** ([`saved_recipes.py`](backend/app/routes/saved_recipes.py)). **Remaining before production UX:** Phase 3 subscription gating on generate; frontend wiring to **`generate`** + **`from-workflow`** as needed.

---

## Phase 2.5: Complete AI Workflow

**Goal**: Finish the full AI workflow—extraction (web + YouTube) and conversion to meal prep parameters. This phase must be complete before Phase 3, which gates the workflow behind subscriptions.

### 2.5.1 Complete Web Extraction

- [x] Implement `extract_recipe_from_web_page()` in `extraction.py`.
- [x] Add system instructions for web page extraction (similar to `SYSTEM_INSTRUCTIONS_YOUTUBE`).
- [x] Use OpenAI structured output with `OriginalRecipe` schema.
- [x] Test with various recipe website formats.

### 2.5.2 Build Conversion Agent

- [x] Create conversion agent/service that takes `OriginalRecipe` + `UserAdjustments` → `ConvertedRecipe`.
- [x] Conversion logic: adjust ingredient quantities for target servings; use AI to estimate/calculate nutritional info (calories, protein) and apply user targets.
- [x] Output conforms to `ConvertedRecipe` model (nutritional_info, conversion_metadata).

### 2.5.3 Wire Full Workflow

- [x] Update `run_workflow()` in `workflow.py` to accept `UserRequest` (recipe_url + user_adjustments).
- [x] Flow: extract → **if extraction was a cache miss**, upsert canonical **`original_recipes/{recipe_id}`** (`OriginalRecipeDocument`, create on miss only, no overwrite on hit—same semantics as [`save_from_workflow`](backend/app/services/save_flow.py)) so LLM extraction cost is retained and the recipe is reusable for everyone → convert → return `ConvertedRecipe`. On **cache hit**, skip fetch/LLM and **do not** require a new write (doc already exists).
- [x] `POST /api/workflow/generate` (and `run_workflow`) **does not** create or update **`users/{uid}/saved_recipes`**—only **`original_recipes`** when persisting a new extraction as above.
- [x] Fix current bug: `recipe_extraction_workflow(UserRequest.recipe_url)` should use `user_request.recipe_url`.
- [x] Create/update API endpoint: `POST /api/workflow/generate` — accepts URL + adjustments, returns `ConvertedRecipe`.

### 2.5.4 Save Flow for Converted Recipes

- [x] **`original_recipes`** after generate: handled in §2.5.3 (canonical doc when extraction runs). **User save** does not need to re-upsert unless the doc is still missing (create-on-miss in [`save_from_workflow`](backend/app/services/save_flow.py)).
- [x] When the user saves from the AI workflow result: **only** create/update **`users/{uid}/saved_recipes`** — store **`ConvertedRecipe`** as **`converted_recipe`**, plus `notes`, `published`, etc., so the user retains their portion-adjusted snapshot. **No duplicate canonical original write** when the doc already exists from generate. **API:** [`POST /api/users/me/saved-recipes/from-workflow`](backend/app/routes/saved_recipes.py) with [`WorkflowSaveCreate`](backend/app/schemas/recipes.py) (auth).

**Deliverable**: End-to-end AI workflow: user submits URL + meal prep params → receives converted recipe. Ready to be gated in Phase 3.

---

## Phase 3: Subscriptions & Gating

**Goal**: Stripe subscriptions (monthly/annual) with 14-day trial. Backend checks subscription status before allowing AI workflow.

### 3.1 Stripe Setup

- [x] Create Stripe account. Create products: Monthly Plan, Annual Plan (Stripe Dashboard).
- [x] Apply **14-day trial** when creating the Checkout Session (`subscription_data.trial_period_days: 14`) — implemented in `POST /api/subscription/checkout`.
- [ ] Store Stripe secret key and webhook secret in **GCP Secret Manager** (staging/production); local dev uses `backend/.env` only.
- [ ] Deployed environments: Stripe **test mode** keys for staging, **live mode** for production.

*Reference:* [API keys](https://docs.stripe.com/keys), [webhook signatures](https://docs.stripe.com/webhooks/signatures). Env var names: `backend/.env.example`.

### 3.2 Subscription Status Storage

- [x] Implement Firestore persistence for subscription state (read by gating; written from webhooks): document `users/{userId}/subscription/default` plus index `stripe_customers/{stripeCustomerId}` → `uid`. Fields:

```
subscription (document fields):
  - stripe_customer_id: string
  - stripe_subscription_id: string | null
  - status: "active" | "trialing" | "past_due" | "canceled" | "none"
  - plan: "monthly" | "annual" | null
  - current_period_end: timestamp | null
  - trial_end: timestamp | null
```

Implementation: [`backend/app/services/firestore/subscription.py`](backend/app/services/firestore/subscription.py), [`backend/app/schemas/subscription.py`](backend/app/schemas/subscription.py).

### 3.3 Backend: Stripe Integration

- [x] Add `stripe` to backend dependencies (`pyproject.toml`).
- [x] **POST /api/subscription/checkout** — Create Stripe Checkout session; returns `{ "url" }`. Auth required (`get_current_uid`).
- [x] **POST /api/subscription/portal** — Create Stripe Customer Portal session; returns `{ "url" }`. Auth required.
- [x] **POST /api/webhooks/stripe** — Verify signature; dispatch events; **persist subscription + customer→uid mapping** (see `stripe_webhook_handlers.py`).
- [x] Create `require_subscription` dependency: checks `users/{uid}/subscription` for `active` or `trialing`. Raise 403 if not.
- [x] Gate **`POST /api/workflow/generate`** with `require_subscription`.

### 3.4 Trial Logic

- [x] When user starts trial: Create Stripe Checkout with `subscription_data.trial_period_days: 14`.
- [x] Webhook handlers persist `status` and `trial_end` from Stripe Subscription objects.
- [x] `require_subscription` allows access when `status in ["active", "trialing"]`.
- [x] After trial ends without payment: Stripe moves subscription status; backend reflects via webhooks; `require_subscription` denies when not `active`/`trialing`.

### 3.5 AI Workflow Gating

- [x] **`POST /api/workflow/generate`** requires `require_subscription` (and thus auth).
- [x] Return clear error: 403 with `detail.code` **`subscription_required`** when user lacks access.
- [x] Free users can still call **`GET /api/published-recipes`**, save copies, etc. (unchanged routes).

**Deliverable**: Free users browse and save. Trial/subscribers access the full AI workflow (extraction + conversion). Stripe handles billing and trials.

---

## Phase 4: Frontend & User Experience

**Goal**: Polished UI for auth, dashboard, recipe browsing, AI workflow, and subscription management.

### 4.1 Pages & Routes

- [ ] **/** — Landing page. CTA to sign up or sign in.
- [ ] **/sign-in**, **/sign-up** — Auth pages.
- [ ] **/dashboard** — User's saved recipes. Auth required.
- [ ] **/recipes** — Browse **published** recipes (from `GET /api/published-recipes`). Pagination, search (if implemented).
- [ ] **/recipes/[ownerUserId]/[savedRecipeId]** — Published recipe detail (or equivalent id scheme matching the API). Show "Save to collection" if logged in (creates a **copy** with provenance). Show **notes** only when viewing **your own** saved recipe (e.g. from dashboard), not when viewing another user's published recipe.
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

- **Auth (Phase 1)**: Firebase ID tokens — `get_current_user` / `get_current_user_optional` in `app/dependencies.py` verify Bearer tokens via Admin SDK; CORS and frontend API client are wired.
- **Config**: Firebase project + service account paths and related settings in `app/config.py` (see `backend/.env.example`). Stripe env vars are defined in `Settings` (§3.1), including Checkout/Portal redirect URLs.
- **Subscriptions (Phase 3)**: `POST /api/subscription/checkout`, `/portal`; `POST /api/webhooks/stripe`; Firestore `users/{uid}/subscription/default` + `stripe_customers/{customerId}`; `require_subscription` on `POST /api/workflow/generate`.
- **Workflow**: [`run_workflow()`](backend/app/services/agents/workflow.py) calls `recipe_extraction_workflow()` (cache read + extract), [`ensure_canonical_original_recipe()`](backend/app/services/save_flow.py) on miss, then **`convert_recipe()`** → **`ConvertedRecipe`**. **`POST /api/workflow/generate`** in [`routes/workflow.py`](backend/app/routes/workflow.py). **Save after workflow:** **`POST /api/users/me/saved-recipes/from-workflow`** with optional **`converted_recipe`** — [`save_from_workflow()`](backend/app/services/save_flow.py) ensures **`original_recipes`** create-on-miss only, then new **`saved_recipes`** row (§2.5.4).
- **Models**: `UserRequest`, `UserAdjustments`, `OriginalRecipe`, **`OriginalRecipeDocument`**, `ConvertedRecipe`, **`SavedRecipe`**, etc. in `app/services/agents/models.py`. Extraction uses **`OriginalRecipe`** only; Firestore persistence uses **`OriginalRecipeDocument`** (canonical, shared) and **`SavedRecipe`** (per-user). Conversion agent consumes **`OriginalRecipe`** + **`UserRequest`** and outputs **`ConvertedRecipe`**.

### B. Firestore Indexes

You may need composite indexes for queries (e.g. **collection group** `saved_recipes` with `published == true` and ordering, `original_recipes` by `created_at`, per-user `saved_recipes` by `saved_at`). Firestore will prompt when you run a query that requires an index.

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
- `stripe` (added — Phase 3 webhook)
- `google-cloud-firestore` (or use firebase-admin's Firestore)

**Frontend**:
- `firebase`
- `stripe` (for Checkout redirects; no secret keys on frontend)

---

*Document version: 1.8*
