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
from datetime import datetime
import json
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

class Memory(BaseModel):
    content: str
    type: str
    metadata: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_string(self) -> str:
        return (
            f"Type: {self.type}\n"
            f"Content: {self.content}\n"
            f"Context: {json.dumps(self.metadata, indent=2)}\n"
            f"When: {self.timestamp.isoformat()}"
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
        
        # Initialize memory namespace
        self.memory_namespace = ("sales_agent_memories",)
        
        # Create memory tools
        memory_tools = [
            create_manage_memory_tool(self.memory_namespace),
            create_search_memory_tool(self.memory_namespace)
        ]
        
        # Initialize MediaPlayer
        self.media_player = MediaPlayer()
        
        # Create tools with proper schemas
        self.tools = [
            *memory_tools,  # Add memory tools
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

    async def add_memory(self, content: str, memory_type: str, metadata: Dict[str, Any] = None):
        'Add a new memory to the store'
        if metadata is None:
            metadata = {}
            
        memory = Memory(
            content=content,
            type=memory_type,
            metadata=metadata
        )
        
        meta_dict = metadata.copy()
        meta_dict.update({
            "type": memory_type,
            "timestamp": memory.timestamp.isoformat()
        })
        
        await self.store.add(
            self.memory_namespace,
            memory.to_string(),
            metadata=meta_dict
        )

    async def search_memories(self, query: str, memory_type: str = None) -> List[str]:
        'Search memories with optional type filter'
        filter_dict = {"type": memory_type} if memory_type else {}
        items = await self.store.search(
            self.memory_namespace,
            query=query,
            filter_dict=filter_dict
        )
        return items

    async def get_recent_memories(self, memory_type: str = None, limit: int = 5) -> List[str]:
        'Get most recent memories of a specific type'
        filter_dict = {"type": memory_type} if memory_type else {}
        items = await self.store.search(
            self.memory_namespace,
            query="",  # Empty query to get all
            filter_dict=filter_dict,
            sort_by="timestamp",
            limit=limit
        )
        return items

    async def _create_prompt(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        'Create the prompt with relevant context and memories'
        # Get current context
        current_msg = state["messages"][-1].content
        
        # Search for relevant memories
        relevant_memories = await self.search_memories(current_msg)
        recent_interruptions = await self.get_recent_memories("interruption", limit=3)
        
        # Format memories for the prompt
        memories_str = (
            f"## Relevant Context:\n"
            f"{chr(10).join(str(m) for m in relevant_memories)}\n\n"
            f"## Recent Interruptions:\n"
            f"{chr(10).join(str(m) for m in recent_interruptions)}"
        )
        
        system_msg = {
            "role": "system",
            "content": (
                f"You are an AI Sales Representative that plays a sequence of videos.\n\n"
                f"## Memories:\n{memories_str}\n\n"
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
        # Record start of sales pitch
        await self.add_memory(
            content=f"Started sales pitch with videos from: {video_folder}",
            memory_type="session",
            metadata={"video_folder": video_folder}
        )
        
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
        # Record the interruption
        await self.add_memory(
            content=interruption_text,
            memory_type="interruption",
            metadata={
                "handled": False,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Create state for interruption handling
        state = {
            "messages": [{
                "role": "user",
                "content": f"Interruption detected: {interruption_text}"
            }]
        }
        
        # Run the workflow to handle interruption
        result = await self.workflow.invoke(state)
        
        # Record the response
        await self.add_memory(
            content=result["messages"][-1]["content"],
            memory_type="response",
            metadata={
                "interruption": interruption_text,
                "handled": True,
                "timestamp": datetime.now().isoformat()
            }
        )