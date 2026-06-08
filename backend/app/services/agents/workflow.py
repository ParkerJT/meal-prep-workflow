"""
LangGraph recipe generation workflow.

Nodes and edges:
  START -> resolve_input -> [prepare_youtube | prepare_web | prepare_text]
        -> extract_recipe_llm -> validate_extraction -> convert_recipe_llm
        -> validate_conversion -> END

Any step may set state.rejection to short-circuit remaining work at invoke time.
"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.services.agents.conversion import convert_recipe
from app.services.agents.errors import WorkflowRejection
from app.services.agents.extraction import (
    extract_recipe_from_pasted_text,
    extract_recipe_from_web_page,
    extract_recipe_from_youtube_video,
    is_youtube_url,
    scrape_web_page,
    scrape_youtube_video,
)
from app.services.agents.llm_factory import get_openai_client
from app.services.agents.models import GenerateResponse, UserRequest
from app.services.agents.validation import (
    validate_conversion_programmatic,
    validate_extraction_programmatic,
    validate_extraction_with_llm,
)
from app.services.agents.workflow_state import ExtractionRoute, WorkflowState
from app.services.recipe_id import normalize_source_url
from app.services.user_text import RECIPE_TEXT_MAX_CHARS

_RAW_SNIPPET_MAX = 4_000


def _rejection(code: str, message: str) -> dict:
    return {"rejection": {"code": code, "message": message}}


def _route_after_step(state: WorkflowState) -> Literal["continue", "reject"]:
    if state.get("rejection"):
        return "reject"
    return "continue"


def _route_to_prepare(state: WorkflowState) -> str:
    route = state.get("extraction_route")
    if route == "youtube":
        return "prepare_youtube"
    if route == "web":
        return "prepare_web"
    return "prepare_text"


def resolve_input_node(state: WorkflowState) -> dict:
    user_request = state["user_request"]
    if user_request.input_mode == "text":
        text = user_request.recipe_text or ""
        if not text:
            return _rejection("invalid_input", "Pasted recipe text is empty.")
        if len(text) > RECIPE_TEXT_MAX_CHARS:
            return _rejection(
                "invalid_input",
                f"Pasted text exceeds the maximum length of {RECIPE_TEXT_MAX_CHARS} characters.",
            )
        return {
            "source_url": f"text://{uuid4()}",
            "source_type": "text",
            "extraction_route": "text",
            "raw_content": text,
        }

    url = (user_request.recipe_url or "").strip()
    if not url.startswith("https://"):
        return _rejection("invalid_input", "Recipe URL must start with https://.")

    normalized = normalize_source_url(url)
    if is_youtube_url(url):
        return {
            "source_url": normalized,
            "source_type": "youtube",
            "extraction_route": "youtube",
        }
    return {
        "source_url": normalized,
        "source_type": "web",
        "extraction_route": "web",
    }


def prepare_youtube_node(state: WorkflowState) -> dict:
    url = state["user_request"].recipe_url or ""
    try:
        video_info = scrape_youtube_video(url)
    except ValueError as exc:
        return _rejection("fetch_failed", str(exc))
    transcript = (video_info.get("transcript") or "").strip()
    if not transcript:
        return _rejection("no_content", "Could not extract a transcript from this YouTube video.")
    return {
        "youtube_meta": video_info,
        "raw_content": transcript,
    }


def prepare_web_node(state: WorkflowState) -> dict:
    url = state["user_request"].recipe_url or ""
    try:
        content = scrape_web_page(url)
    except ValueError as exc:
        message = str(exc)
        code = "no_content" if "no extractable content" in message.lower() else "fetch_failed"
        return _rejection(code, message)
    return {"raw_content": content}


def prepare_text_node(state: WorkflowState) -> dict:
    text = (state.get("raw_content") or "").strip()
    if not text:
        return _rejection("invalid_input", "Pasted recipe text is empty.")
    return {"raw_content": text}


def extract_recipe_llm_node(state: WorkflowState) -> dict:
    client = state["openai_client"]
    route: ExtractionRoute | None = state.get("extraction_route")
    try:
        if route == "youtube":
            meta = state.get("youtube_meta") or {}
            original = extract_recipe_from_youtube_video(
                meta.get("title") or "",
                meta.get("description") or "",
                meta.get("transcript") or "",
                client,
            )
        elif route == "web":
            original = extract_recipe_from_web_page(state.get("raw_content") or "", client)
        elif route == "text":
            original = extract_recipe_from_pasted_text(state.get("raw_content") or "", client)
        else:
            return _rejection("invalid_input", f"Unsupported extraction route: {route}")
    except Exception as exc:
        return _rejection("extraction_incomplete", f"Recipe extraction failed: {exc}")

    if original is None:
        return _rejection("extraction_incomplete", "Recipe extraction returned no result.")
    return {"original_recipe": original}


def validate_extraction_node(state: WorkflowState) -> dict:
    original = state.get("original_recipe")
    if original is None:
        return _rejection("extraction_incomplete", "No extracted recipe to validate.")

    programmatic_error = validate_extraction_programmatic(original)
    if programmatic_error:
        return _rejection("extraction_incomplete", programmatic_error)

    raw = state.get("raw_content") or ""
    snippet = raw[:_RAW_SNIPPET_MAX]
    result = validate_extraction_with_llm(
        raw_content_snippet=snippet,
        original_recipe=original,
        openai_client=state["openai_client"],
    )
    if not result.is_valid_recipe:
        code = result.rejection_code or "not_a_recipe"
        return _rejection(code, result.message)
    return {}


def convert_recipe_llm_node(state: WorkflowState) -> dict:
    original = state.get("original_recipe")
    if original is None:
        return _rejection("extraction_incomplete", "Missing original recipe for conversion.")
    try:
        converted = convert_recipe(
            original,
            state["user_request"],
            state["openai_client"],
            source_url=state.get("source_url"),
            global_instructions=state.get("global_instructions"),
        )
    except Exception as exc:
        return _rejection("conversion_failed", f"Recipe conversion failed: {exc}")
    return {"converted_recipe": converted}


def validate_conversion_node(state: WorkflowState) -> dict:
    converted = state.get("converted_recipe")
    if converted is None:
        return _rejection("conversion_failed", "No converted recipe to validate.")
    error = validate_conversion_programmatic(converted, state["user_request"].user_adjustments)
    if error:
        return _rejection("conversion_failed", error)
    return {}


def _build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("resolve_input", resolve_input_node)
    graph.add_node("prepare_youtube", prepare_youtube_node)
    graph.add_node("prepare_web", prepare_web_node)
    graph.add_node("prepare_text", prepare_text_node)
    graph.add_node("extract_recipe_llm", extract_recipe_llm_node)
    graph.add_node("validate_extraction", validate_extraction_node)
    graph.add_node("convert_recipe_llm", convert_recipe_llm_node)
    graph.add_node("validate_conversion", validate_conversion_node)

    graph.add_edge(START, "resolve_input")

    graph.add_conditional_edges(
        "resolve_input",
        lambda state: "reject" if state.get("rejection") else _route_to_prepare(state),
        {
            "reject": END,
            "prepare_youtube": "prepare_youtube",
            "prepare_web": "prepare_web",
            "prepare_text": "prepare_text",
        },
    )

    for prepare_node in ("prepare_youtube", "prepare_web", "prepare_text"):
        graph.add_conditional_edges(
            prepare_node,
            _route_after_step,
            {"continue": "extract_recipe_llm", "reject": END},
        )

    graph.add_conditional_edges(
        "extract_recipe_llm",
        _route_after_step,
        {"continue": "validate_extraction", "reject": END},
    )

    graph.add_conditional_edges(
        "validate_extraction",
        _route_after_step,
        {"continue": "convert_recipe_llm", "reject": END},
    )

    graph.add_conditional_edges(
        "convert_recipe_llm",
        _route_after_step,
        {"continue": "validate_conversion", "reject": END},
    )

    graph.add_edge("validate_conversion", END)
    return graph.compile()


_compiled_graph = _build_graph()


def run_workflow(
    user_request: UserRequest,
    *,
    global_instructions: str | None = None,
) -> GenerateResponse:
    initial_state: WorkflowState = {
        "user_request": user_request,
        "openai_client": get_openai_client(),
        "global_instructions": global_instructions,
    }
    final = _compiled_graph.invoke(initial_state)

    rejection = final.get("rejection")
    if rejection:
        raise WorkflowRejection(rejection["code"], rejection["message"])

    original = final.get("original_recipe")
    converted = final.get("converted_recipe")
    source_type = final.get("source_type")
    if original is None or converted is None or source_type is None:
        raise WorkflowRejection("conversion_failed", "Workflow finished without a complete recipe.")

    return GenerateResponse(
        original_recipe=original,
        converted_recipe=converted,
        source_url=final.get("source_url"),
        source_type=source_type,
    )
