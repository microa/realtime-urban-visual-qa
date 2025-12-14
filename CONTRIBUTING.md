# Contributing to Realtime Urban Visual QA

We welcome contributions! Here's how you can help improve the project.

## How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs
- Include Python version, OS, and error messages
- Provide steps to reproduce the issue

### Adding New Cities
1. Find camera URLs on [EarthCam](https://www.earthcam.com)
2. Add to `known_cameras` dict in `environment_qa.py`:
```python
"yourcity": [
    "https://www.earthcam.com/world/country/yourcity/",
],
```
3. Test with: `python environment_qa.py "What's the weather in YourCity?"`

### Adding New Streaming Platforms
Current supported platforms:
- HLS streams (.m3u8)
- YouTube embeds
- EarthCamTV iframes (via Playwright)

To add a new platform:
1. Add detection logic in `extract_hls_url()`
2. Implement extraction function
3. Add tests
4. Update documentation

### Code Style
- Follow PEP 8
- Add docstrings to functions
- Include type hints where appropriate
- Write descriptive commit messages

### Testing
Before submitting:
```bash
# Test basic functionality
python examples/basic_usage.py

# Test new cities
python examples/evaluate_cities.py
```

### Pull Request Process
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -m "Add: your feature description"`
6. Push: `git push origin feature/your-feature`
7. Create a Pull Request on GitHub

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/realtime-urban-visual-qa.git
cd realtime-urban-visual-qa

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt  # If available
```

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Questions?

Open an issue or start a discussion on GitHub.

Thank you for contributing! 🎉
