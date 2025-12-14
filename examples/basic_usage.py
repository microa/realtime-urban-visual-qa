#!/usr/bin/env python3
"""
Basic Usage Examples for Realtime Urban Visual QA

These examples demonstrate the main features of the system.
"""

from environment_qa import EarthCamQA

def example_1_weather_query():
    """Example 1: Ask about weather in a single city"""
    print("="*70)
    print("Example 1: Weather Query")
    print("="*70)
    
    qa = EarthCamQA()
    qa.answer_question("What's the weather like in London right now?")

def example_2_traffic_query():
    """Example 2: Ask about traffic conditions"""
    print("\n" + "="*70)
    print("Example 2: Traffic Query")
    print("="*70)
    
    qa = EarthCamQA()
    qa.answer_question("Is Times Square crowded?")

def example_3_multi_city_comparison():
    """Example 3: Compare multiple cities"""
    print("\n" + "="*70)
    print("Example 3: Multi-City Comparison")
    print("="*70)
    
    qa = EarthCamQA()
    qa.answer_question("Compare air quality between London and Paris")

def example_4_chinese_query():
    """Example 4: Query in Chinese"""
    print("\n" + "="*70)
    print("Example 4: Chinese Language Query")
    print("="*70)
    
    qa = EarthCamQA()
    qa.answer_question("How is the weather in London now?")

def example_5_direct_capture():
    """Example 5: Direct image capture from specific camera"""
    print("\n" + "="*70)
    print("Example 5: Direct Image Capture")
    print("="*70)
    
    qa = EarthCamQA()
    
    # Capture from specific camera URL
    camera_url = "https://www.earthcam.com/usa/newyork/timessquare/"
    print(f"Capturing from: {camera_url}")
    
    image_path = qa.capture_camera_image(camera_url)
    
    if image_path:
        print(f"✅ Image saved to: {image_path}")
    else:
        print("❌ Failed to capture image")

if __name__ == "__main__":
    # Run all examples
    print("Realtime Urban Visual QA - Usage Examples\n")
    
    # Uncomment the examples you want to run:
    
    example_1_weather_query()
    # example_2_traffic_query()
    # example_3_multi_city_comparison()
    # example_4_chinese_query()
    # example_5_direct_capture()
