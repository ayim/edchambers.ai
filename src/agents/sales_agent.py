from typing import List, Dict, Any, Tuple, Literal
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from dotenv import load_dotenv
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
import os

# Load environment variables
load_dotenv()

# Tools
# from ..services.voice.text_to_speech import TextToSpeechService
# from ..services.voice.speech_to_text import SpeechToTextService
# from ..services.video.obs_controller import OBSController
# from ..services.memory.objection_tracker import ObjectionTracker

llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile")

class MemoryType(Enum):
    OBJECTION = "objection"
    RESPONSE = "response"
    SENTIMENT = "sentiment"
    BACKGROUND = "background"
    FOLLOWUP = "followup"

@dataclass
class Memory:
    type: MemoryType
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime = datetime.now()
    
    def to_string(self) -> str:
        return (
            f"Type: {self.type.value}\n"
            f"Content: {self.content}\n"
            f"Context: {json.dumps(self.metadata, indent=2)}\n"
            f"When: {self.timestamp.isoformat()}"
        )

class MemoryManager:
    def __init__(self, store: InMemoryStore, namespace: Tuple[str, ...]):
        self.store = store
        self.namespace = namespace
        self.memory_tools = [
            create_manage_memory_tool(namespace),
            create_search_memory_tool(namespace)
        ]
    
    async def add_memory(self, memory: Memory):
        'Add a new memory to the store'
        await self.store.add(
            self.namespace,
            memory.to_string(),
            metadata={
                "type": memory.type.value,
                "timestamp": memory.timestamp.isoformat(),
                **memory.metadata
            }
        )
    
    async def search_memories(self, query: str, memory_type: MemoryType = None) -> List[Memory]:
        'Search memories with optional type filter'
        filter_dict = {"type": memory_type.value} if memory_type else {}
        items = await self.store.search(
            self.namespace,
            query=query,
            filter_dict=filter_dict
        )
        return items

    async def get_recent_memories(self, memory_type: MemoryType = None, limit: int = 5) -> List[Memory]:
        'Get most recent memories of a specific type'
        filter_dict = {"type": memory_type.value} if memory_type else {}
        items = await self.store.search(
            self.namespace,
            query="",  # Empty query to get all
            filter_dict=filter_dict,
            sort_by="timestamp",
            limit=limit
        )
        return items

class SalesAgent:
    def __init__(self):
        # Initialize store for vector embeddings
        self.store = InMemoryStore(
            index={
                "dims": 1536,
                "embed": "openai:text-embedding-3-small"
            }
        )
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            store=self.store,
            namespace=("sales_agent_memories",)
        )
        
        # Initialize services
        self.tts = TextToSpeechService()
        self.stt = SpeechToTextService()
        self.obs = OBSController()
        self.objection_tracker = ObjectionTracker()
        
        # Tools include memory tools
        self.tools = self.memory_manager.memory_tools + [
            self.tts.speak,
            self.obs.pause_video,
            self.obs.resume_video,
            self.objection_tracker.record_objection
        ]
        
        # Checkpoint saver for persistence
        self.checkpointer = InMemorySaver()
        
        # Initialize the agent workflow
        self.workflow = self._create_workflow()

    async def _create_prompt(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        'Create the prompt with relevant memories and context'
        # Get relevant memories for the current context
        current_msg = state["messages"][-1].content
        
        # Search for different types of relevant memories
        objection_memories = await self.memory_manager.search_memories(
            current_msg, 
            memory_type=MemoryType.OBJECTION
        )
        response_memories = await self.memory_manager.search_memories(
            current_msg, 
            memory_type=MemoryType.RESPONSE
        )
        background_memories = await self.memory_manager.search_memories(
            current_msg, 
            memory_type=MemoryType.BACKGROUND
        )
        
        # Format memories by type
        memories_str = (
            f"## Recent Objections:\n"
            f"{chr(10).join(str(m) for m in objection_memories[:3])}\n\n"
            f"## Successful Responses:\n"
            f"{chr(10).join(str(m) for m in response_memories[:3])}\n\n"
            f"## Background Information:\n"
            f"{chr(10).join(str(m) for m in background_memories[:3])}"
        )
        
        # Create system message with memories and role
        system_msg = {
            "role": "system",
            "content": (
                f"You are an AI Sales Representative. Use memories and context to have natural sales conversations.\n\n"
                f"## Memories:\n"
                f"{memories_str}\n\n"
                f"## Guidelines:\n"
                f"- Listen actively for objections and interruptions\n"
                f"- Use past interaction context to improve responses\n"
                f"- Maintain a professional and empathetic tone\n"
                f"- Know when to escalate to human sales rep"
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

    async def handle_message(self, message: str) -> str:
        'Handle incoming message and return response'
        # Initialize state
        state = {
            "messages": [{"role": "user", "content": message}]
        }
        
        # Run the workflow
        result = await self.workflow.invoke(state)
        
        # Store the response as a memory
        response = result["messages"][-1]["content"]
        await self.memory_manager.add_memory(
            Memory(
                type=MemoryType.RESPONSE,
                content=response,
                metadata={
                    "user_message": message,
                    "successful": True  # This should be determined by feedback
                }
            )
        )
        
        return response

    async def handle_interruption(self, interruption: str) -> str:
        'Handle interruptions during sales pitch'
        # Record the objection as a memory
        await self.memory_manager.add_memory(
            Memory(
                type=MemoryType.OBJECTION,
                content=interruption,
                metadata={
                    "context": "interruption",
                    "handled": False
                }
            )
        )
        
        # Pause video
        await self.obs.pause_video()
        
        # Get agent response
        response = await self.handle_message(
            f"INTERRUPTION: {interruption}\n"
            f"Please handle this objection appropriately."
        )
        
        # Update objection memory as handled
        await self.memory_manager.add_memory(
            Memory(
                type=MemoryType.RESPONSE,
                content=response,
                metadata={
                    "objection": interruption,
                    "context": "interruption_response",
                    "handled": True
                }
            )
        )
        
        # Resume video if appropriate
        if "RESUME_VIDEO" in response:
            await self.obs.resume_video()
            
        return response