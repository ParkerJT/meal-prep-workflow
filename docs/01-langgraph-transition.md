# 01 — LangGraph transition

Goal: orchestrate **recipe generation** (`POST /api/workflow/generate`) with **LangGraph** instead of a single linear Python function, without changing product behavior until you deliberately add new branches.

**Next doc after this:** [02 — Generate input expansion](./02-generate-input-expansion.md) (multi-input routes fit naturally as graph branches).

---

## Prerequisites (learning)

Skim official LangGraph docs until these are clear:

- **State** — one shared object (e.g. `TypedDict` or Pydantic) passed through the run.
- **Nodes** — functions that read state and return **partial** state updates.
- **Edges** — linear `add_edge` vs **conditional** routing after a node.
- **`compile()`** and how you invoke the graph from FastAPI (sync vs async: match your route style).

You do **not** need persistence, streaming, or subgraphs on day one.

---

## Implementation sequence

### 1. Dependencies and config

- Add `langgraph` (and whatever LangChain packages you use for chat models / structured output, aligned with current LangGraph docs).
- Keep API keys and default model IDs in **`Settings`** / env (e.g. `backend/.env.example`). Plan for **multiple** model profiles later (text vs vision) even if you only wire one profile now.

### 2. Model abstraction (parallel track)

- Introduce a small **factory or registry** (“default chat”, “structured extract”, later “vision”) so nodes do not import `OpenAI()` directly everywhere. This is what makes “swap provider/model” real, independent of LangGraph.

### 3. Define workflow state

- Decide fields you need end-to-end, for example: `user_request` (or equivalent), `original_recipe`, `converted_recipe`, optional `error` / `retry_count`, and later `input_mode` for **02**.
- Pick **TypedDict** or **Pydantic** for `State` and stick with it for the graph.

### 4. First milestone — lift-and-shift linear graph

- Replace the body of `run_workflow` with: **compile once** (module level or app lifespan) or build per request if you inject clients per request.
- **Nodes** (minimal split):
  1. **Extract** — call existing `recipe_extraction_workflow(db, url)` (same signature as today).
  2. **Persist canonical** — `ensure_canonical_original_recipe(...)` with the same arguments as today.
  3. **Convert** — `convert_recipe(original_recipe, user_request, client)` → `ConvertedRecipe`.
- **Edges:** `START → extract → persist → convert → END`.
- Route handler (`routes/workflow.py`) still parses `UserRequest` and returns **`ConvertedRecipe`**; it only calls “run compiled graph” instead of `run_workflow` if you rename internally.

**Exit criteria:** Same request/response as before; tests or manual smoke pass.

### 5. Second milestone — hooks for 02 and quality

- Add **conditional routing** stub (e.g. always `"url"` until **02** ships).
- Add a **validation** node after extract (or after convert) with a conditional edge: pass → continue, fail → retry extract or return structured error (your product rule).
- Optionally add **LangSmith** tracing if you want portfolio-visible observability.

### 6. Cleanup

- Remove dead imperative code paths once the graph is authoritative.
- Document the node list and edges in `docs/README.md` or a short comment block at the graph definition file so **02** is easy to extend.

---

## Files likely to change

- `backend/app/services/agents/workflow.py` — graph definition and/or thin `run_workflow` wrapper.
- `backend/app/routes/workflow.py` — unchanged contract; may call renamed entrypoint.
- `backend/pyproject.toml` — new dependencies.
- Later: `extraction.py` / `conversion.py` stay as **capabilities** called from nodes; **02** extends extraction branches.

---

## Pitfalls to avoid

- **Do not** fold Firestore or HTTP concerns *inside* LLM nodes more than necessary; keep I/O at the edges of nodes for testability.
- **Do not** block the event loop: if the app goes async, use async nodes or `run_in_executor` as appropriate.
- Prefer **one graph module** plus small pure helpers over scattering graph construction across the package.

When this milestone is done, open [02 — Generate input expansion](./02-generate-input-expansion.md) and map each checklist section to new nodes or edges.
