"""
Exposure Agent -- watches production spend vs. budget in real time.

Built with Google ADK's LlmAgent + MCPToolset, pointed at the official
ClickHouse MCP server (mcp-clickhouse: https://github.com/ClickHouse/mcp-clickhouse).
This is the piece that satisfies the contest's "ClickHouse used at runtime,
not just referenced" requirement -- the MCP connection is instantiated and
handed to the agent as real, callable tools.

NOTE ON ADK API SURFACE: google-adk's exact class names/kwargs for
MCPToolset and StdioServerParameters have moved between versions. Before
your first real run, check `python -c "import google.adk; help(google.adk)"`
or the current docs at https://google.github.io/adk-docs/ and adjust the
import path below if it's changed since this was written.
"""
import os

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioServerParameters

from agents.prompts import EXPOSURE_AGENT_INSTRUCTION

MODEL = os.getenv("REELLEDGER_MODEL", "gemini-2.5-flash")


def _clickhouse_mcp_toolset() -> McpToolset:
    """Spawns the ClickHouse MCP server as a subprocess and exposes its
    tools (run_select_query, list_databases, list_tables, etc.) to the agent.
    """
    return McpToolset(
        connection_params=StdioServerParameters(
            command="uvx",
            args=["mcp-clickhouse"],
            env={
                "CLICKHOUSE_HOST": os.environ["CLICKHOUSE_HOST"],
                "CLICKHOUSE_PORT": os.environ.get("CLICKHOUSE_PORT", "8443"),
                "CLICKHOUSE_USER": os.environ.get("CLICKHOUSE_USER", "default"),
                "CLICKHOUSE_PASSWORD": os.environ.get("CLICKHOUSE_PASSWORD", ""),
                "CLICKHOUSE_SECURE": os.environ.get("CLICKHOUSE_SECURE", "true"),
                "CLICKHOUSE_DATABASE": os.environ.get("CLICKHOUSE_DATABASE", "reelledger"),
            },
        ),
        # Restrict to read-only analytical tools -- this agent should never
        # be able to mutate production financial data.
        tool_filter=["run_select_query", "list_tables", "list_databases"],
    )


def build_exposure_agent() -> LlmAgent:
    return LlmAgent(
        name="exposure_agent",
        model=MODEL,
        description=(
            "Answers questions about a production's current spend, burn rate, "
            "and budget-vs-actual by department using live ClickHouse data."
        ),
        instruction=EXPOSURE_AGENT_INSTRUCTION,
        tools=[_clickhouse_mcp_toolset()],
    )
