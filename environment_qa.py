#!/usr/bin/env python3
"""
Realtime Urban Visual QA System
Intelligent question-answering system based on real-time camera images

Features:
- Multi-language input support (Chinese, English, etc.)
- Intelligent intent recognition
- Automatic city camera discovery and capture
- Multimodal visual question answering

AI Models:
- Vision: Qwen2.5-VL-72B-Instruct (72B params) - Image understanding
- Text: Qwen2.5-7B-Instruct (7B params) - Intent recognition & planning
- API: SiliconFlow inference API (https://siliconflow.cn)

Technology Stack:
- Video: HLS streams, YouTube embeds, EarthCamTV iframes
- Browser: Playwright for JavaScript execution
- Vector DB: ChromaDB for temporal RAG
"""

import requests
import re
import m3u8
import cv2
import numpy as np
from datetime import datetime
import time
from urllib.parse import urljoin
import json
import base64
import os
from playwright.sync_api import sync_playwright
import asyncio

# SiliconFlow API Configuration
API_KEY = os.getenv("SILICONFLOW_API_KEY")
API_BASE = "https://api.siliconflow.cn/v1"

# LLM Model Configuration
TEXT_MODEL = "Qwen/Qwen2.5-7B-Instruct"  # Text analysis model
VISION_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"  # Visual QA model (supports image understanding)

class EarthCamQA:
    """Main class for the Environmental QA System"""
    
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_local_time_from_llm(self, city):
        """Get city's current local time using LLM"""
        utc_time = datetime.now(datetime.UTC if hasattr(datetime, 'UTC') else None)
        if utc_time.tzinfo is None:
            # Python < 3.11 fallback
            from datetime import timezone
            utc_time = datetime.now(timezone.utc)
        
        utc_time_str = utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        prompt = f"""Current UTC time is: {utc_time_str}

What is the current local time in {city}? 

Please return ONLY a JSON object in this exact format:
{{
    "local_time": "YYYY-MM-DD HH:MM:SS",
    "timezone": "timezone name (e.g., EST, GMT, CET)"
}}

No explanations, just the JSON."""
        
        response = self.call_llm_text(prompt, temperature=0.1)
        
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    time_info = json.loads(json_match.group())
                    return time_info.get('local_time'), time_info.get('timezone')
            except:
                pass
        
        # If fails, return UTC time for fallback
        return utc_time_str.replace(' UTC', ''), 'UTC'
        
    def call_llm_text(self, prompt, system_prompt=None, temperature=0.7):
        """Call text LLM"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": TEXT_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=60
            )
            result = response.json()
            
            # Check API error
            if 'error' in result:
                print(f"  ✗ API error: {result['error']}")
                return None
            
            if 'choices' not in result or not result['choices']:
                print(f"  ✗ API response abnormal: {result}")
                return None
            
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"  ✗ LLM call failed: {str(e)}")
            return None
    
    def call_llm_vision(self, image_path, question, image_url=None):
        """Call vision LLM"""
        # Read and encode image
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_data}"
        
        if not image_url:
            return None
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ]
        
        data = {
            "model": VISION_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=90
            )
            result = response.json()
            
            # Print detailed error info
            if 'error' in result:
                print(f"  API error: {result['error']}")
                return None
            
            if 'choices' not in result:
                print(f"  API response abnormal: {result}")
                return None
                
            return result['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            print(f"  ✗ Vision LLM call timeout")
            return None
        except Exception as e:
            print(f"  ✗ Vision LLM call failed: {str(e)}")
            return None
    
    def analyze_user_intent(self, user_query):
        """Analyze user intent - completely delegate toLLMfor judgment and maximum generalization"""
        system_prompt = """You are an intelligent assistant that analyzes whether a user query can be answered using **real-time camera images**.

Core principle: Be GENEROUS in judgment. As long as the query involves ANY aspect of a location's current/real-time state, consider using camera images.

