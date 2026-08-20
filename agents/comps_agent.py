"""
Comps Agent -- comparable-title outcome intelligence.

Same MCP wiring pattern as exposure_agent.py, pointed at the same ClickHouse
cluster but reasoning over reelledger.comparable_titles instead of spend data.
Kept as a separate agent (rather than folding into exposure_agent) so each
agent has a narrow, auditable responsibility and a focused system prompt --
that separation is also what makes this a genuine multi-agent system rather
than one agent with two prompts glued together.
"""
import os
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioServerParameters

from agents.prompts import COMPS_AGENT_INSTRUCTION

MODEL = os.getenv("REELLEDGER_MODEL", "gemini-2.5-flash")


def _clickhouse_mcp_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioServerParameters(
            command=sys.executable,
            args=["-c", "from mcp_clickhouse.main import main; main()"],
            env={
                "CLICKHOUSE_HOST": os.environ["CLICKHOUSE_HOST"],
                "CLICKHOUSE_PORT": os.environ.get("CLICKHOUSE_PORT", "8443"),
                "CLICKHOUSE_USER": os.environ.get("CLICKHOUSE_USER", "default"),
                "CLICKHOUSE_PASSWORD": os.environ.get("CLICKHOUSE_PASSWORD", ""),
                "CLICKHOUSE_SECURE": os.environ.get("CLICKHOUSE_SECURE", "true"),
                "CLICKHOUSE_DATABASE": os.environ.get("CLICKHOUSE_DATABASE", "reelledger"),
            },
        ),
        tool_filter=["run_query", "list_tables", "list_databases"],
    )


def build_comps_agent() -> LlmAgent:
    return LlmAgent(
        name="comps_agent",
        model=MODEL,
        description=(
            "Answers questions about how comparable historical titles performed, "
            "given genre, budget tier, cast tier, and release window, using live "
            "ClickHouse data."
        ),
        instruction=COMPS_AGENT_INSTRUCTION,
        tools=[_clickhouse_mcp_toolset()],
    )
