"""AI-powered evaluation system for agent performance assessment."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic_ai import Agent

logger = logging.getLogger(__name__)


class AIJudge:
    """
    AI-powered judge to evaluate agent responses.

    Uses an LLM to assess the quality, accuracy, and relevance of agent answers.
    """

    def __init__(
        self,
        model: str = "openai:gpt-4o-mini",
        evaluation_criteria: dict[str, str] | None = None,
    ):
        """
        Initialize AI Judge.

        Args:
            model: LLM model to use for evaluation
            evaluation_criteria: Custom evaluation criteria
        """
        self.model = model
        self.evaluation_criteria = evaluation_criteria or self._default_criteria()

        # Create evaluation agent
        self.judge = Agent(model=self.model)

        logger.info(f"Initialized AIJudge with model: {model}")

    @staticmethod
    def _default_criteria() -> dict[str, str]:
        """Get default evaluation criteria."""
        return {
            "accuracy": "Is the answer factually correct and accurate?",
            "relevance": "Does the answer directly address the question?",
            "completeness": "Is the answer complete and comprehensive?",
            "clarity": "Is the answer clear and easy to understand?",
            "helpfulness": "Would this answer be helpful to the user?",
        }

    async def evaluate_response(
        self,
        question: str,
        answer: str,
        ground_truth: str | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate an agent response.

        Args:
            question: The question asked
            answer: The agent's answer
            ground_truth: Optional ground truth answer for comparison

        Returns:
            Evaluation results with scores and feedback
        """
        start_time = time.time()

        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(question, answer, ground_truth)

        # Get evaluation from judge
        result = await self.judge.run(prompt)
        evaluation_text = result.output

        # Parse evaluation (expecting JSON format)
        try:
            evaluation = self._parse_evaluation(evaluation_text)
        except Exception as e:
            logger.warning(f"Failed to parse evaluation: {e}")
            evaluation = {"raw_evaluation": evaluation_text}

        # Add metadata
        evaluation["evaluation_time_seconds"] = time.time() - start_time
        evaluation["judge_model"] = self.model
        evaluation["timestamp"] = datetime.now().isoformat()

        return evaluation

    def _build_evaluation_prompt(
        self, question: str, answer: str, ground_truth: str | None
    ) -> str:
        """Build prompt for the AI judge."""
        criteria_text = "\n".join(
            f"- {name}: {desc}" for name, desc in self.evaluation_criteria.items()
        )

        prompt = f"""Evaluate the following agent response based on these criteria:

{criteria_text}

QUESTION:
{question}

AGENT'S ANSWER:
{answer}"""

        if ground_truth:
            prompt += f"""

GROUND TRUTH ANSWER (for reference):
{ground_truth}"""

        prompt += """

Please provide your evaluation in the following JSON format:
{
    "scores": {
        "accuracy": <score 1-10>,
        "relevance": <score 1-10>,
        "completeness": <score 1-10>,
        "clarity": <score 1-10>,
        "helpfulness": <score 1-10>
    },
    "overall_score": <average score 1-10>,
    "feedback": "<detailed feedback>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "improvements": ["<improvement 1>", "<improvement 2>"]
}

Provide only the JSON response, no additional text."""

        return prompt

    def _parse_evaluation(self, evaluation_text: str) -> dict[str, Any]:
        """Parse evaluation text into structured format."""
        # Try to extract JSON from the text
        import re

        json_match = re.search(r"\{.*\}", evaluation_text, re.DOTALL)
        if json_match:
            result: dict[str, Any] = json.loads(json_match.group())
            return result

        # If no JSON found, return raw text
        return {"raw_evaluation": evaluation_text}

    def evaluate_sync(
        self, question: str, answer: str, ground_truth: str | None = None
    ) -> dict[str, Any]:
        """Synchronous wrapper for evaluate_response."""
        import asyncio

        return asyncio.run(self.evaluate_response(question, answer, ground_truth))


