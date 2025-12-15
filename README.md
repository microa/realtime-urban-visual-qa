# Realtime Urban Visual QA

> A Multi-Platform Video Stream System for Real-Time Urban Environmental Question Answering

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Playwright](https://img.shields.io/badge/Playwright-1.56.0-orange.svg)](https://playwright.dev/)

**Live Camera Analysis** + **Vision-Language Models** + **Multi-Platform Support**

Access real-time urban environments from 36 global cities using EarthCam, YouTube, and custom stream extraction with JavaScript execution support.

---

## 🌟 Key Features

- 🎥 **Multi-Platform Support**: HLS streams, YouTube embeds, EarthCamTV iframes
- 🤖 **Vision-Language AI**: Powered by [Qwen2.5-VL-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct) (72B parameters) for advanced image understanding
- 🧠 **Text Intelligence**: Qwen2.5-7B-Instruct for intent recognition and planning
- 🌍 **Global Coverage**: 36 cities across 6 continents
- 🚀 **JavaScript Execution**: Playwright-based dynamic content extraction
- 💬 **Natural Language QA**: Ask questions in English or Chinese
- 📊 **Temporal RAG**: Historical data comparison and trend analysis

---

## 🧪 AI Models

| Component | Model | Parameters | Purpose |
|-----------|-------|------------|---------|
| **Vision Analysis** | [Qwen2.5-VL-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct) | 72B | Image understanding, weather/traffic/crowd detection |
| **Text Processing** | Qwen2.5-7B-Instruct | 7B | Intent recognition, planning, translation |
| **API Provider** | [SiliconFlow](https://siliconflow.cn) | - | Inference API (free tier available) |

---

## 📊 Performance Metrics

### Global Coverage

**12/36 cities successfully accessible (33.3% success rate)**

| Region | Success Rate | Working Cities |
|--------|--------------|----------------|
| 🌎 **North America** | **85.7%** (6/7) | New York, Miami, Las Vegas, Chicago, San Francisco, Washington DC |
| 🌍 **Europe** | **57.1%** (4/7) | London, Paris, Amsterdam, Dublin |
| 🌎 **South America** | 33.3% (2/6) | Rio de Janeiro |
| 🌏 **Asia** | 0% (0/12) | Blocked by subscription walls |
| 🌏 **Oceania** | 0% (0/4) | Blocked by subscription walls |
| 🌍 **Africa** | 0% (0/2) | Limited coverage |

**Technology Stack**: Multi-platform support including HLS streams, YouTube embeds, and JavaScript-enabled dynamic content extraction (Playwright).

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- API Key from [SiliconFlow](https://siliconflow.cn) (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/microa/realtime-urban-visual-qa.git
cd realtime-urban-visual-qa

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Configuration

Set your API key as an environment variable:

```bash
export SILICONFLOW_API_KEY="your_api_key_here"
```

Or create a `.env` file (optional).

### Basic Usage

```bash
# Ask about current conditions
python environment_qa.py "What's the weather in London?"

# Traffic inquiry
python environment_qa.py "Is Times Square crowded right now?"

# Multi-city comparison
python environment_qa.py "Compare air quality between Paris and New York"
```

---

## 📖 Example Queries

### Weather & Environment
```python
"What's the air quality around London Tower Bridge?"
"Is it raining in Paris right now?"
"How's the visibility in New York?"
```

### Traffic & Crowds
```python
"Is Times Square crowded?"
"How's the traffic in Chicago?"
"Is it busy at Miami Beach?"
```

### Multi-City Analysis
```python
"Compare weather between London and Paris"
"Which city has better air quality: New York or San Francisco?"
```

**More examples**: See [docs/FAQ.md](docs/FAQ.md) for detailed usage patterns and troubleshooting.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 User Query (NLU)                    │
│          "What's the weather in London?"            │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│           Intent Analysis (Qwen2.5-7B)              │
│  • City extraction  • Language detection            │
│  • Query type       • Execution planning            │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Multi-Platform Scraper                 │
│  ┌──────────────┬───────────────┬─────────────────┐ │
│  │ HLS Streams  │ YouTube API   │ JavaScript (PW) │ │
│  │ (Native)     │ (Embed)       │ (EarthCamTV)    │ │
│  └──────────────┴───────────────┴─────────────────┘ │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          Frame Extraction & Processing              │
│  • M3U8 → TS → OpenCV  • YouTube thumbnails         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│      Vision Analysis (Qwen2.5-VL-72B)               │
│  • Weather detection  • Traffic analysis            │
│  • Air quality        • Crowd density               │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          Response Generation (LLM)                  │
│  • Multi-language  • Contextual reasoning           │
└─────────────────────────────────────────────────────┘
```

---

## 🔬 Technical Highlights

### 1. Multi-Platform Video Extraction

Supports multiple streaming technologies:
- **HLS Streams**: Native M3U8 playlist parsing
- **YouTube Embeds**: Direct iframe detection and thumbnail extraction
- **JavaScript-Required Content**: Playwright browser automation for dynamic streams

### 2. Vision-Language Understanding

**Model**: Qwen2.5-VL-72B-Instruct (72B parameters)

**Capabilities**:
- Weather condition recognition (sunny/cloudy/rainy)
- Air quality inference from visibility
- Traffic flow estimation
- Crowd density analysis

### 3. Temporal RAG System

**Features**:
- Historical data storage (ChromaDB + SQLite)
- Time-aware retrieval
- Trend analysis and comparison

---

## 📁 Project Structure

```
realtime-urban-visual-qa/
├── environment_qa.py              # Main QA system
├── temporal_rag_qa.py             # Temporal RAG system
├── requirements.txt               # Dependencies
├── EVALUATION_RESULTS.md          # 36-city evaluation report
├── docs/FAQ.md                    # Frequently asked questions
├── examples/                      # Usage examples
└── README.md                      # This file
```

---

## 🔧 Advanced Usage

### Custom City Cameras

Add your own camera URLs to `known_cameras` dict in `environment_qa.py`:

```python
known_cameras = {
    "yourcity": [
        "https://www.earthcam.com/world/country/yourcity/",
    ],
}
```

### Temporal Analysis

```bash
# Compare historical data
python temporal_rag_qa.py "How has London's air quality changed this month?"
```

### Batch Evaluation

```bash
# Evaluate multiple cities
python examples/evaluate_cities.py
```

---

## 📊 Research Findings

### Geographic Digital Divide

Our evaluation reveals significant inequality in smart city infrastructure:

- **Developed Regions** (NA/EU): 57-86% free public access
- **Developing Regions** (Asia/Africa): 0-17% often behind paywalls

### Technology Stack Migration

- **2020-2023**: Native HLS streams dominant
- **2024-2025**: YouTube embeds (83.3% of successful cities)
- **Future**: EarthCamTV iframes require JavaScript

### Commercial Barriers

- 25% of cities blocked by subscription walls
- Premium cities (Tokyo, Sydney) require EarthCam Network membership
- Public data accessibility decreasing

---

## 🛠️ Troubleshooting

### Common Issues

**1. "No stream found"**
- City may require subscription
- Try alternative landmarks: `python environment_qa.py "Times Square New York"`

**2. "Playwright timeout"**
- Increase timeout in `extract_hls_url_with_browser()`
- Check network connection

**3. "API error"**
- Verify SiliconFlow API key
- Check rate limits (free tier: 1M tokens/month)

---

## 📈 Performance Tips

1. **Caching**: Reuse captured images within 5 minutes
2. **Parallel Queries**: Avoid simultaneous requests (rate limit)
3. **Image Quality**: Use `maxresdefault.jpg` for YouTube (better analysis)

---

## 🤝 Contributing

Contributions welcome! Areas of interest:

- [ ] Add more city camera sources
- [ ] Support additional streaming platforms
- [ ] Improve air quality inference models
- [ ] Multi-language documentation

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **Paper**: iEMSs 2026 Conference Submission
- **Model**: [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL)
- **API Provider**: [SiliconFlow](https://siliconflow.cn)
- **Data Source**: [EarthCam](https://www.earthcam.com)

---

## 📧 Contact

For questions or collaboration:
- GitHub Issues: [Create an issue](https://github.com/microa/realtime-urban-visual-qa/issues)
- Email: [Your contact email]

---

## 🙏 Acknowledgments

- EarthCam for providing public camera streams
- SiliconFlow for VLM API access
- Playwright team for browser automation
- Qwen team for open-source models

---

**Star ⭐ this repo if you find it useful!**

---

<div align="center">
<sub>Built with ❤️ for smart city research • Last updated: November 2025</sub>
</div>