What can be inferred from camera images (non-exhaustive list):
✅ Weather: sunny/cloudy/rainy/snowy (sky, ground wetness)
✅ Air quality: visibility, haze level, sky clarity
✅ Traffic: vehicle flow, congestion level, vehicle types
✅ Crowd density: number of people, crowding level
✅ Environmental conditions: lighting, time of day (day/night), street conditions
✅ Urban activities: festivals, special events, construction
✅ Suitability forsessment: is it good for cycling/running/sightseeing (based on above information)
✅ ANY question that forks "what's happening now" or "current situation"

Only set is_camera_query = false for:
❌ Pure chitchat ("hello", "thank you")
❌ Historical data ("lfort year's weather", "lfort month's traffic")
❌ Knowledge Q&A ("what is PM2.5", "which country is London in")
❌ Completely non-visual questions ("is it noisy", "exact temperature in Celsius")

IMPORTANT: Normalize city names properly:
- "LA" → "Los Angeles"
- "NYC" or "NY" → "New York"
- "SF" → "San Francisco"
- Handle typos and variations
- Return FULL city names for searching

Return JSON format:
{
    "is_camera_query": true/false,
    "city": "FULL city name in English (e.g., Los Angeles, not LA)",
    "country": "Country name in English",
    "query_type": "environmental/weather/traffic/people/general",
    "query_language": "en/zh/other",
    "visual_method": "Brief explanation of how to infer the answer from images",
    "search_keywords": "Keywords for searching EarthCam (use full city name + landmarks if mentioned)"
}

IMPORTANT: 
- Detect the language of the user's query and set query_language accordingly
- Always use FULL city names, not abbreviations"""

        prompt = f"""User input: {user_query}

Example 1:
User: "What's the air quality around London Tower Bridge?"
Answer: {{"is_camera_query": true, "city": "London", "country": "UK", "query_type": "environmental", "query_language": "en", "visual_method": "Infer air quality from visibility, sky clarity, and haze level", "search_keywords": "London Tower Bridge"}}

Example 2:
User: "how's the environment in LA"
Answer: {{"is_camera_query": true, "city": "Los Angeles", "country": "USA", "query_type": "environmental", "query_language": "en", "visual_method": "Infer environmental conditions from visibility, sky clarity, traffic, and weather", "search_keywords": "Los Angeles USA"}}

Example 3:
User: "How is traffic in NYC?"
Answer: {{"is_camera_query": true, "city": "New York", "country": "USA", "query_type": "traffic", "query_language": "zh", "visual_method": "observe traffic flow and road conditions", "search_keywords": "New York Times Square"}}

Example 4:
User: "Are there many people at the Eiffel Tower in Paris now"
Answer: {{"is_camera_query": true, "city": "Paris", "country": "France", "query_type": "people", "query_language": "zh", "visual_method": "observe crowd density", "search_keywords": "Paris Eiffel Tower"}}

Example 5:
User: "What does PM2.5 mean?"
Answer: {{"is_camera_query": false, "query_language": "en"}}

Now analyze the user input above. Return ONLY JSON, no explanations."""
        
        response = self.call_llm_text(prompt, system_prompt, temperature=0.3)
        
        if not response:
            return None
        
        # Extract JSON
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                intent = json.loads(json_match.group())
                return intent
        except:
            pass
        
        return None
    
    def search_earthcam(self, city, country=None):
        """Search for city camerfor on EarthCam"""
        
        # If city name is in Chinese, translate to English first
        if any('\u4e00' <= char <= '\u9fff' for char in city):
            print(f"  ⚠ Detected Chinese city name '{city}'，Translating...")
            translate_prompt = f"""Translate the following city name to English:
City name: {city}

Return only English city name, no other text. For example:
London → London
New York → New York
Los Angeles → Los Angeles
Tokyo → Tokyo