class PerformanceMetrics:
    """
    Track and calculate agent performance metrics.

    Metrics include:
    - Average scores
    - Response time
    - Success rate
    - Quality distribution
    """

    def __init__(self) -> None:
        """Initialize metrics tracker."""
        self.evaluations: list[dict[str, Any]] = []
        self.start_time = datetime.now()

    def add_evaluation(self, evaluation: dict[str, Any]) -> None:
        """Add an evaluation result."""
        self.evaluations.append(evaluation)

    def get_metrics(self) -> dict[str, Any]:
        """
        Calculate performance metrics.

        Returns:
            Dictionary with calculated metrics
        """
        if not self.evaluations:
            return {"message": "No evaluations yet"}

        # Extract scores
        overall_scores = []
        category_scores: dict[str, list[float]] = {}

        for eval_result in self.evaluations:
            if "overall_score" in eval_result:
                overall_scores.append(eval_result["overall_score"])

            if "scores" in eval_result:
                for category, score in eval_result["scores"].items():
                    if category not in category_scores:
                        category_scores[category] = []
                    category_scores[category].append(score)

        # Calculate averages
        metrics = {
            "total_evaluations": len(self.evaluations),
            "average_overall_score": (
                round(sum(overall_scores) / len(overall_scores), 2)
                if overall_scores
                else 0
            ),
            "category_averages": {
                category: round(sum(scores) / len(scores), 2)
                for category, scores in category_scores.items()
            },
            "score_distribution": self._score_distribution(overall_scores),
            "runtime_seconds": (datetime.now() - self.start_time).total_seconds(),
        }

        return metrics

    def _score_distribution(self, scores: list[float]) -> dict[str, int]:
        """Calculate score distribution."""
        if not scores:
            return {}

        distribution = {
            "excellent (9-10)": sum(1 for s in scores if s >= 9),
            "good (7-8)": sum(1 for s in scores if 7 <= s < 9),
            "fair (5-6)": sum(1 for s in scores if 5 <= s < 7),
            "poor (<5)": sum(1 for s in scores if s < 5),
        }

        return distribution

    def export_metrics(self, filepath: str | Path) -> None:
        """Export metrics to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metrics": self.get_metrics(),
            "evaluations": self.evaluations,
            "generated_at": datetime.now().isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported metrics to {filepath}")

    def print_summary(self) -> None:
        """Print metrics summary."""
        metrics = self.get_metrics()

        print("\n" + "=" * 70)
        print("AGENT PERFORMANCE METRICS")
        print("=" * 70)

        print("\n📊 Overall Performance")
        print(f"   Total Evaluations: {metrics.get('total_evaluations', 0)}")
        print(f"   Average Score: {metrics.get('average_overall_score', 0):.2f}/10")

        if "category_averages" in metrics:
            print("\n📈 Category Scores")
            for category, score in metrics["category_averages"].items():
                print(f"   {category.capitalize()}: {score:.2f}/10")

        if "score_distribution" in metrics:
            print("\n📉 Score Distribution")
            for range_name, count in metrics["score_distribution"].items():
                print(f"   {range_name}: {count}")

        print("\n" + "=" * 70)


class TestDataGenerator:
    """
    Generate test questions and ground truth answers.

    Uses LLM to create realistic test scenarios.
    """

    def __init__(self, model: str = "openai:gpt-4o-mini"):
        """Initialize test data generator."""
        self.model = model
        self.generator = Agent(model=self.model)
        logger.info(f"Initialized TestDataGenerator with model: {model}")

    async def generate_test_set(
        self,
        context: str,
        num_questions: int = 10,
        difficulty_levels: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """
        Generate test questions from context.

        Args:
            context: Source context for generating questions
            num_questions: Number of questions to generate
            difficulty_levels: List of difficulty levels (easy, medium, hard)

        Returns:
            List of test cases with questions and ground truth answers
        """
        difficulty_levels = difficulty_levels or ["easy", "medium", "hard"]

        prompt = f"""Based on the following context, generate {num_questions} test questions
with ground truth answers. Include a mix of difficulty levels: {', '.join(difficulty_levels)}.

CONTEXT:
{context[:2000]}

Generate questions that test:
- Factual recall
- Understanding of concepts
- Practical application
- Troubleshooting scenarios

Format your response as a JSON array:
[
    {{
        "question": "<question text>",
        "ground_truth": "<correct answer>",
        "difficulty": "<easy/medium/hard>",
        "category": "<category name>"
    }},
    ...
]

Provide only the JSON array, no additional text."""

        result = await self.generator.run(prompt)
        response_text = result.output

        # Parse JSON response
        try:
            test_cases = self._parse_test_cases(response_text)
            logger.info(f"Generated {len(test_cases)} test cases")
            return test_cases
        except Exception as e:
            logger.error(f"Failed to generate test cases: {e}")
            return []

    def _parse_test_cases(self, response_text: str) -> list[dict[str, str]]:
        """Parse test cases from response."""
        import re

        # Try to extract JSON array
        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if json_match:
            result: list[dict[str, str]] = json.loads(json_match.group())
            return result

        raise ValueError("No JSON array found in response")

    def generate_sync(
        self,
        context: str,
        num_questions: int = 10,
        difficulty_levels: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Synchronous wrapper for generate_test_set."""
        import asyncio

        return asyncio.run(
            self.generate_test_set(context, num_questions, difficulty_levels)
        )

    def save_test_set(
        self, test_cases: list[dict[str, str]], filepath: str | Path
    ) -> None:
        """Save test set to file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "test_cases": test_cases,
            "generated_at": datetime.now().isoformat(),
            "total_questions": len(test_cases),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(test_cases)} test cases to {filepath}")


def create_ai_judge(model: str = "openai:gpt-4o-mini") -> AIJudge:
    """Create an AI judge with default settings."""
    return AIJudge(model=model)


def create_test_generator(model: str = "openai:gpt-4o-mini") -> TestDataGenerator:
    """Create a test data generator with default settings."""
    return TestDataGenerator(model=model)
