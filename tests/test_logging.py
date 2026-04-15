"""Tests for logging system."""

import json

from repo_sage.log_analyzer import LogAnalyzer
from repo_sage.logging_system import (
    AgentInteractionLogger,
    ConversationTracker,
    create_interaction_logger,
)


class TestAgentInteractionLogger:
    """Test AgentInteractionLogger class."""

    def test_initialization(self, tmp_path):
        """Test logger initialization."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        assert logger.log_file == log_file
        assert logger.interaction_count == 0
        assert logger.session_id is not None

    def test_log_interaction(self, tmp_path):
        """Test logging an interaction."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_interaction(
            question="test question",
            answer="test answer",
            metadata={"key": "value"},
        )

        # Verify log was written
        assert log_file.exists()

        # Verify content
        with open(log_file) as f:
            log = json.loads(f.readline())

        assert log["question"] == "test question"
        assert log["answer"] == "test answer"
        assert log["metadata"]["key"] == "value"
        assert "timestamp" in log
        assert "session_id" in log

    def test_log_search(self, tmp_path):
        """Test logging a search operation."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_search(
            query="test query",
            search_type="hybrid",
            results_count=5,
            top_score=0.95,
            response_time=0.5,
        )

        with open(log_file) as f:
            log = json.loads(f.readline())

        assert log["event_type"] == "search"
        assert log["query"] == "test query"
        assert log["search_type"] == "hybrid"
        assert log["results_count"] == 5

    def test_log_error(self, tmp_path):
        """Test logging an error."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_error(
            error_type="ValueError",
            error_message="Invalid input",
            context={"input": "bad"},
        )

        with open(log_file) as f:
            log = json.loads(f.readline())

        assert log["event_type"] == "error"
        assert log["error_type"] == "ValueError"
        assert log["error_message"] == "Invalid input"

    def test_log_performance(self, tmp_path):
        """Test logging performance metrics."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_performance(
            operation="search", duration_seconds=1.5, metrics={"count": 10}
        )

        with open(log_file) as f:
            log = json.loads(f.readline())

        assert log["event_type"] == "performance"
        assert log["operation"] == "search"
        assert log["duration_seconds"] == 1.5

    def test_multiple_interactions(self, tmp_path):
        """Test logging multiple interactions."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        for i in range(3):
            logger.log_interaction(question=f"question {i}", answer=f"answer {i}")

        assert logger.interaction_count == 3

        # Verify all logged
        with open(log_file) as f:
            logs = [json.loads(line) for line in f]

        assert len(logs) == 3

    def test_get_session_stats(self, tmp_path):
        """Test getting session statistics."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_interaction("q1", "a1")
        logger.log_interaction("q2", "a2")

        stats = logger.get_session_stats()

        assert stats["interactions"] == 2
        assert "session_id" in stats
        assert str(log_file) in stats["log_file"]


class TestConversationTracker:
    """Test ConversationTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = ConversationTracker(max_history=10)

        assert tracker.max_history == 10
        assert len(tracker.history) == 0
        assert tracker.conversation_id is not None

    def test_add_interaction(self):
        """Test adding interactions."""
        tracker = ConversationTracker()

        tracker.add_interaction("q1", "a1")
        tracker.add_interaction("q2", "a2")

        assert len(tracker.history) == 2
        assert tracker.history[0]["question"] == "q1"
        assert tracker.history[1]["answer"] == "a2"

    def test_max_history_limit(self):
        """Test history size limit."""
        tracker = ConversationTracker(max_history=3)

        for i in range(5):
            tracker.add_interaction(f"q{i}", f"a{i}")

        # Should only keep last 3
        assert len(tracker.history) == 3
        assert tracker.history[0]["question"] == "q2"
        assert tracker.history[-1]["question"] == "q4"

    def test_get_history(self):
        """Test getting history."""
        tracker = ConversationTracker()

        for i in range(5):
            tracker.add_interaction(f"q{i}", f"a{i}")

        # Get all
        all_history = tracker.get_history()
        assert len(all_history) == 5

        # Get last 2
        recent = tracker.get_history(last_n=2)
        assert len(recent) == 2
        assert recent[0]["question"] == "q3"

    def test_get_context_summary(self):
        """Test context summary."""
        tracker = ConversationTracker()

        # Empty history
        summary = tracker.get_context_summary()
        assert "No conversation history" in summary

        # With history
        tracker.add_interaction("What is Python?", "A programming language")
        tracker.add_interaction("How to install?", "Use pip install")

        summary = tracker.get_context_summary()
        assert "What is Python" in summary

    def test_clear_history(self):
        """Test clearing history."""
        tracker = ConversationTracker()

        tracker.add_interaction("q1", "a1")
        assert len(tracker.history) == 1

        tracker.clear_history()
        assert len(tracker.history) == 0

    def test_export_to_file(self, tmp_path):
        """Test exporting to file."""
        tracker = ConversationTracker()
        tracker.add_interaction("q1", "a1")
        tracker.add_interaction("q2", "a2")

        output_file = tmp_path / "conversation.json"
        tracker.export_to_file(output_file)

        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["total_interactions"] == 2
        assert len(data["interactions"]) == 2
        assert data["interactions"][0]["question"] == "q1"


