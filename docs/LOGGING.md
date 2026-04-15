# Logging System Documentation

## Overview

The repo-sage logging system provides comprehensive tracking of AI agent interactions, search operations, performance metrics, and errors. It's designed for production use with structured logging, conversation history, and analytics.

## Features

- 📝 **Interaction Logging** - Track questions and answers
- 🔍 **Search Tracking** - Log all search operations
- ⏱️ **Performance Metrics** - Response times, token usage
- 💬 **Conversation History** - Maintain conversation context
- ❌ **Error Tracking** - Log and analyze errors
- 📊 **Analytics** - Generate reports and insights
- 📁 **JSON Lines Format** - Easy to parse and process

## Quick Start

### Basic Usage

```python
from repo_sage import RepoAgent, SearchEngine

# Create agent with logging enabled (default)
agent = RepoAgent(search_engine, enable_logging=True)

# Ask questions - automatically logged
answer = agent.ask("How do I install this?")

# Get session stats
stats = agent.get_session_stats()
print(stats)
```

### View Logs

```python
from repo_sage import view_logs

# View recent log entries
view_logs("logs/agent_interactions.jsonl", last_n=10)
```

### Analyze Logs

```python
from repo_sage import LogAnalyzer

# Create analyzer
analyzer = LogAnalyzer("logs/agent_interactions.jsonl")

# Print comprehensive report
analyzer.print_report()

# Export report to JSON
analyzer.export_report("reports/analysis.json")
```

## Components

### 1. AgentInteractionLogger

Logs agent interactions and events to JSON Lines format.

```python
from repo_sage.logging_system import AgentInteractionLogger

# Create logger
logger = AgentInteractionLogger("logs/my_agent.jsonl")

# Log interaction
logger.log_interaction(
    question="How do I install?",
    answer="Run: pip install...",
    metadata={"response_time_seconds": 2.5}
)

# Log search
logger.log_search(
    query="installation",
    search_type="hybrid",
    results_count=5,
    top_score=0.95,
    response_time=0.15
)

# Log error
logger.log_error(
    error_type="APIError",
    error_message="Rate limit exceeded",
    context={"retry_after": 60}
)

# Log performance
logger.log_performance(
    operation="indexing",
    duration_seconds=5.2,
    metrics={"documents": 1000}
)
```

### 2. ConversationTracker

Maintains conversation history and context.

```python
from repo_sage.logging_system import ConversationTracker

# Create tracker
tracker = ConversationTracker(max_history=50)

# Add interactions
tracker.add_interaction("Q1", "A1")
tracker.add_interaction("Q2", "A2")

# Get history
history = tracker.get_history(last_n=5)

# Get context summary
summary = tracker.get_context_summary()

# Export conversation
tracker.export_to_file("conversations/session_001.json")
```

### 3. LogAnalyzer

Analyze logs and generate insights.

```python
from repo_sage.log_analyzer import LogAnalyzer

# Load logs
analyzer = LogAnalyzer("logs/agent_interactions.jsonl")

# Get summary statistics
summary = analyzer.get_summary()
# {
#     "total_logs": 150,
#     "interactions": 100,
#     "searches": 300,
#     "errors": 2,
#     "avg_response_time_seconds": 2.5
# }

# Get common questions
common = analyzer.get_common_questions(top_n=10)
# [("How do I install?", 25), ...]

# Get search statistics
search_stats = analyzer.get_search_stats()
# {
#     "total_searches": 300,
#     "search_types": {"hybrid": 150, "vector": 100, "text": 50},
#     "avg_results_per_search": 5.2
# }

# Get error summary
errors = analyzer.get_error_summary()
```

## Integration with Agent

### Enable Logging (Default)

```python
from repo_sage import RepoAgent, SearchEngine

engine = SearchEngine()
engine.fit(documents)

# Logging enabled by default
agent = RepoAgent(engine, enable_logging=True)
```

### Custom Log File

```python
agent = RepoAgent(
    engine,
    enable_logging=True,
    log_file="logs/custom_agent.jsonl"
)
```

### Disable Logging

```python
agent = RepoAgent(engine, enable_logging=False)
```

### Access Conversation History

```python
# Get recent history
history = agent.get_conversation_history(last_n=5)

for interaction in history:
    print(f"Q: {interaction['question']}")
    print(f"A: {interaction['answer']}")
    print(f"Time: {interaction['metadata']['response_time_seconds']}s")
```

### Export Conversation

```python
# Export current conversation
agent.export_conversation("conversations/session_001.json")
```

## Log Format

### Interaction Log

```json
{
  "timestamp": "2026-04-15T10:30:45.123456",
  "session_id": "20260415_103045",
  "interaction_id": 1,
  "question": "How do I install this project?",
  "answer": "Run: pip install my-project",
  "metadata": {
    "model": "openai:gpt-4o-mini",
    "response_time_seconds": 2.5,
    "answer_length": 156
  }
}
```

### Search Log

```json
{
  "timestamp": "2026-04-15T10:30:47.123456",
  "session_id": "20260415_103045",
  "event_type": "search",
  "query": "installation guide",
  "search_type": "hybrid",
  "results_count": 5,
  "top_score": 0.95,
  "response_time_seconds": 0.15
}
```

