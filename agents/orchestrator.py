"""
Producer Agent -- the root agent a user actually talks to.

Wires the Exposure Agent and Comps Agent in as sub-agents using ADK's
built-in multi-agent delegation (an LlmAgent with `sub_agents` set will
route to them automatically based on each sub-agent's `description`, and
can also be driven explicitly via AgentTool if you want tighter control --
see the commented alternative below).
"""
import os

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner

from agents.comps_agent import build_comps_agent
from agents.exposure_agent import build_exposure_agent
from agents.prompts import PRODUCER_AGENT_INSTRUCTION

MODEL = os.getenv("REELLEDGER_MODEL", "gemini-2.5-flash")


def build_producer_agent() -> LlmAgent:
    exposure_agent = build_exposure_agent()
    comps_agent = build_comps_agent()

    return LlmAgent(
        name="producer_agent",
        model=MODEL,
        description="Root agent for ReelLedger -- routes producer questions to the right specialist.",
        instruction=PRODUCER_AGENT_INSTRUCTION,
        sub_agents=[exposure_agent, comps_agent],
        # Alternative, more explicit wiring if you want the producer agent to
        # call sub-agents as tools rather than via automatic LLM-driven
        # transfer (useful if you want both agents to run and be synthesized
        # in one turn, e.g. for the "over budget AND is this still a good
        # bet" combined question):
        #
        # from google.adk.tools.agent_tool import AgentTool
        # tools=[AgentTool(agent=exposure_agent), AgentTool(agent=comps_agent)],
    )


def build_runner() -> InMemoryRunner:
    """Convenience factory used by the FastAPI backend."""
    return InMemoryRunner(agent=build_producer_agent(), app_name="reelledger")
