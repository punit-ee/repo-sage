"""Advanced logging system for tracking agent interactions and performance."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AgentInteractionLogger:
    """
    Logger for tracking AI agent interactions and performance.

    Tracks:
    - Questions and answers
    - Search tool calls
    - Performance metrics (response time, searches made)
    - Conversation history
    - Errors and exceptions

    Example:
        >>> logger = AgentInteractionLogger("logs/agent_interactions.jsonl")
        >>> logger.log_interaction(
        ...     question="How do I install?",
        ...     answer="Run: pip install...",
        ...     metadata={"response_time": 2.5}
        ... )
    """

    def __init__(
        self,
        log_file: str | Path = "logs/agent_interactions.jsonl",
        console_output: bool = False,
    ):
        """
        Initialize the interaction logger.

        Args:
            log_file: Path to JSON Lines log file
            console_output: Whether to also print to console
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.console_output = console_output

        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.interaction_count = 0

        logger.info(f"Initialized AgentInteractionLogger: {self.log_file}")

    def log_interaction(
        self,
        question: str,
        answer: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a complete agent interaction.

        Args:
            question: User's question
            answer: Agent's answer
            metadata: Additional metadata (response_time, searches, etc.)
        """
        self.interaction_count += 1

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "interaction_id": self.interaction_count,
            "question": question,
            "answer": answer,
            "metadata": metadata or {},
        }

        self._write_log(interaction)

        if self.console_output:
            self._print_interaction(interaction)

    def log_search(
        self,
        query: str,
        search_type: str,
        results_count: int,
        top_score: float | None = None,
        response_time: float | None = None,
    ) -> None:
        """
        Log a search operation.

        Args:
            query: Search query
            search_type: Type of search (vector, text, hybrid)
            results_count: Number of results returned
            top_score: Score of top result
            response_time: Search execution time in seconds
        """
        search_log = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "search",
            "query": query,
            "search_type": search_type,
            "results_count": results_count,
            "top_score": top_score,
            "response_time_seconds": response_time,
        }

        self._write_log(search_log)

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an error or exception.

        Args:
            error_type: Type/category of error
            error_message: Error message
            context: Additional context about the error
        """
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
        }

        self._write_log(error_log)

    def log_performance(
        self,
        operation: str,
        duration_seconds: float,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """
        Log performance metrics.

        Args:
            operation: Name of the operation
            duration_seconds: How long it took
            metrics: Additional metrics
        """
        perf_log = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "performance",
            "operation": operation,
            "duration_seconds": duration_seconds,
            "metrics": metrics or {},
        }

        self._write_log(perf_log)

    def _write_log(self, log_entry: dict[str, Any]) -> None:
        """Write log entry to file in JSON Lines format."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write log: {e}")

    def _print_interaction(self, interaction: dict[str, Any]) -> None:
        """Print interaction to console in readable format."""
        print(f"\n{'='*70}")
        print(f"Interaction #{interaction['interaction_id']}")
        print(f"Time: {interaction['timestamp']}")
        print(f"{'='*70}")
        print(f"\nQ: {interaction['question']}")
        print(f"\nA: {interaction['answer'][:200]}...")
        if interaction.get("metadata"):
            print(f"\nMetadata: {interaction['metadata']}")
        print(f"{'='*70}\n")

    def get_session_stats(self) -> dict[str, Any]:
        """
        Get statistics for current session.

        Returns:
            Dictionary with session statistics
        """
        return {
            "session_id": self.session_id,
            "interactions": self.interaction_count,
            "log_file": str(self.log_file),
        }


class ConversationTracker:
    """
    Track conversation history and context.

    Maintains a conversation thread with questions, answers, and metadata.
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize conversation tracker.

        Args:
            max_history: Maximum number of interactions to keep in memory
        """
        self.max_history = max_history
        self.history: list[dict[str, Any]] = []
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def add_interaction(
        self,
        question: str,
        answer: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add an interaction to the conversation history."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "metadata": metadata or {},
        }

        self.history.append(interaction)

        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

    def get_history(self, last_n: int | None = None) -> list[dict[str, Any]]:
        """
        Get conversation history.

        Args:
            last_n: Return only last N interactions (all if None)

        Returns:
            List of interactions
        """
        if last_n is None:
            return self.history.copy()
        return self.history[-last_n:]

    def get_context_summary(self) -> str:
        """Get a summary of recent conversation context."""
        if not self.history:
            return "No conversation history"

        recent = self.history[-3:]  # Last 3 interactions
        summary = []

        for i, interaction in enumerate(recent, 1):
            q = interaction["question"][:50]
            a = interaction["answer"][:50]
            summary.append(f"{i}. Q: {q}... A: {a}...")

        return "\n".join(summary)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history = []

    def export_to_file(self, filepath: str | Path) -> None:
        """
        Export conversation history to JSON file.

        Args:
            filepath: Path to output file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "conversation_id": self.conversation_id,
            "total_interactions": len(self.history),
            "interactions": self.history,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported conversation to {filepath}")


def create_interaction_logger(
    log_dir: str | Path = "logs",
    console_output: bool = False,
) -> AgentInteractionLogger:
    """
    Create an interaction logger with default settings.

    Args:
        log_dir: Directory for log files
        console_output: Whether to print to console

    Returns:
        Configured AgentInteractionLogger

    Example:
        >>> logger = create_interaction_logger()
        >>> logger.log_interaction("test question", "test answer")
    """
    log_dir = Path(log_dir)
    log_file = log_dir / "agent_interactions.jsonl"

    return AgentInteractionLogger(log_file=log_file, console_output=console_output)
