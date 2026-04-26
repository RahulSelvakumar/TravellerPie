# agents/sub_agents.py
import os
from langchain_google_vertexai import ChatVertexAI
from google.cloud.aiplatform_v1beta1.types import Tool as VertexTool
from langchain_core.messages import SystemMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

class TravellerSubAgents:
    def __init__(self):
        # Using Gemini 2.5 Flash for speed and high context window
        self.llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            project="travellerpie-hackathon",
            location="us-central1",
            temperature=0,
            max_retries=10
        )
        # 2026 FIXED SCHEMA: Correct native tool for Google Search
        self.grounding_tool = VertexTool(google_search={})

    async def transit_agent(self, messages):
        prompt = "You are the Transit Specialist. Summarize real-time flights and transport options found in the history."
        return await self.llm.ainvoke([SystemMessage(content=prompt)] + messages, tools=[self.grounding_tool])

    async def intel_agent(self, messages, preferences=[]):
        pref_ctx = f"User Preferences: {', '.join(preferences)}."
        prompt = f"You are the Local Intel Agent. {pref_ctx} Find hidden gems and coffee spots using live search."
        return await self.llm.ainvoke([SystemMessage(content=prompt)] + messages, tools=[self.grounding_tool])

    async def planning_agent(self, messages, preferences=[]):
        pref_ctx = f"User Preferences: {', '.join(preferences)}."
        prompt = f"You are the Lead Planner. {pref_ctx} Build a structured itinerary using all grounded data."
        return await self.llm.ainvoke([SystemMessage(content=prompt)] + messages, tools=[self.grounding_tool])