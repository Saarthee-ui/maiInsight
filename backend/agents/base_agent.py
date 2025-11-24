"""Base agent class for all agents."""

import structlog
from typing import Any, Dict, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from config import settings

logger = structlog.get_logger()


class BaseAgent:
    """Base class for all agents."""
    
    def __init__(
        self,
        name: str,
        llm: Optional[BaseChatModel] = None,
        temperature: Optional[float] = None,
        allow_no_llm: bool = False,
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            llm: Optional LLM instance (will create if not provided)
            temperature: LLM temperature (defaults to settings.agent_temperature)
            allow_no_llm: If True, don't raise error if LLM can't be created (default: False)
        """
        self.name = name
        self.temperature = temperature or settings.agent_temperature
        try:
            self.llm = llm or self._create_llm()
        except (ValueError, Exception) as e:
            if allow_no_llm:
                self.llm = None
                logger.warning(f"Agent {name} initialized without LLM", error=str(e))
            else:
                raise
        self.logger = logger.bind(agent=name)
        
    def _create_llm(self) -> BaseChatModel:
        """Create LLM instance based on configuration."""
        provider = settings.llm_provider.lower()
        
        if provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set")
            return ChatOpenAI(
                model="gpt-4o",
                temperature=self.temperature,
                api_key=settings.openai_api_key,
                timeout=30,  # 30 second timeout
            )
        elif provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=self.temperature,
                api_key=settings.anthropic_api_key,
                timeout=30,  # 30 second timeout
            )
        elif provider == "ollama":
            return ChatOllama(
                model="llama3.1",
                base_url=settings.ollama_base_url,
                temperature=self.temperature,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def log(self, level: str, message: str, **kwargs):
        """Structured logging."""
        getattr(self.logger, level.lower())(message, **kwargs)
    
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute agent task. Override in subclasses.
        
        This is the main entry point for agent execution.
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def validate_output(self, output: Any) -> bool:
        """
        Validate agent output. Override in subclasses.
        
        Returns:
            True if output is valid, False otherwise
        """
        return True
