"""Research tools with Tavily web search and context offloading.

Searches the web via Tavily, fetches full page content, summarizes it
with a local LLM, and saves raw content to the virtual file system.
Only minimal summaries are returned to the agent's message stream.
"""

import os
import uuid
from datetime import datetime
from typing import Annotated, Literal

import httpx
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import InjectedToolArg, InjectedToolCallId, tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from markdownify import markdownify
from pydantic import BaseModel, Field
from tavily import TavilyClient

from src.prompts import SUMMARIZE_WEB_SEARCH
from src.state import DeepAgentState

_summarization_model: ChatOllama | None = None
_tavily_client: TavilyClient | None = None


def _get_summarization_model() -> ChatOllama:
    global _summarization_model
    if _summarization_model is None:
        _summarization_model = ChatOllama(
            model="gemma4:e4b", temperature=0
        )
    return _summarization_model


def _get_tavily_client() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient()
    return _tavily_client


class Summary(BaseModel):
    filename: str = Field(description="Name of the file to store.")
    summary: str = Field(description="Key learnings from the webpage.")


def get_today_str() -> str:
    return datetime.now().strftime("%a %b %-d, %Y")


def run_tavily_search(
    search_query: str,
    max_results: int = 1,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = True,
) -> dict:
    return _get_tavily_client().search(
        query=search_query,
        max_results=max_results,
        topic=topic,
        include_raw_content=include_raw_content,
    )


def summarize_webpage_content(webpage_content: str) -> Summary:
    try:
        structured_model = _get_summarization_model().with_structured_output(
            Summary
        )
        return structured_model.invoke(
            [
                HumanMessage(
                    content=SUMMARIZE_WEB_SEARCH.format(
                        webpage_content=webpage_content, date=get_today_str()
                    )
                )
            ]
        )
    except Exception:
        truncated = (
            webpage_content[:1000] + "..."
            if len(webpage_content) > 1000
            else webpage_content
        )
        return Summary(filename="search_result.md", summary=truncated)


def process_search_results(results: dict) -> list[dict]:
    processed = []
    client = httpx.Client(timeout=30.0)

    for result in results.get("results", []):
        url = result.get("url", "")
        title = result.get("title", "")

        try:
            response = client.get(url)
            if response.status_code == 200:
                raw_content = markdownify(response.text)
                summary_result = summarize_webpage_content(raw_content)
            else:
                raw_content = result.get("raw_content") or result.get("content", "")
                summary_result = Summary(
                    filename="URL_error.md",
                    summary=result.get("content", "Error reading URL"),
                )
        except (httpx.TimeoutException, httpx.RequestError):
            raw_content = result.get("raw_content") or result.get("content", "")
            summary_result = Summary(
                filename="connection_error.md",
                summary=result.get("content", "Error connecting to URL"),
            )

        uid = uuid.uuid4().hex[:8]
        name, ext = os.path.splitext(summary_result.filename)
        filename = f"{name}_{uid}{ext}"

        processed.append(
            {
                "url": url,
                "title": title,
                "summary": summary_result.summary,
                "filename": filename,
                "raw_content": raw_content,
            }
        )

    client.close()
    return processed


@tool(parse_docstring=True)
def tavily_search(
    query: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> Command:
    """Search web and save detailed results to files while returning minimal context.

    Args:
        query: Search query string to look up on the web.
        state: Agent state containing virtual filesystem (injected).
        tool_call_id: Tool call identifier for message response (injected).
        max_results: Maximum number of search results to return.
        topic: Search topic category — general, news, or finance.
    """
    search_results = run_tavily_search(
        query, max_results, topic, include_raw_content=True
    )
    processed = process_search_results(search_results)

    files = dict(state.get("files", {}))
    today = get_today_str()

    for result in processed:
        file_content = (
            f"# {result['title']}\n\n"
            f"**URL:** {result['url']}\n"
            f"**Query:** {query}\n"
            f"**Date:** {today}\n\n"
            f"## Summary\n{result['summary']}\n\n"
            f"## Raw Content\n{result['raw_content']}"
        )
        files[result["filename"]] = file_content

    summary_lines = [f"Found {len(processed)} result(s):\n"]
    for result in processed:
        summary_lines.append(f"- **{result['filename']}**: {result['summary']}")
    summary_lines.append(
        "\nUse read_file() to access full content of any result."
    )
    summary_text = "\n".join(summary_lines)

    return Command(
        update={
            "files": files,
            "messages": [ToolMessage(summary_text, tool_call_id=tool_call_id)],
        }
    )
