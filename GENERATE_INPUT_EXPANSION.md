# Generate recipe — multi-input & personal instructions

Implementation guide for extending **Generate recipe** so users can supply a **URL**, **pasted text**, or an **image**; optional **per-generation personal instructions**; and optional **account-level global instructions** that apply to every generation unless superseded by the per-run field. Use this document as the checklist while changing backend, workflow, and frontend.

**Related:** [`BUILD_PLAN.md`](BUILD_PLAN.md) (Phase 2.5 workflow), canonical `original_recipes` / user `saved_recipes`.

---

## 1. Goals

| Feature | Description |
|--------|-------------|
| **Input modes** | Exactly one of: recipe URL (existing), pasted plain text, or uploaded image (screenshot/photo of a recipe). |
| **Personal instructions (per generation)** | Optional short text applied during conversion for **this run only**—e.g. swap one ingredient, tweak for tonight—**not** the same as library “save notes.” |
| **Global instructions (account)** | Optional text stored on the user profile and **automatically included on every generate** (e.g. “I’m vegetarian—adapt all recipes accordingly”). Users avoid retyping standing preferences. |
| **Caching** | **`original_recipes` read-through cache applies only to URL extractions.** Text and image inputs **never** use cache lookup or cross-request reuse; treat every run as a fresh extraction. |

---

## 2. Caching & persistence (critical)

### 2.1 URL (unchanged behavior)

- Normalize URL → `recipe_id` → if `original_recipes/{recipe_id}` exists, return cached `OriginalRecipe` and **skip** fetch + extraction LLM.
- On cache miss, extract, then `ensure_canonical_original_recipe(...)` (create on miss only).

### 2.2 Pasted text & image (no cache reuse)

- **Do not** call `get_original_recipe` for deduplication; **always** run the text or vision extraction path.
- **Persistence after a successful generate:** You still need a stable **`source_url` (or agreed key)** so:
  - `ensure_canonical_original_recipe` can store the canonical original if you keep that pattern, and
  - `POST /api/users/me/saved-recipes/from-generate` can resolve `original_recipe_id` from the same key the generate run used (see [`saved_recipes.py`](backend/app/routes/saved_recipes.py) `GeneratedSaveCreate` + 409 when canonical doc missing).

**Recommended approach:**

1. On each **text** or **image** generate, generate a **one-time synthetic identifier** (e.g. UUID) and form a stable pseudo-URL such as `text://{uuid}` or `image://{uuid}` (pick one scheme and document it).
2. Use that value everywhere this flow needs `source_url`: `ensure_canonical_original_recipe`, `convert_recipe` metadata patching, and **return it in the generate response** so the client can send it back unchanged on **save**.
3. Do **not** attempt to hash content for cache keys; duplicates are assumed rare.

**Save UX:** The frontend must **not** rely on the URL field for non-URL modes. After generate, use **`source_url` returned by the API** when calling `from-generate`.

---

## 3. Account-level global instructions

### 3.1 Behavior

- **Stored per user** (Firestore under `users/{uid}`, e.g. a dedicated field or a small `preferences` / `generation_settings` map—pick one pattern and stay consistent with existing [`users` ... `subscription`](backend/app/services/firestore/subscription.py) layout).
- **Loaded server-side on each `POST /api/workflow/generate`** (after auth): read global instructions for the current uid and pass them into conversion alongside any **per-generation** `personal_instructions`.
- **Merge semantics for the LLM:** Send two labeled blocks so the model can reconcile them, for example:
  - **Standing account preferences** (global)—always apply when non-empty.
  - **Additional instructions for this recipe only** (per-run)—optional.
- **Conflict resolution:** Document in the conversion prompt that **per-generation instructions take precedence** when they contradict global ones (e.g. global says “vegetarian” but this run says “use chicken for this recipe only”—the run wins). Optional product rule: if you prefer global to always win, state that instead—pick one and encode it in `SYSTEM_INSTRUCTIONS_CONVERSION`.
- **Empty state:** If the user clears global instructions, treat as absent (no DB row / empty string).

### 3.2 API surface (account settings)

Add authenticated endpoints (names illustrative):

| Method | Path (example) | Purpose |
|--------|----------------|---------|
| `GET` | `/api/users/me/generation-preferences` | Return `{ global_instructions: string }` (or nested object if you add more keys later). |
| `PATCH` | `/api/users/me/generation-preferences` | Update global instructions; validate max length server-side. |

**Alternative:** Fold into an existing **Settings** user-profile route if you add one later; avoid scattering profile fields across many routes without a plan.