Now translate: {city}"""
            english_city = self.call_llm_text(translate_prompt, temperature=0.1)
            if english_city:
                english_city = english_city.strip().strip('"').strip("'")
                print(f"  ✓ Translation: '{city}' → '{english_city}'")
                city = english_city
        
        # First check if there are known popular city camerfor（including YouTube redirects）
        known_camerfor = {
            "london": [
                "https://www.earthcam.com/world/england/london/abbeyroad/",
                "https://www.earthcam.com/world/england/london/londoneye/",
                "https://www.earthcam.com/world/england/london/trafalgarsquare/",
            ],
            "newyork": [
                "https://www.earthcam.com/usa/newyork/timessquare/",
                "https://www.earthcam.com/usa/newyork/statueofliberty/",
            ],
            "miami": [
                "https://www.earthcam.com/usa/florida/miamibeach/",
                "https://www.earthcam.com/usa/florida/miami/",
            ],
            "lforvegas": [
                "https://www.earthcam.com/usa/nevada/lforvegas/",
            ],
            "chicago": [
                "https://www.earthcam.com/usa/illinois/chicago/",
            ],
            "dublin": [
                "https://www.earthcam.com/world/ireland/dublin/",
            ],
            "amsterdam": [
                "https://www.earthcam.com/world/netherlands/amsterdam/",
            ],
            # Following cities contain YouTube live streams
            "paris": [
                "https://www.earthcam.com/world/france/paris/?cam=eiffeltower",
                "https://www.earthcam.com/world/france/paris/",
            ],
            "tokyo": [
                "https://www.earthcam.com/world/japan/tokyo/?cam=tokyoskytree",
                "https://www.earthcam.com/world/japan/tokyo/",
            ],
            "sydney": [
                "https://www.earthcam.com/world/australia/sydney/",
            ],
            "barcelona": [
                "https://www.earthcam.com/world/spain/barcelona/",
            ],
            "rome": [
                "https://www.earthcam.com/world/italy/rome/",
            ],
            "munich": [
                "https://www.earthcam.com/world/germany/munich/",
            ],
            "dubai": [
                "https://www.earthcam.com/world/unitedarabemirates/dubai/",
            ],
            "singapore": [
                "https://www.earthcam.com/world/singapore/singapore/",
            ],
            "hongkong": [
                "https://www.earthcam.com/world/china/hongkong/",
            ],
            "losangeles": [
                "https://www.earthcam.com/usa/california/losangeles/",
            ],
            "sanfrancisco": [
                "https://www.earthcam.com/usa/california/sanfrancisco/",
            ],
            "boston": [
                "https://www.earthcam.com/usa/mforsachusetts/boston/",
            ],
            "wforhingtondc": [
                "https://www.earthcam.com/usa/dc/",
            ],
            # South American cities (some use EarthCamTV iframe)
            "riodejaneiro": [
                "https://www.earthcam.com/world/brazil/riodejaneiro/",
            ],
        }
        
        city_lower = city.lower().replace(" ", "")
        if city_lower in known_camerfor:
            print(f"  ✓ from known listFound {len(known_camerfor[city_lower])} camerfor")
            return known_camerfor[city_lower]
        
        # Otherwise try searching（Add timeout and error handling）
        print(f"  ⚠ {city} Not in known list, trying online search...")

        search_terms = [
            f"{city} {country}" if country else city,
            city,
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        all_links = []
        
        for search_term in search_terms:
            try:
                search_url = f"https://www.earthcam.com/search/results.php?searchtext={search_term}"
                print(f"  Trying to search: {search_term}")
                
                response = requests.get(search_url, headers=headers, timeout=10)
                html = response.text
                
                # Extract camera links
                camera_links = re.findall(r'href="(https://www\.earthcam\.com/[^"]+/)"', html)
                
                # Deduplicate and filter
                for link in camera_links:
                    if any(skip in link for skip in ['/search/', '/apps/', '/about/', '/content/']):
                        continue
                    if link not in all_links:
                        all_links.append(link)
                
                if all_links:
                    break
                    
            except Exception as e:
                print(f"  ✗ Search failed: {str(e)}")
                continue
        
        if all_links:
            print(f"  ✓ Found {len(all_links)} camerfor")
        
        return all_links[:5]
    
    def extract_hls_url_with_browser(self, page_url, timeout=15):
        """Use browser to execute JavaScript and extract HLS stream URLs - Supports dynamically loaded videos"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Intercept network requests, capture m3u8 files
                captured_m3u8 = []
                captured_youtube = []
                
                def handle_request(request):
                    url = request.url
                    if '.m3u8' in url:
                        captured_m3u8.append(url)
                        print(f"    ✓ Captured m3u8 stream: {url[:80]}...")
                    elif 'youtube.com' in url or 'youtu.be' in url:
                        match = re.search(r'(?:embed/|watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
                        if match:
                            captured_youtube.append(match.group(1))
                
                page.on('request', handle_request)
                
                # Visit page（Lower timeout, fail ffort）
                print(f"    ⏳ Loading page with browser...")
                try:
                    page.goto(page_url, wait_until='domcontentloaded', timeout=timeout*1000)
                    # Wait for network to stabilize
                    page.wait_for_load_state('networkidle', timeout=5000)
                except:
                    # Continue even if timeout, may have already captured stream
                    pass
                
                # Additional wait 2 seconds to ensure video starts loading
                time.sleep(2)
                
                # Check page content
                html = page.content()
                
                browser.close()
                
                # Prioritize returning captured m3u8 stream
                if captured_m3u8:
                    print(f"    ✓ Browser captured HLS stream")
                    return captured_m3u8[0]
                
                # Check YouTube
                if captured_youtube:
                    print(f"    ✓ Browser captured YouTube: {captured_youtube[0]}")
                    return f"YOUTUBE:{captured_youtube[0]}"
                
                # Extract from final HTML
                m3u8_matches = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html)
                if m3u8_matches:
                    print(f"    ✓ Found HLS stream in HTML")
                    return m3u8_matches[0]
                
                # Check YouTube iframe
                youtube_matches = re.findall(r'(?:youtube\.com/embed/|youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', html)
                if youtube_matches:
                    print(f"    ✓ Found YouTube in HTML: {youtube_matches[0]}")
                    return f"YOUTUBE:{youtube_matches[0]}"
                
                print(f"    ✗ Browser did not find video stream")
                return None
                
        except Exception as e:
            print(f"    ✗ Browser extraction failed: {str(e)[:50]}")
            return None
    
    def extract_hls_url(self, page_url):
        """Extract HLS stream URL from camera page - Enhanced version: Support YouTube and other external platformsrmsredirects + JavaScriptdynamically loaded"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Step 1: Try static method first (ffort)
        try:
            response = requests.get(page_url, headers=headers, timeout=15, allow_redirects=True)
            html = response.text
            final_url = response.url
                
                # Detect if redirected to external platform
            if 'youtube.com' in final_url or 'youtu.be' in final_url:
                print(f"    ⚠ Detected YouTube redirect: {final_url}")
                return self.extract_youtube_stream(final_url)
            
            # Prioritize detecting EarthCamTV and other external camera iframes（These are real camerfor）
            hfor_earthcamtv_iframe = False
            iframe_matches = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            for iframe_src in iframe_matches:
                if 'earthcamtv.com' in iframe_src:
                    hfor_earthcamtv_iframe = True
                    print(f"    ⚠ Detected EarthCamTV iframe，Requires JavaScript execution")
                    break
            
            # if found EarthCamTV iframe but static method cannot get stream, use browser
            if hfor_earthcamtv_iframe:
                print(f"    ⏳ Switch to browser mode...")
                browser_result = self.extract_hls_url_with_browser(page_url)
                if browser_result:
                    return browser_result
            
            # Then detect YouTube（May be embedded video, lower priority than real camerfor）
            if 'youtube.com' in html or 'youtu.be' in html:
                # Page-embedded YouTube
                youtube_matches = re.findall(r'(?:youtube\.com/embed/|youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', html)
                if youtube_matches:
                    video_id = youtube_matches[0]
                    print(f"    ⚠ Detected embedded YouTube video: {video_id}")
                    return f"YOUTUBE:{video_id}"
            
            # Detect other iframes
            for iframe_src in iframe_matches:
                if 'youtube.com' in iframe_src or 'youtu.be' in iframe_src:
                    youtube_id = re.search(r'(?:embed/|watch\?v=)([a-zA-Z0-9_-]{11})', iframe_src)
                    if youtube_id:
                        print(f"    ⚠ Detected YouTube in iframe: {youtube_id.group(1)}")
                        return f"YOUTUBE:{youtube_id.group(1)}"
            
            # Method 1: Standard html5_streaming configuration
            domain_match = re.search(r'html5_streamingdomain":"([^"]+)"', html)
            path_match = re.search(r'html5_streampath":"([^"]+)"', html)
            
            if domain_match and path_match:
                domain = domain_match.group(1).replace(r'\/', '/')
                path = path_match.group(1).replace(r'\/', '/')
                hls_url = domain + path
                print(f"    ✓ Found HLS stream (Standard configuration)")
                return hls_url
            
            # Method 2: Search for m3u8 links directly
            m3u8_matches = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html)
            if m3u8_matches:
                hls_url = m3u8_matches[0]
                print(f"    ✓ Found HLS stream (Direct link)")
                return hls_url
            
            # Method 3: Find player configuration
            player_match = re.search(r'"file"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
            if player_match:
                hls_url = player_match.group(1).replace(r'\/', '/')
                print(f"    ✓ Found HLS stream (Player configuration)")
                return hls_url
            
        except Exception as e:
            print(f"    ✗ Static extraction failed: {str(e)[:50]}")
        
        # If static method fails, try browser（As fallback）
        print(f"    ⏳ Static method failed, trying browser mode...")
        return self.extract_hls_url_with_browser(page_url)
    
    def extract_youtube_stream(self, youtube_url):
        """Handle YouTube links - Return special marker for subsequent processing"""
        try:
            # Extract video ID
            video_id = None
            if 'watch?v=' in youtube_url:
                video_id = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', youtube_url)
            elif 'youtu.be/' in youtube_url:
                video_id = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', youtube_url)
            elif 'embed/' in youtube_url:
                video_id = re.search(r'embed/([a-zA-Z0-9_-]{11})', youtube_url)
            
            if video_id:
                print(f"    ✓ Extract YouTube video ID: {video_id.group(1)}")
                return f"YOUTUBE:{video_id.group(1)}"
        except Exception as e:
            print(f"    ✗ Failed to parse YouTube link: {str(e)}")
        
        return None
    
    def get_latest_ts_segment(self, playlist_url):
        """Get latest TS video segment - Enhanced version: Multiple fallbacks"""
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.earthcam.com/'
        }
        
        for attempt in range(2):
            try:
                if attempt > 0:
                    time.sleep(3)
                
                playlist = m3u8.load(playlist_url, headers=headers, timeout=15)
                
                # If mforter playlist, get sub-playlist
                if playlist.is_variant:
                    # Select highest quality stream
                    best_playlist = max(playlist.playlists, key=lambda p: p.stream_info.bandwidth if p.stream_info else 0)
                    variant_url = urljoin(playlist_url, best_playlist.uri)
                    playlist = m3u8.load(variant_url, headers=headers, timeout=15)
                
                if playlist.segments and len(playlist.segments) > 0:
                    # Get lfort segment (most recent)
                    latest_segment = playlist.segments[-1]
                    ts_url = urljoin(playlist.base_uri or playlist_url, latest_segment.uri)
                    print(f"    ✓ Found latest segment ({len(playlist.segments)} available)")
                    return ts_url
                else:
                    print(f"    ✗ No segments in playlist")
                    
            except Exception as e:
                if attempt == 1:
                    print(f"    ✗ Failed to parse playlist: {str(e)[:50]}")
        
        return None
    
    def extract_frame_from_ts(self, ts_url):
        """Extract frame from TS segment"""
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.earthcam.com/'
        }
        
        try:
            response = requests.get(ts_url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                temp_ts = f"/tmp/temp_segment_{int(time.time())}.ts"
                with open(temp_ts, 'wb') as f:
                    f.write(response.content)
                
                cap = cv2.VideoCapture(temp_ts)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    os.remove(temp_ts)
                    
                    if ret:
                        return frame
        except:
            pass
        
        return None
    
    def capture_camera_image(self, camera_url):
        """Capture image from camera URL - Support YouTube and other external platforms"""
        print(f"\n  [1/3] Analyzing camera page...")
        hls_url = self.extract_hls_url(camera_url)
        
        if not hls_url:
            print(f"  ✗ No video stream found")
            return None
        
        # Handle YouTube video
        if isinstance(hls_url, str) and hls_url.startswith('YOUTUBE:'):
            video_id = hls_url.split(':', 1)[1]
            print(f"  ✓ Found YouTube video")
            return self.capture_youtube_thumbnail(video_id)
        
        print(f"  ✓ Found HLS stream")
        
        print(f"  [2/3] Getting latest video segment...")
        ts_url = self.get_latest_ts_segment(hls_url)
        
        if not ts_url:
            print(f"  ✗ Unable to get video segment")
            return None
        
        print(f"  ✓ Get segment URL")
        
        print(f"  [3/3] Download and extract frame...")
        frame = self.extract_frame_from_ts(ts_url)
        
        if frame is not None:
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("captured_images", exist_ok=True)
            filename = f"captured_images/qa_capture_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            
            print(f"  ✓ Saved image: {filename}")
            return filename
        
        print(f"  ✗ Unable to extract frame")
        return None
    
    def capture_youtube_thumbnail(self, video_id):
        """Get thumbnail from YouTube video（Current frame of live stream）"""
        try:
            # YouTube provides multiple quality thumbnails
            # For live streams, hqdefault usually gets newer frames
            thumbnail_urls = [
                f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",  # Highest quality
                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",      # High quality
                f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",      # Medium quality
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            for url in thumbnail_urls:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200 and len(response.content) > 1000:  # Ensure not placeholder image
                        # Save image
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        os.makedirs("captured_images", exist_ok=True)
                        filename = f"captured_images/qa_capture_youtube_{timestamp}.jpg"
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        print(f"  ✓ YouTube image saved: {filename}")
                        return filename
                except:
                    continue
            
            print(f"  ✗ Unable to get YouTube thumbnail")
            
        except Exception as e:
            print(f"  ✗ YouTube processing failed: {str(e)}")
        
        return None
    
    def answer_question(self, user_query):
        """Main function: Answer user question - Let LLM drive the entire process"""
        print("="*70)
        print("Environment QA System")
        print("="*70)
        print(f"\nUser question: {user_query}")
        print("\n" + "-"*70)
        
        # Step 1: Let LLM analyze requirements and create plan
        print("\n[Step 1] Analyzing user needs and creating execution plan...")
        
        plan_prompt = f"""User query: {user_query}

