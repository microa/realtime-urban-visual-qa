# Examples

This directory contains example scripts demonstrating how to use the Realtime Urban Visual QA system.

## Available Examples

### 1. `basic_usage.py`
Basic usage examples including:
- Single city weather query
- Traffic/crowd inquiries
- Multi-city comparison
- Chinese language support
- Direct camera image capture

**Run**:
```bash
python examples/basic_usage.py
```

### 2. `evaluate_cities.py`
Comprehensive city coverage evaluation script that tests camera availability across 36 global cities.

**Run**:
```bash
python examples/evaluate_cities.py
```

**Output**: Generates `evaluation_results_YYYYMMDD_HHMMSS.json` with detailed results.

## Quick Start

```python
from environment_qa import EarthCamQA

# Initialize the system
qa = EarthCamQA()

# Ask a question
qa.answer_question("What's the weather in Paris?")
```

## Note

Make sure you have:
1. Installed all dependencies: `pip install -r requirements.txt`
2. Installed Playwright browsers: `playwright install chromium`
3. Set your API key in `environment_qa.py`