### 3.3 Limits & product notes

- Use a **max length** similar to or slightly larger than per-generation instructions (global text may be a short paragraph).
- **Medical/allergy claims:** Consider a short UI disclaimer that the AI is not a substitute for professional dietary advice; global instructions are still user-authored prompts.

### 3.4 Backend checklist (global instructions)

- Firestore read/write helper for the chosen field(s) on `users/{uid}`.
- Pydantic schemas for GET/PATCH payloads.
- **`generate` route:** inject `Depends(get_current_uid)` (see [`dependencies.py`](backend/app/dependencies.py)), load global instructions, pass into `run_workflow(...)` or a wrapper that merges before `convert_recipe`.
- **`run_workflow` / `convert_recipe`:** Accept optional `global_instructions: str | None` (or bundle both strings into a small struct) and extend the conversion user prompt + system instructions per §5.4.

### 3.5 Frontend checklist (global instructions)

- **Settings** (or dedicated section): textarea for global instructions, save button, load on mount, character limit hint.
- **Generate page:** Optional read-only summary (“Your account preferences will apply”) or link to Settings—avoid duplicating the full global text on generate unless useful for transparency.

---

## 4. API design (generate request & response)

### 4.1 Two shapes to choose from (pick one in implementation)

| Approach | Pros | Cons |
|----------|------|------|
| **A. Single multipart endpoint** | One route; image + fields in one request | Client must use `Form`/`multipart` for all modes or branch |
| **B. Split routes** | JSON stays simple for URL + text; separate route for image upload | Two code paths to maintain |

**Minimum fields (conceptual):**

- `input_mode`: `"url" | "text" | "image"`
- `recipe_url` (when `url`)
- `recipe_text` (when `text`) — cap length (align with extraction limits, e.g. on the order of `WEB_PAGE_TEXT_MAX_CHARS` in [`extraction.py`](backend/app/services/agents/extraction.py))
- `image` file (when `image`) — max size, allowed MIME types (`image/jpeg`, `image/png`, `image/webp`, etc.)
- `user_adjustments` — existing [`UserAdjustments`](backend/app/services/agents/models.py)
- `personal_instructions` (optional) — new; short max length (e.g. 500–1000 chars—tune to product)

**Validation:** Exactly one of URL / text / image payload present; reject ambiguous combinations.

**Response:** Extend generate response to include at least:

- `ConvertedRecipe` (as today)
- `source_url` — **authoritative** string to send to `from-generate` (always; for URL mode it can echo the normalized URL you keyed on)

This removes ambiguity for the client when mode ≠ URL.

---

## 5. Backend modules (checklist)

### 5.1 Models — [`backend/app/services/agents/models.py`](backend/app/services/agents/models.py)

- Extend or replace `UserRequest`:
  - Discriminated input (mode + optional fields), **or** optional fields with a `@model_validator` enforcing exclusivity.
- Add optional `personal_instructions: str | None = None` (or similar name—avoid clashing with `SavedRecipe.notes`).
- Consider keeping `UserAdjustments` as-is (macros + servings).

### 5.2 Extraction — [`backend/app/services/agents/extraction.py`](backend/app/services/agents/extraction.py)

- **`recipe_extraction_workflow`**: Refactor so URL path keeps current behavior (cache **only** here for URLs).
- Add **`extract_recipe_from_pasted_text(text, client)`** (or reuse `extract_recipe_from_web_page` with a system prompt tuned for “user pasted recipe text” if that is cleaner—same structured output `OriginalRecipe`).
- Add **`extract_recipe_from_image(bytes | path, client)`** using a **vision-capable** model; structured output to `OriginalRecipe`. Define image preprocessing if needed (resize, max pixels) before API call.
- New env var(s) if vision uses a different model than `OPENAI_MODEL` (optional but common).

### 5.3 Workflow — [`backend/app/services/agents/workflow.py`](backend/app/services/agents/workflow.py)

- Branch on input mode:
  - **URL:** `recipe_extraction_workflow(db, url)` (cache applies inside).
  - **Text / image:** call new extraction helpers; **no** cache read; build synthetic `source_url`; then `ensure_canonical_original_recipe` with that key (still “create on miss”; first write wins per UUID).
- Pass full `UserRequest` into `convert_recipe`.

### 5.4 Conversion — [`backend/app/services/agents/conversion.py`](backend/app/services/agents/conversion.py)

