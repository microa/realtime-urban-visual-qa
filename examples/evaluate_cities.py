#!/usr/bin/env python3
"""
City Coverage Evaluation Script
Evaluates camera availability across 36 global cities

Usage:
    python examples/evaluate_cities.py
"""

import json
import time
from datetime import datetime
from environment_qa import EarthCamQA

def evaluate_all_cities():
    """Evaluate camera availability for all cities"""
    
    # Test cities (grouped by region)
    test_cities = {
        "Europe": [
            "London", "Paris", "Amsterdam", "Dublin", 
            "Munich", "Barcelona", "Rome"
        ],
        "North America": [
            "New York", "Chicago", "Miami", "Las Vegas",
            "San Francisco", "Boston", "Washington DC"
        ],
        "Asia": [
            "Tokyo", "Dubai", "Singapore", "Hong Kong",
            "Seoul", "Bangkok", "Shanghai", "Delhi",
            "Mumbai", "Manila", "Jakarta", "Beijing"
        ],
        "Oceania": [
            "Sydney", "Melbourne", "Auckland", "Brisbane"
        ],
        "South America": [
            "São Paulo", "Rio de Janeiro", "Buenos Aires",
            "Santiago", "Lima", "Bogotá"
        ],
        "Africa": [
            "Cairo", "Cape Town"
        ]
    }
    
    qa_system = EarthCamQA()
    
    results = {
        "metadata": {
            "evaluation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_cities": sum(len(cities) for cities in test_cities.values()),
        },
        "by_continent": {},
        "summary": {}
    }
    
    total_success = 0
    total_tested = 0
    
    print("="*80)
    print("City Coverage Evaluation")
    print("="*80)
    
    for continent, cities in test_cities.items():
        print(f"\n{'='*80}")
        print(f"Region: {continent}")
        print(f"{'='*80}")
        
        continent_results = []
        continent_success = 0
        
        for city in cities:
            total_tested += 1
            print(f"\n[{total_tested}/{results['metadata']['total_cities']}] {city}")
            
            try:
                # Get camera URLs
                camera_urls = qa_system.search_earthcam(city)
                
                if not camera_urls:
                    print(f"  ❌ No cameras found")
                    continent_results.append({
                        "city": city,
                        "status": "no_cameras",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    continue
                
                # Try to capture image
                image_captured = False
                for i, url in enumerate(camera_urls[:3], 1):
                    print(f"  Trying camera {i}/{min(3, len(camera_urls))}: {url[:60]}...")
                    
                    image_path = qa_system.capture_camera_image(url)
                    if image_path:
                        print(f"  ✅ Success")
                        continent_success += 1
                        total_success += 1
                        image_captured = True
                        
                        continent_results.append({
                            "city": city,
                            "url": url,
                            "status": "success",
                            "image": image_path,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        break
                
                if not image_captured:
                    print(f"  ❌ All cameras failed")
                    continent_results.append({
                        "city": city,
                        "status": "failed",
                        "urls_tried": camera_urls[:3],
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                # Delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)[:100]}")
                continent_results.append({
                    "city": city,
                    "status": "error",
                    "error": str(e)[:200],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Regional summary
        success_rate = (continent_success / len(cities) * 100) if cities else 0
        results["by_continent"][continent] = {
            "cities": continent_results,
            "total": len(cities),
            "success": continent_success,
            "failed": len(cities) - continent_success,
            "success_rate": f"{success_rate:.1f}%"
        }
        
        print(f"\n{continent} Summary: {continent_success}/{len(cities)} ({success_rate:.1f}%)")
    
    # Overall summary
    overall_rate = (total_success / total_tested * 100) if total_tested else 0
    results["summary"] = {
        "total_tested": total_tested,
        "total_success": total_success,
        "total_failed": total_tested - total_success,
        "overall_success_rate": f"{overall_rate:.1f}%"
    }
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Final report
    print("\n" + "="*80)
    print("Final Report")
    print("="*80)
    print(f"Overall Success Rate: {total_success}/{total_tested} = {overall_rate:.1f}%")
    print(f"\nBy Region:")
    for continent, data in results["by_continent"].items():
        print(f"  {continent:20s}: {data['success']:2d}/{data['total']:2d} = {data['success_rate']:6s}")
    
    print(f"\nResults saved to: {filename}")
    
    return results

if __name__ == "__main__":
    evaluate_all_cities()
