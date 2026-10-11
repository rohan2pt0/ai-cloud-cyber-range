"""SecuRAX autonomous web-research agent — sovereign, read-only, injection-safe."""
from .executor import Action, execute_action
from .researcher import (
    PendingAction,
    ResearchResult,
    Source,
    ddg_search,
    extract_text,
    gateway_llm,
    http_fetch,
    make_render_fetch,
    research,
)

__all__ = [
    "research", "ResearchResult", "Source", "PendingAction",
    "extract_text", "gateway_llm", "http_fetch", "make_render_fetch", "ddg_search",
    "Action", "execute_action",
]
