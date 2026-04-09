"""Tests for M5: Research tools with Tavily search and context offloading.

Unit tests (no LLM, no network) verify tool mechanics via mocking.
Integration test (Ollama + Tavily) verifies agent uses search tools.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from langgraph.types import Command

from src.research_tools import (
    Summary,
    process_search_results,
    summarize_webpage_content,
    tavily_search,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_call(name: str, args: dict, call_id: str = "test-123") -> dict:
    """Build a ToolCall dict for invoking tools with InjectedToolCallId."""
    return {"name": name, "args": args, "type": "tool_call", "id": call_id}


def invoke(agent, prompt: str) -> dict:
    """Run the agent and return final state."""
    return agent.invoke({"messages": [("human", prompt)], "todos": [], "files": {}})


# ---------------------------------------------------------------------------
# Unit tests — summarize_webpage_content
# ---------------------------------------------------------------------------


def test_summarize_webpage_content_fallback():
    """When the LLM fails, summarize_webpage_content returns truncated content."""
    with patch("src.research_tools._get_summarization_model") as mock_getter:
        mock_getter.return_value.with_structured_output.side_effect = Exception(
            "LLM unavailable"
        )

        long_content = "A" * 2000
        result = summarize_webpage_content(long_content)

        assert isinstance(result, Summary)
        assert result.filename == "search_result.md"
        assert len(result.summary) == 1003  # 1000 chars + "..."
        assert result.summary.endswith("...")


def test_summarize_webpage_content_fallback_short():
    """When the LLM fails on short content, returns full content without truncation."""
    with patch("src.research_tools._get_summarization_model") as mock_getter:
        mock_getter.return_value.with_structured_output.side_effect = Exception(
            "LLM unavailable"
        )

        short_content = "Short webpage content"
        result = summarize_webpage_content(short_content)

        assert isinstance(result, Summary)
        assert result.filename == "search_result.md"
        assert result.summary == short_content


# ---------------------------------------------------------------------------
# Unit tests — process_search_results
# ---------------------------------------------------------------------------


@patch("src.research_tools.summarize_webpage_content")
@patch("src.research_tools.httpx.Client")
def test_process_search_results_timeout(mock_client_cls, mock_summarize):
    """When httpx times out, process_search_results uses fallback summary."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("timed out")
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    results = {
        "results": [
            {
                "url": "http://example.com",
                "title": "Test Page",
                "content": "fallback content",
                "raw_content": "",
            }
        ]
    }

    processed = process_search_results(results)

    assert len(processed) == 1
    assert "connection_error" in processed[0]["filename"]
    assert processed[0]["summary"] == "fallback content"
    # summarize_webpage_content should NOT be called on timeout path
    mock_summarize.assert_not_called()


@patch("src.research_tools.summarize_webpage_content")
@patch("src.research_tools.httpx.Client")
def test_filename_uniquification(mock_client_cls, mock_summarize):
    """Two results returning the same filename get unique suffixes."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("timed out")
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    results = {
        "results": [
            {
                "url": "http://example.com/a",
                "title": "Page A",
                "content": "content a",
                "raw_content": "",
            },
            {
                "url": "http://example.com/b",
                "title": "Page B",
                "content": "content b",
                "raw_content": "",
            },
        ]
    }

    processed = process_search_results(results)

    assert len(processed) == 2
    filenames = [r["filename"] for r in processed]
    # Both get connection_error prefix but UUID suffix makes them unique
    assert filenames[0] != filenames[1]
    assert all("connection_error" in f for f in filenames)


# ---------------------------------------------------------------------------
# Unit tests — tavily_search tool
# ---------------------------------------------------------------------------


@patch("src.research_tools.process_search_results")
@patch("src.research_tools.run_tavily_search")
def test_tavily_search_tool_saves_files(mock_run_search, mock_process):
    """tavily_search returns Command with files and ToolMessage."""
    mock_run_search.return_value = {"results": []}
    mock_process.return_value = [
        {
            "url": "http://example.com",
            "title": "Test Result",
            "summary": "A concise summary of the page.",
            "filename": "test_result_abc123.md",
            "raw_content": "Full raw content of the page...",
        }
    ]

    state = {"files": {}, "messages": []}
    result = tavily_search.invoke(
        _tool_call("tavily_search", {"query": "test query", "state": state})
    )

    assert isinstance(result, Command)
    files = result.update["files"]
    assert "test_result_abc123.md" in files
    assert "Full raw content" in files["test_result_abc123.md"]

    messages = result.update["messages"]
    assert len(messages) == 1
    assert messages[0].tool_call_id == "test-123"
    assert "test_result_abc123.md" in messages[0].content


@patch("src.research_tools.process_search_results")
@patch("src.research_tools.run_tavily_search")
def test_tavily_search_tool_minimal_summary(mock_run_search, mock_process):
    """ToolMessage contains summary but NOT the raw content (context offloading)."""
    long_raw = "UNIQUE_RAW_MARKER " * 500
    mock_run_search.return_value = {"results": []}
    mock_process.return_value = [
        {
            "url": "http://example.com",
            "title": "Big Page",
            "summary": "Short summary only.",
            "filename": "big_page_xyz789.md",
            "raw_content": long_raw,
        }
    ]

    state = {"files": {}, "messages": []}
    result = tavily_search.invoke(
        _tool_call("tavily_search", {"query": "big query", "state": state})
    )

    assert isinstance(result, Command)
    tool_msg = result.update["messages"][0].content

    # The ToolMessage should have the summary but NOT the raw content
    assert "Short summary only." in tool_msg
    assert "UNIQUE_RAW_MARKER" not in tool_msg

    # But the files dict DOES have the raw content
    assert "UNIQUE_RAW_MARKER" in result.update["files"]["big_page_xyz789.md"]


# ---------------------------------------------------------------------------
# Integration test — requires Ollama + Tavily API key
# ---------------------------------------------------------------------------


@pytest.fixture
def agent():
    from src.deep_agent import create_deep_agent

    return create_deep_agent()


@pytest.mark.integration
def test_agent_researches_topic(agent):
    """Agent searches the web and saves results to the virtual file system."""
    result = invoke(
        agent,
        "Search the web for 'What is the Model Context Protocol?' "
        "and save your findings.",
    )

    files = result.get("files", {})
    assert len(files) >= 1, "Agent should save at least one search result file"

    messages = result.get("messages", [])
    assert len(messages) >= 2, "Agent should have human message + at least one response"

    # Final message should have content
    last_msg = messages[-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    assert len(content) > 0, "Final message should have content"
