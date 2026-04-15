"""Log analyzer for agent interactions - view and analyze logs."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


class LogAnalyzer:
    """
    Analyze agent interaction logs.

    Provides insights into:
    - Most common questions
    - Average response times
    - Search patterns
    - Error rates
    """

    def __init__(self, log_file: str | Path):
        """
        Initialize log analyzer.

        Args:
            log_file: Path to JSON Lines log file
        """
        self.log_file = Path(log_file)
        self.logs: list[dict[str, Any]] = []
        self._load_logs()

    def _load_logs(self) -> None:
        """Load logs from file."""
        if not self.log_file.exists():
            print(f"Log file not found: {self.log_file}")
            return

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    self.logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    def get_interactions(self) -> list[dict[str, Any]]:
        """Get all interaction logs."""
        return [log for log in self.logs if "question" in log and "answer" in log]

    def get_searches(self) -> list[dict[str, Any]]:
        """Get all search logs."""
        return [log for log in self.logs if log.get("event_type") == "search"]

    def get_errors(self) -> list[dict[str, Any]]:
        """Get all error logs."""
        return [log for log in self.logs if log.get("event_type") == "error"]

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Dictionary with summary statistics
        """
        interactions = self.get_interactions()
        searches = self.get_searches()
        errors = self.get_errors()

        # Calculate average response time
        response_times = [
            i["metadata"].get("response_time_seconds", 0)
            for i in interactions
            if "metadata" in i
        ]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # Get unique sessions
        sessions = {log.get("session_id") for log in self.logs if "session_id" in log}

        return {
            "total_logs": len(self.logs),
            "interactions": len(interactions),
            "searches": len(searches),
            "errors": len(errors),
            "unique_sessions": len(sessions),
            "avg_response_time_seconds": round(avg_response_time, 2),
        }

    def get_common_questions(self, top_n: int = 10) -> list[tuple[str, int]]:
        """
        Get most common questions.

        Args:
            top_n: Number of top questions to return

        Returns:
            List of (question, count) tuples
        """
        interactions = self.get_interactions()
        questions = [i["question"] for i in interactions]
        counter = Counter(questions)
        return counter.most_common(top_n)

    def get_search_stats(self) -> dict[str, Any]:
        """
        Get search statistics.

        Returns:
            Dictionary with search statistics
        """
        searches = self.get_searches()

        if not searches:
            return {"message": "No search logs found"}

        # Search type distribution
        search_types = Counter(s.get("search_type") for s in searches)

        # Average results count
        results_counts = [s.get("results_count", 0) for s in searches]
        avg_results = sum(results_counts) / len(results_counts) if results_counts else 0

        # Average search time
        search_times = [
            s.get("response_time_seconds", 0)
            for s in searches
            if s.get("response_time_seconds")
        ]
        avg_search_time = sum(search_times) / len(search_times) if search_times else 0

        return {
            "total_searches": len(searches),
            "search_types": dict(search_types),
            "avg_results_per_search": round(avg_results, 1),
            "avg_search_time_seconds": round(avg_search_time, 3),
        }

    def get_error_summary(self) -> dict[str, Any]:
        """
        Get error summary.

        Returns:
            Dictionary with error statistics
        """
        errors = self.get_errors()

        if not errors:
            return {"message": "No errors logged"}

        # Error type distribution
        error_types = Counter(e.get("error_type") for e in errors)

        return {
            "total_errors": len(errors),
            "error_types": dict(error_types),
            "recent_errors": errors[-5:],  # Last 5 errors
        }

    def print_report(self) -> None:
        """Print a comprehensive report."""
        print("=" * 70)
        print("AGENT INTERACTION LOG ANALYSIS")
        print("=" * 70)

        # Summary
        summary = self.get_summary()
        print("\n📊 SUMMARY")
        print("-" * 70)
        for key, value in summary.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        # Common questions
        print("\n❓ MOST COMMON QUESTIONS")
        print("-" * 70)
        common_q = self.get_common_questions(5)
        for i, (question, count) in enumerate(common_q, 1):
            print(f"  {i}. [{count}x] {question[:60]}...")

        # Search stats
        print("\n🔍 SEARCH STATISTICS")
        print("-" * 70)
        search_stats = self.get_search_stats()
        for key, value in search_stats.items():
            if key != "message":
                print(f"  {key.replace('_', ' ').title()}: {value}")

        # Errors
        print("\n❌ ERRORS")
        print("-" * 70)
        error_summary = self.get_error_summary()
        if "message" in error_summary:
            print(f"  {error_summary['message']}")
        else:
            for key, value in error_summary.items():
                if key != "recent_errors":
                    print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\n" + "=" * 70)

    def export_report(self, output_file: str | Path) -> None:
        """
        Export analysis report to JSON file.

        Args:
            output_file: Path to output file
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "log_file": str(self.log_file),
            "summary": self.get_summary(),
            "common_questions": self.get_common_questions(),
            "search_stats": self.get_search_stats(),
            "error_summary": self.get_error_summary(),
        }

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"Report exported to: {output_file}")


def view_logs(log_file: str | Path, last_n: int = 10) -> None:
    """
    View recent log entries.

    Args:
        log_file: Path to log file
        last_n: Number of recent entries to show
    """
    log_file = Path(log_file)

    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return

    logs = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    print(f"\n📜 Last {last_n} log entries from: {log_file}")
    print("=" * 70)

    for log in logs[-last_n:]:
        timestamp = log.get("timestamp", "N/A")
        print(f"\n⏰ {timestamp}")

        if "question" in log:
            print(f"❓ Q: {log['question'][:60]}...")
            print(f"💬 A: {log['answer'][:60]}...")
            if "metadata" in log:
                print(f"📊 {log['metadata']}")

        elif log.get("event_type") == "search":
            print(f"🔍 Search: {log.get('query', 'N/A')}")
            print(
                f"   Type: {log.get('search_type')}, Results: {log.get('results_count')}"
            )

        elif log.get("event_type") == "error":
            print(f"❌ Error: {log.get('error_type')}")
            print(f"   {log.get('error_message')}")

        print("-" * 70)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = "logs/agent_interactions.jsonl"

    analyzer = LogAnalyzer(log_file)
    analyzer.print_report()