### Error Log

```json
{
  "timestamp": "2026-04-15T10:30:50.123456",
  "session_id": "20260415_103045",
  "event_type": "error",
  "error_type": "APIError",
  "error_message": "Rate limit exceeded",
  "context": {
    "question": "How does this work?",
    "retry_after": 60
  }
}
```

## Analytics Examples

### Most Asked Questions

```python
analyzer = LogAnalyzer("logs/agent_interactions.jsonl")
common_questions = analyzer.get_common_questions(top_n=10)

for question, count in common_questions:
    print(f"{count}x: {question}")
```

### Response Time Analysis

```python
summary = analyzer.get_summary()
avg_time = summary["avg_response_time_seconds"]
print(f"Average response time: {avg_time}s")
```

### Search Patterns

```python
search_stats = analyzer.get_search_stats()
print(f"Total searches: {search_stats['total_searches']}")
print(f"Search types: {search_stats['search_types']}")
print(f"Avg results: {search_stats['avg_results_per_search']}")
```

### Error Analysis

```python
error_summary = analyzer.get_error_summary()
print(f"Total errors: {error_summary['total_errors']}")
print(f"Error types: {error_summary['error_types']}")
```

## Command Line Tools

### View Recent Logs

```bash
python -c "from repo_sage import view_logs; view_logs('logs/agent_interactions.jsonl', last_n=10)"
```

### Generate Report

```bash
python -m repo_sage.log_analyzer logs/agent_interactions.jsonl
```

## Production Best Practices

### 1. Log Rotation

```python
from logging.handlers import RotatingFileHandler
import logging

# Set up log rotation
handler = RotatingFileHandler(
    "logs/agent.jsonl",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### 2. Structured Logging

All logs are in JSON Lines format for easy parsing:

```bash
# Parse with jq
cat logs/agent_interactions.jsonl | jq '.question'

# Filter errors
cat logs/agent_interactions.jsonl | jq 'select(.event_type == "error")'

# Get average response time
cat logs/agent_interactions.jsonl | jq '[.metadata.response_time_seconds] | add/length'
```

### 3. Monitoring

```python
# Monitor error rate
analyzer = LogAnalyzer("logs/agent_interactions.jsonl")
summary = analyzer.get_summary()

error_rate = summary["errors"] / summary["total_logs"]
if error_rate > 0.05:  # More than 5% errors
    alert("High error rate detected!")
```

### 4. Performance Tracking

```python
# Track performance over time
analyzer = LogAnalyzer("logs/agent_interactions.jsonl")
interactions = analyzer.get_interactions()

for interaction in interactions[-10:]:
    rt = interaction["metadata"].get("response_time_seconds", 0)
    if rt > 10:  # Slow responses
        print(f"Slow response: {rt}s for: {interaction['question']}")
```

## File Structure

```
logs/
├── agent_interactions.jsonl    # Main log file
└── conversations/
    ├── session_001.json        # Exported conversations
    └── session_002.json

reports/
└── analysis_report.json        # Analysis reports
```

## Examples

See `examples_logging.py` for complete examples:

```bash
python examples_logging.py
```

## Testing

```bash
# Run logging tests
pytest tests/test_logging.py -v
```

## Troubleshooting

### Logs Not Being Written

Check:
1. Logging is enabled: `enable_logging=True`
2. Log directory exists and is writable
3. Check permissions on log file

### Cannot Read Logs

```python
# Check if file exists
from pathlib import Path
log_file = Path("logs/agent_interactions.jsonl")
print(f"Exists: {log_file.exists()}")
print(f"Size: {log_file.stat().st_size if log_file.exists() else 0}")
```

### JSON Decode Errors

```python
# Validate JSON Lines format
with open("logs/agent_interactions.jsonl", "r") as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Error on line {i}: {e}")
```

## API Reference

### AgentInteractionLogger

- `log_interaction(question, answer, metadata)` - Log Q&A interaction
- `log_search(query, search_type, results_count, ...)` - Log search
- `log_error(error_type, error_message, context)` - Log error
- `log_performance(operation, duration, metrics)` - Log performance
- `get_session_stats()` - Get session statistics

### ConversationTracker

- `add_interaction(question, answer, metadata)` - Add to history
- `get_history(last_n)` - Get conversation history
- `get_context_summary()` - Get context summary
- `clear_history()` - Clear history
- `export_to_file(filepath)` - Export to JSON

### LogAnalyzer

- `get_interactions()` - Get all interactions
- `get_searches()` - Get all searches
- `get_errors()` - Get all errors
- `get_summary()` - Get summary statistics
- `get_common_questions(top_n)` - Get most asked questions
- `get_search_stats()` - Get search statistics
- `get_error_summary()` - Get error summary
- `print_report()` - Print comprehensive report
- `export_report(output_file)` - Export report to JSON

## Summary

The logging system provides:

✅ **Automatic Tracking** - No manual logging needed
✅ **Comprehensive Data** - Questions, answers, searches, errors
✅ **Easy Analysis** - Built-in analytics and reporting
✅ **Production Ready** - Structured logs, error handling
✅ **Conversation Context** - Full history tracking
✅ **Performance Metrics** - Response times and usage stats

Perfect for monitoring, debugging, and improving your AI agent!
