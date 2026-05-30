# Documentation roadmap

Use these files **in numeric order**. Each step builds on the previous one.

| Order | Document | Purpose |
|-------|----------|---------|
| **01** | [01-langgraph-transition.md](./01-langgraph-transition.md) | Move recipe generation orchestration to **LangGraph** (linear graph first, then branching and quality gates, pluggable LLMs per node). |
| **02** | [02-generate-input-expansion.md](./02-generate-input-expansion.md) | **Multi-input generate**: URL, pasted text, image; per-run and account-level instructions; caching rules; API and frontend contract. |
| **03** | [03-build-plan.md](./03-build-plan.md) | Full phased **product build plan** (auth, data, subscriptions, UI, deployment, launch prep). |

---

## Suggested journey

1. **LangGraph (01)** — Establish the orchestration layer while behavior stays close to today’s `run_workflow` (extract → persist canonical → convert). Add conditional edges and gates as you learn; introduce a model factory so providers and model IDs are not hard-coded to a single vendor.
2. **Input expansion (02)** — Route by `input_mode` in the graph; add vision-capable extraction for images and text extraction for paste; wire `source_url` return contract and global instructions. Update Phase 2.5 bullets in **03** when shipped.
3. **Launch slice (03)** — Treat Phases **1–4** as largely done unless checkboxes say otherwise. For an **initial public version**, work through:

   - **Phase 5** — GCP projects, Docker + **Cloud Run**, Firebase Hosting for Next.js, Cloud Build triggers, env/secrets wiring.
   - **Phase 3.1** (remaining) — Stripe keys and webhook secret in **GCP Secret Manager** for staging/production; test vs live mode per environment.
   - **Phase 6** — CORS hardening, rate limits on generate, input validation, Terms/Privacy, health checks, error tracking (e.g. Sentry), production Stripe webhook URL, root **README** and `.env.example` polish.

Adjust scope if you want a thinner v1 (e.g. skip custom domain until after first deploy).

---

## Repo layout

- Application code: `backend/`, `frontend/` (unchanged).
- Planning docs: **`docs/`** (this folder).
- Firebase config at repo root: `firebase.json`, `firestore.rules`, `firestore.indexes.json` (linked from **03** where relevant).

If you followed an old bookmark: `BUILD_PLAN.md` and `GENERATE_INPUT_EXPANSION.md` at the repository root now redirect to **`docs/03-build-plan.md`** and **`docs/02-generate-input-expansion.md`**.
