"""AI Agent for repository Q&A using pydantic-ai and search tools."""

import logging
import time
from typing import Any

from pydantic_ai import Agent, RunContext

from .logging_system import AgentInteractionLogger, ConversationTracker
from .search import SearchEngine

logger = logging.getLogger(__name__)


class RepoAgent:
    """
    AI Agent for answering questions about repository documentation.

    Uses pydantic-ai with search tools to provide intelligent answers
    based on repository content.

    Example:
        >>> from repo_sage import RepoAgent, SearchEngine, read_repo_data
        >>> from repo_sage.chunking import DocumentChunker, SlidingWindowStrategy
        >>>
        >>> # Prepare search engine
        >>> documents = read_repo_data("owner", "repo")
        >>> chunker = DocumentChunker(SlidingWindowStrategy(1000, 500))
        >>> chunks = chunker.chunk_documents(documents)
        >>> engine = SearchEngine()
        >>> engine.fit([c.to_dict() for c in chunks])
        >>>
        >>> # Create agent
        >>> agent = RepoAgent(engine)
        >>> response = agent.ask("How do I install this?")
    """

    def __init__(
        self,
        search_engine: SearchEngine,
        model: str = "openai:gpt-4o-mini",
        system_prompt: str | None = None,
        enable_logging: bool = True,
        log_file: str | None = None,
    ):
        """
        Initialize the RepoAgent.

        Args:
            search_engine: Fitted SearchEngine instance
            model: Model to use (e.g., "openai:gpt-4o-mini", "anthropic:claude-3-sonnet")
            system_prompt: Custom system prompt (uses default if None)
            enable_logging: Whether to enable interaction logging
            log_file: Custom log file path (uses default if None)
        """
        self.search_engine = search_engine
        self.model = model

        # Default system prompt
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        self.system_prompt = system_prompt

        # Initialize logging
        self.enable_logging = enable_logging
        if enable_logging:
            if log_file:
                self.interaction_logger = AgentInteractionLogger(log_file)
            else:
                from .logging_system import create_interaction_logger

                self.interaction_logger = create_interaction_logger()

            self.conversation_tracker = ConversationTracker()
        else:
            self.interaction_logger = None
            self.conversation_tracker = None

        # Create pydantic-ai agent with search tools
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            deps_type=SearchEngine,
        )

        # Register search tools
        self._register_tools()

        logger.info(f"Initialized RepoAgent with model: {model}")
        if enable_logging:
            logger.info("Interaction logging enabled")

    @staticmethod
    def _get_default_system_prompt() -> str:
        """Get default system prompt."""
        return """You are a helpful assistant for a code repository.

Your job is to help users understand the repository by answering their questions
based on the documentation.

IMPORTANT GUIDELINES:
1. Always search for relevant information before answering
2. If the first search doesn't give enough information, try different search terms
3. Make multiple searches if needed to provide comprehensive answers
4. Cite the source of your information when possible
5. If you can't find the answer, say so honestly
6. Use hybrid search by default for best results

Be concise, accurate, and helpful."""

    def _register_tools(self) -> None:
        """Register search tools with the agent."""

        @self.agent.tool
        async def vector_search(
            ctx: RunContext[SearchEngine], query: str, top_k: int = 5
        ) -> list[dict[str, Any]]:
            """
            Perform semantic vector search on the repository.

            Use this for questions about concepts, ideas, or when you need
            to understand the meaning and context.

            Args:
                query: The search query
                top_k: Number of results to return (default: 5)

            Returns:
                List of relevant documents with scores
            """
            logger.info(f"Agent performing vector search: {query}")
            results: list[dict[str, Any]] = ctx.deps.search(
                query, search_type="vector", top_k=top_k
            )
            return results

        @self.agent.tool
        async def text_search(
            ctx: RunContext[SearchEngine], query: str, top_k: int = 5
        ) -> list[dict[str, Any]]:
            """
            Perform keyword-based text search on the repository.

            Use this for finding specific terms, function names, or exact matches.

            Args:
                query: The search query
                top_k: Number of results to return (default: 5)

            Returns:
                List of relevant documents with scores
            """
            logger.info(f"Agent performing text search: {query}")
            results: list[dict[str, Any]] = ctx.deps.search(
                query, search_type="text", top_k=top_k
            )
            return results

        @self.agent.tool
        async def hybrid_search(
            ctx: RunContext[SearchEngine],
            query: str,
            top_k: int = 5,
            vector_weight: float = 0.5,
        ) -> list[dict[str, Any]]:
            """
            Perform hybrid search combining vector and text search.

            This is the recommended search method for most queries as it
            combines semantic understanding with keyword matching.

            Args:
                query: The search query
                top_k: Number of results to return (default: 5)
                vector_weight: Weight for vector search 0.0-1.0 (default: 0.5)

            Returns:
                List of relevant documents with scores
            """
            logger.info(f"Agent performing hybrid search: {query}")
            results: list[dict[str, Any]] = ctx.deps.search(
                query, search_type="hybrid", top_k=top_k, vector_weight=vector_weight
            )
            return results

    async def ask_async(self, question: str) -> str:
        """
        Ask a question asynchronously and get an answer.

        Args:
            question: User's question

        Returns:
            Agent's answer based on repository content
        """
        start_time = time.time()
        logger.info(f"Agent received question: {question}")

        try:
            result = await self.agent.run(question, deps=self.search_engine)
            answer: str = result.output
            response_time = time.time() - start_time

            logger.info("Agent generated response")

            # Log the interaction
            if self.enable_logging and self.interaction_logger:
                metadata = {
                    "model": self.model,
                    "response_time_seconds": round(response_time, 2),
                    "answer_length": len(answer),
                }

                self.interaction_logger.log_interaction(
                    question=question, answer=answer, metadata=metadata
                )

                # Track in conversation
                if self.conversation_tracker:
                    self.conversation_tracker.add_interaction(
                        question=question, answer=answer, metadata=metadata
                    )

            return answer

        except Exception as e:
            response_time = time.time() - start_time

            # Log the error
            if self.enable_logging and self.interaction_logger:
                self.interaction_logger.log_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={
                        "question": question,
                        "response_time_seconds": round(response_time, 2),
                    },
                )

            raise

    def ask(self, question: str) -> str:
        """
        Ask a question and get an answer (synchronous wrapper).

        Args:
            question: User's question

        Returns:
            Agent's answer based on repository content

        Example:
            >>> agent = RepoAgent(search_engine)
            >>> answer = agent.ask("How do I install this project?")
            >>> print(answer)
        """
        import asyncio

        return asyncio.run(self.ask_async(question))

    def get_conversation_history(
        self, last_n: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get conversation history.

        Args:
            last_n: Return only last N interactions (all if None)

        Returns:
            List of interactions

        Example:
            >>> history = agent.get_conversation_history(last_n=5)
            >>> for interaction in history:
            ...     print(interaction['question'])
        """
        if self.conversation_tracker:
            return self.conversation_tracker.get_history(last_n)
        return []

    def get_session_stats(self) -> dict[str, Any]:
        """
        Get statistics for the current session.

        Returns:
            Dictionary with session statistics
        """
        if self.interaction_logger:
            stats = self.interaction_logger.get_session_stats()
            if self.conversation_tracker:
                stats["conversation_id"] = self.conversation_tracker.conversation_id
                stats["history_size"] = len(self.conversation_tracker.history)
            return stats
        return {"logging_enabled": False}

    def export_conversation(self, filepath: str) -> None:
        """
        Export conversation history to a file.

        Args:
            filepath: Path to output file

        Example:
            >>> agent.export_conversation("conversations/session_001.json")
        """
        if self.conversation_tracker:
            self.conversation_tracker.export_to_file(filepath)
        else:
            logger.warning("Logging not enabled, no conversation to export")


def create_repo_agent(
    search_engine: SearchEngine,
    model: str = "openai:gpt-4o-mini",
    system_prompt: str | None = None,
) -> RepoAgent:
    """
    Convenience function to create a RepoAgent.

    Args:
        search_engine: Fitted SearchEngine instance
        model: Model to use
        system_prompt: Custom system prompt

    Returns:
        Configured RepoAgent instance

    Example:
        >>> from repo_sage import create_search_engine, create_repo_agent
        >>> engine = create_search_engine(documents)
        >>> agent = create_repo_agent(engine)
        >>> answer = agent.ask("What is this repository about?")
    """
    return RepoAgent(search_engine, model, system_prompt)