This is an EarthCam-based environmental monitoring system. Our PRIMARY PURPOSE is to answer questions using real-time camera images from cities worldwide.

CORE PRINCIPLE: If the query mentions ANY city/location or forks about ANY observable condition (weather, traffic, people, environment, etc.), we SHOULD use camerfor.

Only set needs_camera=false if:
- Asking definitions/explanations (e.g., "What is PM2.5?", "How does photosynthesis work?")
- Completely unrelated topics (e.g., "Who is Sun Wukong's mother?", "Recipe for pizza")
- Historical facts without visual evidence needed

For MOST queries about cities, current conditions, comparisons, environment → needs_camera=true

Determine:
1. Does this query need real-time camera images? (DEFAULT: YES for city/location/environment queries)
2. Which cities are involved? (normalize: LA→Los Angeles, NYC→New York, Tokyo→Tokyo, Londn→London, etc.)
3. Is this comparing multiple cities?
4. What language to respond in?

Return ONLY JSON:
{{
    "needs_camera": true/false,
    "cities": ["City1", "City2", ...],
    "is_comparison": true/false,
    "query_language": "en/zh/other",
    "query_type": "environmental/weather/traffic/people/general",
    "execution_strategy": "Brief description"
}}"""
        
        plan_response = self.call_llm_text(plan_prompt, temperature=0.3)
        
        if not plan_response:
            return "Sorry, I cannot understand your question." if '?' in user_query or '' in user_query else "Sorry, I cannot understand your question."
        
        try:
            json_match = re.search(r'\{.*\}', plan_response, re.DOTALL)
            if not json_match:
                return "Sorry, I cannot process your request。"
            
            plan = json.loads(json_match.group())
            print(f"  Execution plan:")
            print(f"    Needs camera: {plan.get('needs_camera')}")
            print(f"    Cities involved: {plan.get('cities')}")
            print(f"    Is comparison: {plan.get('is_comparison')}")
            print(f"    Query language: {plan.get('query_language')}")
            print(f"    Execution strategy: {plan.get('execution_strategy')}")
            
        except Exception as e:
            print(f"  ✗ Plan parsing failed: {str(e)}")
            return "Sorry, I cannot process your request。"
        
        # If camera not needed, let LLM answer directly
        if not plan.get('needs_camera'):
            print("\n[Note] This question does not require real-time camera images")
            
            lang_prompt = "You are a friendly assistant。" if plan.get('query_language') == 'zh' else "You are a friendly assistant."
            response = self.call_llm_text(user_query, lang_prompt)
            
            print("\n" + "="*70)
            print("Answer:")
            print("="*70)
            print(response)
            return response
        
        # Step 2: Capture images for each city
        cities = plan.get('cities', [])
        if not cities:
            return "Sorry, I cannot identify the cities you're forking about。" if plan.get('query_language') == 'zh' else "Sorry, I cannot identify the cities you're forking about."
        
        print(f"\n[Step 2] for {len(cities)} cities capturing images...")
        
        city_images = {}
        city_analyses = {}
        
        for city in cities:
            print(f"\n  --- Processing city: {city} ---")
            
            # Search for camerfor
            camera_urls = self.search_earthcam(city)
            
            if not camera_urls:
                print(f"  ⚠ {city}: No available camera found, trying to search...")
                # Let LLM suggest search keywords
                search_prompt = f"Suggest 2-3 specific landmark names in {city} that might have EarthCam camerfor. Return only JSON: {{\"landmarks\": [\"landmark1\", \"landmark2\"]}}"
                search_response = self.call_llm_text(search_prompt, temperature=0.3)
                
                try:
                    landmarks_match = re.search(r'\{.*\}', search_response, re.DOTALL)
                    if landmarks_match:
                        landmarks_data = json.loads(landmarks_match.group())
                        for landmark in landmarks_data.get('landmarks', [])[:2]:
                            print(f"  Trying to search landmark: {landmark}")
                            camera_urls = self.search_earthcam(landmark, city)
                            if camera_urls:
                                break
                except:
                    pass
            
            # Try to capture image
            image_path = None
            if camera_urls:
                for i, camera_url in enumerate(camera_urls[:3], 1):
                    print(f"  Trying camera {i}/{min(3, len(camera_urls))}: {camera_url}")
                    image_path = self.capture_camera_image(camera_url)
                    if image_path:
                        break
            
            if image_path:
                city_images[city] = image_path
                print(f"  ✓ {city}: Image capture successful")
            else:
                print(f"  ✗ {city}: No available camerfor")
                city_images[city] = None
        
        # Step 3: Analyze images or handle missing cases
        print(f"\n[Step 3] Analyzing images and generating answer...")
        
        # Let LLM decide how to handle
        for city, image_path in city_images.items():
            if image_path:
                # Get local time
                local_time_str, timezone_str = self.get_local_time_from_llm(city)
                
                # Let LLM analyze image
                query_language = plan.get('query_language', 'en')
                
                if query_language == 'zh':
                    vision_prompt = f"""Please analyze this{city}real-time camera image from（captured at：{local_time_str} {timezone_str}）。

