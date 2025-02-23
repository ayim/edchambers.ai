from typing import List, Dict, Any, Tuple, Literal
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from dotenv import load_dotenv
from langchain.tools import Tool, StructuredTool
from langchain_core.tools import ToolException
from pydantic import BaseModel, Field
import os

# Import video and interrupt services
from src.video.OBS_media_player_loop import MediaPlayer
from src.interrupt.interrupt_service import handle_interruption

# Load environment variables
load_dotenv()

llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile")

# Define input schemas for tools
class VideoPlaybackInput(BaseModel):
    video_folder: str = Field(
        description="Path to folder containing MP4 files to play in sequence"
    )

class InterruptionInput(BaseModel):
    interruption_text: str = Field(
        description="The text of the user's interruption that needs to be handled"
    )

class SalesAgent:
    def __init__(self):
        # Initialize store for vector embeddings
        self.store = InMemoryStore(
            index={
                "dims": 1536,
                "embed": "openai:text-embedding-3-small"
            }
        )
        
        # Initialize MediaPlayer
        self.media_player = MediaPlayer()
        
        # Create tools with proper schemas
        self.tools = [
            StructuredTool.from_function(
                func=self.media_player.play_videos,
                name="play_videos",
                description="Play a sequence of videos from a specified folder in a loop",
                args_schema=VideoPlaybackInput,
                handle_tool_error=True,
                return_direct=False
            ),
            StructuredTool.from_function(
                func=handle_interruption,
                name="handle_interruption",
                description="Handle user interruption during video playback by pausing and addressing the interruption",
                args_schema=InterruptionInput,
                handle_tool_error=True,
                return_direct=False
            )
        ]
        
        # Checkpoint saver for persistence
        self.checkpointer = InMemorySaver()
        
        # Initialize the agent workflow
        self.workflow = self._create_workflow()

    def _create_prompt(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        'Create the prompt with relevant context'
        system_msg = {
            "role": "system",
            "content": (
                f"You are an AI Sales Representative that plays a sequence of videos.\n\n"
                f"## Primary Functions:\n"
                f"1. Play videos in sequence using the play_videos function\n"
                f"2. When an interruption is detected, call handle_interruption\n\n"
                f"## Guidelines:\n"
                f"- Monitor for interruptions during video playback\n"
                f"- Pause video sequence when interrupted\n"
                f"- Resume video sequence after interruption is handled\n\n"
                f"## Error Handling:\n"
                f"- If video playback fails, report the error and try again\n"
                f"- If interruption handling fails, escalate to human operator"
            )
        }
        
        return [system_msg] + state["messages"]

    def _create_workflow(self) -> StateGraph:
        'Create the agent workflow graph'
        # Create the main sales agent
        agent = create_react_agent(
            llm=llm,
            prompt=self._create_prompt,
            tools=self.tools,
            store=self.store,
            checkpointer=self.checkpointer
        )
        
        # Create the workflow graph
        workflow = StateGraph()
        
        # Add agent node
        workflow.add_node("agent", agent)
        
        # Add edges
        workflow.add_edge("agent", END)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        return workflow.compile()

    async def start_sales_pitch(self, video_folder: str):
        'Start the sales pitch by playing videos from the specified folder'
        # Initialize state to start video playback
        state = {
            "messages": [{
                "role": "user", 
                "content": f"Start playing the sales pitch videos from folder: {video_folder}"
            }]
        }
        
        # Run the workflow
        await self.workflow.invoke(state)
    
    async def handle_user_interruption(self, interruption_text: str):
        'Handle user interruption during video playback'
        # Create state for interruption handling
        state = {
            "messages": [{
                "role": "user",
                "content": f"Interruption detected: {interruption_text}"
            }]
        }
        
        # Run the workflow to handle interruption
        await self.workflow.invoke(state)