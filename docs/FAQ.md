# Frequently Asked Questions (FAQ)

## General Questions

### What is this project?
A real-time urban environmental question-answering system that uses live camera streams from cities worldwide to answer questions about weather, traffic, air quality, and crowds using vision-language AI models.

### Which AI models does it use?
- **Vision Model**: [Qwen2.5-VL-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct) (72 billion parameters) - Analyzes images for weather, traffic, crowds
- **Text Model**: Qwen2.5-7B-Instruct (7 billion parameters) - Handles intent recognition, planning, translation
- **API Provider**: [SiliconFlow](https://siliconflow.cn) - Provides inference API (free tier available)

### Why SiliconFlow API?
- Free tier available (1M tokens/month)
- Hosts Qwen models optimized for Chinese + English
- Low latency for Asian users
- No credit card required for signup

---

## Technical Questions

### What streaming technologies are supported?

1. **HLS Streams** (`.m3u8` playlists)
   - Traditional EarthCam format
   - Directly parses M3U8 → TS segments → OpenCV frames
   - Currently rare (format being phased out)

2. **YouTube Embeds** (iframe detection)
   - Most common (83.3% of successful cities)
   - Extracts video ID from iframe → Fetches thumbnail via `img.youtube.com`
   - Examples: Paris, New York, Chicago

3. **EarthCamTV Iframes** (JavaScript required)
   - Dynamic content requiring browser execution
   - Uses Playwright to render page → Captures network requests
   - Examples: Rio de Janeiro, Miami (alt URL)
   - Currently 16.7% of successful cities

### Why such low success rate (33.3%)?

Geographic and commercial barriers:

- **North America**: 85.7% ✅ (free public YouTube streams)
- **Europe**: 57.1% ✅ (mostly free access)
- **Asia**: 0% ❌ (subscription walls - Tokyo, Singapore require paid EarthCam Network)
- **Oceania**: 0% ❌ (subscription walls - Sydney, Melbourne)
- **South America**: 16.7% ⚠️ (mixed - Rio works, others paywalled)
- **Africa**: 0% ❌ (no camera coverage)

**Finding**: 25% of cities require paid subscriptions, 62.5% have no cameras at all.

### Can I add more cities?

Yes! Add to `known_cameras` dict in `environment_qa.py`:

```python
known_cameras = {
    "yourcity": [
        "https://www.earthcam.com/world/country/yourcity/",
    ],
}
```

Then test:
```bash
python environment_qa.py "What's the weather in YourCity?"
```

### Why use Playwright instead of requests?

Some websites (like EarthCamTV) load video streams dynamically via JavaScript:
- **requests**: Gets static HTML (no video URLs)
- **Playwright**: Executes JS → Intercepts network requests → Captures `.m3u8` URLs

Trade-off: Playwright is slower (3-5s) but unlocks 2 additional cities.

---

## Usage Questions

### What questions can I ask?

**Weather**:
- "What's the weather in London?"
- "Is it raining in Paris?"
- "How's visibility in New York?"

**Traffic**:
- "Is Times Square crowded?"
- "How's traffic in Chicago?"
- "Is the road busy in Miami?"

**Air Quality**:
- "How's air quality in London Tower Bridge?"
- "Can I see clearly in Paris?" (visibility = air quality proxy)

**Comparisons**:
- "Compare weather between London and Paris"
- "Which city has better air quality: New York or LA?"

### Does it support Chinese?

Yes! Both input and output:
```bash
python environment_qa.py "How is the weather in Paris now?"
# Answer: "Based on real-time camera images..."

python environment_qa.py "Compare Beijing and Tokyo weather"
# Answer: "Based on real-time camera images..."
```

Language detection is automatic.

### How accurate is the analysis?

**Strengths**:
- Weather conditions (sunny/cloudy/rainy): ~85-90% accurate
- Traffic flow (busy/moderate/light): ~75-80% accurate
- Visibility/air quality inference: ~70-75% accurate

**Limitations**:
- Cannot measure exact temperature (°C/°F)
- Cannot detect noise levels (audio not available)
- Crowd density affected by camera angle
- Night images have reduced accuracy

### Can I use it for research?

Yes! This project was developed for the iEMSs 2026 conference. Potential research areas:

1. **Smart City Infrastructure**: Quantify global digital divide (developed vs developing regions)
2. **Platform Migration**: Document EarthCam's shift from HLS → YouTube (2020-2025)
3. **Commercialization Impact**: Measure how subscription walls affect public data access
4. **Multimodal AI**: Benchmark vision-language models on real-world urban scenarios

Cite as:
```bibtex
@software{realtime_urban_visual_qa,
  title={Realtime Urban Visual QA: Multi-Platform Video Stream System},
  author={Your Name},
  year={2025},
  url={https://github.com/microa/realtime-urban-visual-qa}
}
```

---

## Troubleshooting

### "No stream found" error

**Possible causes**:
1. City requires subscription (Tokyo, Sydney, etc.)
2. Camera offline or removed
3. Network/firewall issues

**Solutions**:
- Try alternative landmarks: `"Times Square New York"` instead of just `"New York"`
- Check if city is in supported list (see EVALUATION_RESULTS.md)
- Verify internet connection

### "Playwright timeout" error

**Cause**: JavaScript execution taking too long (>15s default)

**Solutions**:
```python
# In environment_qa.py, increase timeout:
browser_result = self.extract_hls_url_with_browser(page_url, timeout=30)
```

### "API error" or rate limit

**Cause**: SiliconFlow API key issue or quota exceeded

**Solutions**:
1. Check API key is set correctly
2. Verify free tier quota (1M tokens/month)
3. Wait and retry (rate limits reset monthly)

### Image quality is poor

**Cause**: Using medium/low quality YouTube thumbnails

**Solution**: YouTube API priority order is already optimized (maxresdefault → hqdefault → mqdefault), but some live streams only provide lower resolutions.

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Adding new cities
- Supporting new streaming platforms
- Improving AI model prompts
- Translating documentation

---

## More Questions?

Open an issue on GitHub: https://github.com/microa/realtime-urban-visual-qa/issues