Brief description：
1. Weather conditions（clear/cloudy/rainy）
2. Visibility and air quality
3. Traffic and crowd conditions

Answer concisely in Chinese（3-5sentences）。"""
                else:
                    vision_prompt = f"""Analyze this real-time camera image from {city} (captured at {local_time_str} {timezone_str}).

Briefly describe:
1. Weather conditions (clear/cloudy/rainy)
2. Visibility and air quality
3. Traffic and crowd conditions

Answer concisely in English (3-5 sentences)."""
                
                analysis = self.call_llm_vision(image_path, vision_prompt)
                city_analyses[city] = {
                    'status': 'success',
                    'analysis': analysis,
                    'image_path': image_path,
                    'local_time': local_time_str,
                    'timezone': timezone_str
                }
            else:
                city_analyses[city] = {
                    'status': 'no_camera',
                    'analysis': None
                }
        
        # Step 4: Let LLM synthesize answer
        print(f"\n[Step 4] Generating final answer...")
        
        # Build comprehensive prompt
        query_language = plan.get('query_language', 'en')
        is_comparison = plan.get('is_comparison', False)
        
        context = f"Original user query: {user_query}\n\n"
        context += "Available data:\n"
        
        for city, data in city_analyses.items():
            if data['status'] == 'success':
                context += f"\n{city}:\n"
                context += f"- Local time: {data['local_time']} ({data['timezone']})\n"
                context += f"- Analysis: {data['analysis']}\n"
                context += f"- Image available: {data['image_path']}\n"
            else:
                context += f"\n{city}:\n"
                context += f"- Status: No camera available\n"
        
        if query_language == 'zh':
            final_prompt = f"""{context}

