#!/usr/bin/env python3
"""
Temporal-RAG Enhanced Environment QA System
Intelligent Q&A system with historical comparison and trend analysis support

Core Features:
1. Historical record storage and retrieval (vector database)
2. Temporal comparison queries (today vs yesterday, this week vs last week)
3. Trend analysis and anomaly detection
4. Multi-modal knowledge enhancement
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
import hashlib

# Import existing QA system
from environment_qa import EarthCamQA

class TemporalRAG:
    """Temporal-aware RAG system"""
    
    def __init__(self, db_path="./rag_storage"):
        """Initialize RAG system"""
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize vector database (ChromaDB)
        self.chroma_client = chromadb.PersistentClient(
            path=os.path.join(db_path, "chroma")
        )
        
        # Create collection
        try:
            self.collection = self.chroma_client.get_collection("camera_history")
        except:
            self.collection = self.chroma_client.create_collection(
                name="camera_history",
                metadata={"description": "Historical camera analysis records"}
            )
        
        # Initialize text encoder (using simple TF-IDF or hash method)
        print("  [RAG] Using lightweight text encoding...")
        # No additional encoder needed, using ChromaDB's built-in embedding
        
        # Initialize SQLite for structured data
        self.sql_db_path = os.path.join(db_path, "records.db")
        self._init_sql_db()
        
        print(f"  [RAG] Initialization complete, storage path: {db_path}")
    
    def _init_sql_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.sql_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS camera_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                camera_url TEXT NOT NULL,
                image_path TEXT NOT NULL,
                analysis TEXT NOT NULL,
                weather TEXT,
                traffic_level TEXT,
                people_density TEXT,
                timestamp DATETIME NOT NULL,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_city_time 
            ON camera_records(city, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_city_hour_dow 
            ON camera_records(city, hour_of_day, day_of_week)
        """)
        
        conn.commit()
        conn.close()
    
    def add_record(self, city: str, camera_url: str, image_path: str, 
                   analysis: str, timestamp: datetime = None):
        """Add historical record to RAG system"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Extract structured information
        weather = self._extract_weather(analysis)
        traffic_level = self._extract_traffic(analysis)
        people_density = self._extract_people(analysis)
        
        # 1. Add to vector database (using ChromaDB built-in embedding)
        record_id = f"{city}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        self.collection.add(
            documents=[analysis],  # ChromaDB will automatically generate embedding
            metadatas=[{
                'city': city,
                'camera_url': camera_url,
                'image_path': image_path,
                'timestamp': timestamp.isoformat(),
                'weather': weather,
                'traffic_level': traffic_level,
                'people_density': people_density,
                'hour': timestamp.hour,
                'day_of_week': timestamp.weekday()
            }],
            ids=[record_id]
        )
        
        # 2. Add to SQL database (for temporal queries)
        conn = sqlite3.connect(self.sql_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO camera_records 
            (city, camera_url, image_path, analysis, weather, traffic_level, 
             people_density, timestamp, hour_of_day, day_of_week)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (city, camera_url, image_path, analysis, weather, traffic_level,
              people_density, timestamp, timestamp.hour, timestamp.weekday()))
        
        conn.commit()
        conn.close()
        
        return record_id
    
    def _extract_weather(self, analysis: str) -> str:
        """Extract weather information from analysis text"""
        analysis_lower = analysis.lower()
        
        if any(w in analysis_lower for w in ['sunny', 'sunny', 'sunshine', 'clear']):
            return 'sunny'
        elif any(w in analysis_lower for w in ['cloudy', 'cloudy', 'overcast']):
            return 'cloudy'
        elif any(w in analysis_lower for w in ['rain', 'rain', 'raining']):
            return 'rainy'
        elif any(w in analysis_lower for w in ['snow', 'snow', 'snowing']):
            return 'snowy'
        else:
            return 'unknown'
    
    def _extract_traffic(self, analysis: str) -> str:
        """Extract traffic conditions from analysis text"""
        analysis_lower = analysis.lower()
        
        if any(w in analysis_lower for w in ['congested', 'congested', 'traffic jam', 'traffic jam']):
            return 'heavy'
        elif any(w in analysis_lower for w in ['moderate traffic', 'moderate traffic', 'normal']):
            return 'moderate'
        elif any(w in analysis_lower for w in ['smooth', 'light traffic', 'light traffic', 'smooth']):
            return 'light'
        else:
            return 'unknown'
    
    def _extract_people(self, analysis: str) -> str:
        """Extract crowd density from analysis text"""
        analysis_lower = analysis.lower()
        
        if any(w in analysis_lower for w in ['crowded', 'crowded', 'crowded', 'dense']):
            return 'high'
        elif any(w in analysis_lower for w in ['moderate crowd', 'moderate', 'normal crowd']):
            return 'moderate'
        elif any(w in analysis_lower for w in ['sparse crowd', 'sparse', 'spacious', 'few people']):
            return 'low'
        else:
            return 'unknown'
    
    def query_by_time(self, city: str, target_time: datetime, 
                      time_window: int = 30) -> List[Dict]:
        """Query historical records by time (for temporal comparison)"""
        conn = sqlite3.connect(self.sql_db_path)
        cursor = conn.cursor()
        
        start_time = target_time - timedelta(minutes=time_window)
        end_time = target_time + timedelta(minutes=time_window)
        
        cursor.execute("""
            SELECT city, camera_url, image_path, analysis, weather, 
                   traffic_level, people_density, timestamp
            FROM camera_records
            WHERE city = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (city, start_time, end_time))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'city': row[0],
                'camera_url': row[1],
                'image_path': row[2],
                'analysis': row[3],
                'weather': row[4],
                'traffic_level': row[5],
                'people_density': row[6],
                'timestamp': datetime.fromisoformat(row[7])
            })
        
        conn.close()
        return results
    
    def query_similar(self, query: str, city: str = None, k: int = 5) -> List[Dict]:
        """Semantic similarity retrieval"""
        where = {"city": city} if city else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
        
        similar_records = []
        for i in range(len(results['documents'][0])):
            similar_records.append({
                'id': results['ids'][0][i],
                'analysis': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return similar_records
    
    def get_historical_stats(self, city: str, hours: int = 24) -> Dict:
        """Get historical statistics"""
        conn = sqlite3.connect(self.sql_db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT DATE(timestamp)) as days_covered,
                weather,
                traffic_level,
                people_density
            FROM camera_records
            WHERE city = ? AND timestamp >= ?
            GROUP BY weather, traffic_level, people_density
        """, (city, cutoff_time))
        
        stats = {
            'city': city,
            'total_records': 0,
            'days_covered': 0,
            'weather_distribution': {},
            'traffic_distribution': {},
            'people_distribution': {}
        }
        
        for row in cursor.fetchall():
            stats['total_records'] += row[0]
            stats['days_covered'] = max(stats['days_covered'], row[1])
            
            if row[2]:
                stats['weather_distribution'][row[2]] = stats['weather_distribution'].get(row[2], 0) + row[0]
            if row[3]:
                stats['traffic_distribution'][row[3]] = stats['traffic_distribution'].get(row[3], 0) + row[0]
            if row[4]:
                stats['people_distribution'][row[4]] = stats['people_distribution'].get(row[4], 0) + row[0]
        
        conn.close()
        return stats


class TemporalRAGQA(EarthCamQA):
    """RAG-enhanced Environment QA System"""
    
    def __init__(self, api_key=os.getenv("SILICONFLOW_API_KEY"), enable_rag=True):
        super().__init__(api_key)
        self.enable_rag = enable_rag
        
        if enable_rag:
            print("[RAG] Initializing Temporal RAG system...")
            self.rag = TemporalRAG()
            print("[RAG] Initialization complete\n")
        else:
            self.rag = None
    
    def _is_comparison_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Determine if it's a comparison query, returns (is_comparison, comparison_type)"""
        query_lower = query.lower()
        
        # Detect time comparison keywords
        if any(w in query_lower for w in ['yesterday', 'last time']):
            return True, 'yesterday'
        elif any(w in query_lower for w in ['last week', 'last week', 'one week ago', 'week ago']):
            return True, 'last_week'
        elif any(w in query_lower for w in ['compare', 'compare', 'vs', 'comparison', 'compared to']):
            return True, 'general'
        elif any(w in query_lower for w in ['trend', 'trend', 'change', 'change']):
            return True, 'trend'
        
        return False, None
    
    def answer_question_with_rag(self, user_query: str):
        """RAG-enhanced Q&A"""
        print("="*70)
        print("Temporal RAG Enhanced Environment QA System")
        print("="*70)
        print(f"\nUser question: {user_query}\n")
        print("-"*70)
        
        # Step1: Analyze user intent
        print("\n[Step1] Analyzing user intent...")
        intent = self.analyze_user_intent(user_query)
        
        if not intent:
            return "Sorry, I cannot understand your question."
        
        print(f"  Intent analysis result:")
        print(f"    Requires camera: {intent.get('is_camera_query')}")
        if intent.get('city'):
            print(f"    Target city: {intent.get('city')}")
        if intent.get('query_type'):
            print(f"    Query type: {intent.get('query_type')}")
        
        # Check if it's a comparison query
        is_comparison, comparison_type = self._is_comparison_query(user_query)
        if is_comparison:
            print(f"    Comparison type: {comparison_type}")
        
        # If not a camera query, directly answer
        if not intent.get('is_camera_query'):
            print("\n[Note] User question not related to live camera")
            response = self.call_llm_text(user_query, temperature=0.7)
            print("\n" + "="*70)
            print("Answer:")
            print("="*70)
            print(response)
            return response
        
        city = intent.get('city', '')
        if not city:
            return "Sorry, I cannot identify the city you want to query."
        
        # Step2: Search for cameras
        print("\n[Step2] Searching EarthCam cameras...")
        camera_urls = self.search_earthcam(city, intent.get('country', ''))
        
        if not camera_urls:
            return f"Sorry, I did not find cameras in{city}."
        
        print(f"  ✓ Found {len(camera_urls)} cameras")
        
        # Step3: Capture current image
        print(f"\n[Step3] Capturing current image...")
        current_image_path = None
        current_camera_url = None
        
        for i, camera_url in enumerate(camera_urls[:3], 1):
            print(f"\n  Trying camera {i}/{min(3, len(camera_urls))}: {camera_url}")
            image_path = self.capture_camera_image(camera_url)
            
            if image_path:
                current_image_path = image_path
                current_camera_url = camera_url
                break
        
        if not current_image_path:
            return f"Sorry, {city}'s cameras are temporarily unavailable."
        
        # Step4: Analyze current image
        print(f"\n[Step4] Analyzing current image with vision LLM...")
        
        vision_prompt = f"""Please carefully observe this live camera image and describe in detail:

1. Weather conditions (sunny/cloudy/rainy/snowy, light intensity, visibility)
2. Traffic conditions (number of vehicles, traffic speed, congestion status)
3. Crowd conditions (number of pedestrians, crowd density)
4. Overall environment description

Please provide specific and accurate observations."""
        
        current_analysis = self.call_llm_vision(current_image_path, vision_prompt)
        
        if not current_analysis:
            return "Sorry, Image analysis failed."
        
        print(f"  ✓ Current analysis complete")
        
        # Step5: RAG enhancement (if enabled and is comparison query)
        historical_context = None
        
        if self.enable_rag and self.rag:
            # Store current record
            print(f"\n[Step5] Storing current record to RAG...")
            current_time = datetime.now()
            self.rag.add_record(
                city=city,
                camera_url=current_camera_url,
                image_path=current_image_path,
                analysis=current_analysis,
                timestamp=current_time
            )
            print(f"  ✓ Stored")
            
            # If it's a comparison query, retrieve historical data
            if is_comparison:
                print(f"\n[Step6] Retrieving historical data for comparison...")
                
                # Calculate target time
                if comparison_type == 'yesterday':
                    target_time = current_time - timedelta(days=1)
                    print(f"  Comparison time: Same time yesterday ({target_time.strftime('%Y-%m-%d %H:%M')})")
                elif comparison_type == 'last_week':
                    target_time = current_time - timedelta(weeks=1)
                    print(f"  Comparison time: Same time last week ({target_time.strftime('%Y-%m-%d %H:%M')})")
                else:
                    target_time = current_time - timedelta(days=1)
                    print(f"  Comparison time: One day ago ({target_time.strftime('%Y-%m-%d %H:%M')})")
                
                # Query historical records
                historical_records = self.rag.query_by_time(
                    city=city,
                    target_time=target_time,
                    time_window=60  # within60minutes
                )
                
                if historical_records:
                    print(f"  ✓ Found {len(historical_records)} historical records")
                    historical_context = historical_records[0]  # Using the closest record
                else:
                    print(f"  ✗ No historical records found, will answer based on current analysis")
                    
                    # Display statistics
                    stats = self.rag.get_historical_stats(city, hours=168)  # 7 days
                    if stats['total_records'] > 0:
                        print(f"\n  Historical statistics (Last 7 days):")
                        print(f"    Total records: {stats['total_records']}")
                        print(f"    Days covered: {stats['days_covered']}")
        
        # Step6/7：Generate final answer
        step_num = 7 if (self.enable_rag and is_comparison) else 5
        print(f"\n[Step{step_num}] Generating answer...")
        
        if historical_context:
            # Generate comparison answer
            comparison_prompt = f"""Please compare and analyze the following information to answer the user's question.

User question: {user_query}

Current situation ({current_time.strftime('%Y%m-%d %H:%M')}):
{current_analysis}

Historical situation ({historical_context['timestamp'].strftime('%Y%m-%d %H:%M')}):
{historical_context['analysis']}

Please compare and analyze:
1. Weather changes (if relevant)
2. Traffic changes (if relevant)
3. Crowd changes (if relevant)
4. Overall trends and differences

Provide specific and quantified comparison results."""
            
            answer = self.call_llm_text(comparison_prompt, temperature=0.7)
            
            print("\n" + "="*70)
            print("Comparison Analysis:")
            print("="*70)
            print(answer)
            print("\n" + "="*70)
            print(f"Current image: {current_image_path}")
            print(f"Historical image: {historical_context['image_path']}")
            print("="*70)
        else:
            # Generate regular answer
            answer_prompt = f"""Please answer the user's question based on this live image analysis result.

User question: {user_query}

Image analysis:
{current_analysis}

Please provide accurate and detailed answers."""
            
            answer = self.call_llm_text(answer_prompt, temperature=0.7)
            
            print("\n" + "="*70)
            print("Answer:")
            print("="*70)
            print(answer)
            print("\n" + "="*70)
            print(f"Reference image: {current_image_path}")
            print("="*70)
        
        return answer


def main():
    """Main program"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python temporal_rag_qa.py \"your question\" [--no-rag]")
        print("\nExamples:")
        print("  python temporal_rag_qa.py \"Is there traffic congestion at Times Square New York now?\"")
        print("  python temporal_rag_qa.py \"Is the weather in London better today than yesterday?\"")
        print("  python temporal_rag_qa.py \"What is the traffic trend in Munich this week?\"")
        print("\nOptions:")
        print("  --no-rag: Disable RAG functionality, use original QA system")
        return
    
    # Parse arguments
    enable_rag = '--no-rag' not in sys.argv
    user_query = " ".join([arg for arg in sys.argv[1:] if arg != '--no-rag'])
    
    # Create QA system
    qa_system = TemporalRAGQA(enable_rag=enable_rag)
    qa_system.answer_question_with_rag(user_query)


if __name__ == "__main__":
    main()
