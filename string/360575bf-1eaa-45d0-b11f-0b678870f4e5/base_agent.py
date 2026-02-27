"""
Base agent class with common functionality
"""
from typing import Dict, Any, Optional, Callable
from langchain_openai import ChatOpenAI
from backend.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(
        self,
        name: str,
        temperature: float = 0.3,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            temperature: LLM temperature
            progress_callback: Optional callback for progress updates
        """
        self.name = name
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY
        )
        self.progress_callback = progress_callback
        logger.info(f"Initialized {self.name}")
    
    async def update_progress(self, stage: str, progress: int, message: str):
        """Send progress update"""
        if self.progress_callback:
            await self.progress_callback({
                "agent": self.name,
                "stage": stage,
                "progress": progress,
                "message": message
            })
        logger.info(f"[{self.name}] {stage}: {message} ({progress}%)")
    
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute agent task (to be implemented by subclasses)
        
        Returns:
            Dict containing agent output
        """
        raise NotImplementedError("Subclasses must implement execute()")