Bfored on the above information, answer user's question in Chinese。

Requirements：
1. If all cities have no camera data：
   - Honestly explain EarthCam camerfor are currently unavailable
   - **Proactively provide alternatives**：
     * Suggest checking official local weather websites
     * Suggest using Google Maps real-time traffic layer
     * Suggest checking local environmental agency air quality monitoring data
     * Provide general advice based on typical city characteristics（such as Los Angeles typically has average air quality, traffic congestion, etc.）
   
2. If some cities have camera data, explain honestly and answer based on available data

3. If comparison question, provide clear comparative conclusions

4. Answer professionally and constructively, don't just say"no data"

5. Answer ONLY in Chinese"""
        else:
            final_prompt = f"""{context}

Bfored on the above information, answer the user's question in English.

Requirements:
1. If ALL cities have no camera data:
   - Honestly explain EarthCam camerfor are currently unavailable
   - **Proactively provide alternatives**:
     * Suggest checking official local weather websites
     * Suggest using Google Maps real-time traffic layer
     * Suggest checking local environmental agency air quality monitoring data
     * Provide general insights based on the city's typical characteristics (e.g., LA usually has moderate air quality, heavy traffic, etc.)
   
2. If some cities have camera data, explain honestly and answer based on available data

3. If it's a comparison question, provide clear comparative conclusions

4. Answer professionally and constructively, don't just say "no data available"

5. Answer ONLY in English"""
        
        final_answer = self.call_llm_text(final_prompt, temperature=0.7)
        
        print("\n" + "="*70)
        print("Answer:")
        print("="*70)
        print(final_answer)
        
        # Show reference images
        available_images = [data['image_path'] for data in city_analyses.values() if data['status'] == 'success']
        if available_images:
            print("\n" + "="*70)
            print(f"Reference images: {', '.join(available_images)}")
            print("="*70)
        
        return final_answer

def main():
    """Main program"""
    import sys
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python environment_qa.py \"your question\"")
        print("\nExamples:")
        print("  python environment_qa.py \"What is the weather like in Munich today？\"")
        print("  python environment_qa.py \"How is the traffic at Abbey Road London now?\"")
        print("  python environment_qa.py \"New YorkAre there many people at Times Square now？\"")
        return
    
    user_query = " ".join(sys.argv[1:])
    
    # Create QA system and answer question
    qa_system = EarthCamQA()
    qa_system.answer_question(user_query)

if __name__ == "__main__":
    main()