- Include **`global_instructions`** (from account) and **`personal_instructions`** (from request) in the user message when present; label them distinctly (see §3.1).
- Update `SYSTEM_INSTRUCTIONS_CONVERSION` so the model must:
  - Honor standing account preferences and per-run instructions with the **conflict rule** you chose in §3.1.
  - Honor substitutions/preferences **without** breaking food-safety sanity.
  - Still scale servings and aim for macro targets.
  - Reflect what it did in `conversion_metadata.conversion_notes`.
- Keep setting `original_recipe_url` from the authoritative `source_url` on the request (for URL it stays a real URL; for others it is the synthetic key).

### 5.5 Routes — [`backend/app/routes/workflow.py`](backend/app/routes/workflow.py)

- Accept new body shape and/or multipart.
- Subscription gate unchanged (`require_subscription`).
- Inject uid; load **global instructions** for generate (see §3).
- Return extended response (see §4).

### 5.6 Save — [`backend/app/routes/saved_recipes.py`](backend/app/routes/saved_recipes.py) & schemas — [`backend/app/schemas/recipes.py`](backend/app/schemas/recipes.py)

- **`GeneratedSaveCreate`**: Client should send the **`source_url` returned from generate** (document in OpenAPI/comments).
- No change strictly required if `source_url` remains the join key—only **client contract** and validation messaging.

### 5.7 Optional: OpenAPI / types

- Export response type `GenerateWorkflowResponse` with `converted_recipe` + `source_url`.

---

## 6. Frontend — [`frontend/src/app/generate/page.tsx`](frontend/src/app/generate/page.tsx)

- UI to choose **one** input mode (tabs, radio group, or segmented control).
- Fields: URL input | textarea | file input + preview.
- **Personal instructions:** short textarea or input with character hint/max.
- Submit:
  - URL + text: JSON `fetch` (or `FormData` if unified endpoint).
  - Image: `FormData` with file + adjustments + instructions.
- Store **`source_url` from generate response** in state; use it for `from-generate` instead of `recipeUrl.trim()` when in text/image mode (and prefer server value for URL mode too for consistency).
- Copy/types: extend [`WorkflowRequest`](frontend/src/app/generate/page.tsx) / shared types in [`frontend/src/lib/frontend-types`](frontend/src/lib) if applicable.
- **Global instructions UI:** implement per §3.5 (Settings or equivalent); not duplicated on generate beyond a short hint/link unless you want full preview.

---

## 7. Limits, safety, cost

| Topic | Guidance |
|-------|----------|
| **Text length** | Cap pasted text; mirror or reuse web extraction truncation strategy. |
| **Image size** | Max upload bytes; reject oversized before vision call; optional downscale. |
| **Personal instructions** | Max length; strip or moderate if you add reporting later. |
| **Global instructions** | Max length on PATCH; same abuse considerations as other user-stored prompt text. |
| **Cost** | Vision calls are usually more expensive—log or metric per mode. |
| **Abuse** | Rate limits already desirable for generate; multipart increases payload size—enforce limits at reverse proxy / FastAPI. |

---

## 8. Testing checklist

- [ ] URL generate: cache hit skips extraction; miss extracts and persists.
- [ ] Text generate: always extracts; never reads URL cache; save works using returned `source_url`.
- [ ] Image generate: same as text for caching behavior; save works.
- [ ] Personal instructions: swaps/reflection appear in converted recipe and/or `conversion_notes`.
- [ ] Global instructions: persist via Settings API; load on generate; combine with per-run instructions per §3.1; conflict behavior matches prompt.
- [ ] Clearing global instructions: generate behaves as if none were set.
- [ ] Validation errors: zero inputs, multiple inputs, oversize text/image.
- [ ] Subscription 403 unchanged.

---

## 9. Documentation follow-ups

- Update [`BUILD_PLAN.md`](BUILD_PLAN.md) Phase 2.5 / product bullets when behavior ships (multi-input + per-run + account-level instructions).
- Optionally add a short **user-facing** FAQ: library “notes” vs “instructions for this generation” vs **standing account preferences**.

---

## 10. Summary

1. **Three mutually exclusive inputs** + optional **per-generation personal instructions** + optional **account-level global instructions** (loaded server-side every time).  
2. **Cache only for URLs**; text/image always extract fresh; use **synthetic `source_url` per run** for persistence and save alignment.  
3. **Return `source_url` from generate** so **from-generate** stays consistent without hashing pasted content or images.  
4. **GET/PATCH preferences** for global instructions; **merge + precedence** documented in the conversion prompt (§3.1).