class TestLogAnalyzer:
    """Test LogAnalyzer class."""

    def test_initialization_nonexistent_file(self, tmp_path):
        """Test with non-existent file."""
        log_file = tmp_path / "nonexistent.jsonl"
        analyzer = LogAnalyzer(log_file)

        assert len(analyzer.logs) == 0

    def test_load_logs(self, tmp_path):
        """Test loading logs from file."""
        log_file = tmp_path / "test.jsonl"

        # Create sample logs
        logs = [
            {"question": "q1", "answer": "a1"},
            {"event_type": "search", "query": "test"},
            {"event_type": "error", "error_type": "ValueError"},
        ]

        with open(log_file, "w") as f:
            for log in logs:
                f.write(json.dumps(log) + "\n")

        analyzer = LogAnalyzer(log_file)
        assert len(analyzer.logs) == 3

    def test_get_interactions(self, tmp_path):
        """Test getting interaction logs."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_interaction("q1", "a1")
        logger.log_search("test", "vector", 5)

        analyzer = LogAnalyzer(log_file)
        interactions = analyzer.get_interactions()

        assert len(interactions) == 1
        assert interactions[0]["question"] == "q1"

    def test_get_summary(self, tmp_path):
        """Test getting summary statistics."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_interaction("q1", "a1", metadata={"response_time_seconds": 1.0})
        logger.log_search("test", "vector", 5)
        logger.log_error("ValueError", "test error")

        analyzer = LogAnalyzer(log_file)
        summary = analyzer.get_summary()

        assert summary["interactions"] == 1
        assert summary["searches"] == 1
        assert summary["errors"] == 1
        assert summary["avg_response_time_seconds"] == 1.0

    def test_get_common_questions(self, tmp_path):
        """Test getting common questions."""
        log_file = tmp_path / "test.jsonl"
        logger = AgentInteractionLogger(log_file)

        logger.log_interaction("How to install?", "a1")
        logger.log_interaction("How to install?", "a2")
        logger.log_interaction("What is this?", "a3")

        analyzer = LogAnalyzer(log_file)
        common = analyzer.get_common_questions()

        assert len(common) == 2
        assert common[0][0] == "How to install?"
        assert common[0][1] == 2


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_interaction_logger(self, tmp_path, monkeypatch):
        """Test create_interaction_logger function."""
        # Change to tmp directory
        monkeypatch.chdir(tmp_path)

        logger = create_interaction_logger(log_dir="test_logs")

        assert logger.log_file.parent.name == "test_logs"
        assert logger.log_file.name == "agent_interactions.jsonl"
