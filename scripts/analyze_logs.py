"""
Log Analysis Script for AI Mau Bot
Parses application logs to extract analytics data.

Usage:
    python scripts/analyze_logs.py [log_file_path]
"""

import sys
import json
import re
from datetime import datetime
from collections import Counter, defaultdict

def analyze_logs(log_file_path="logs/app.log"):
    print(f"🔍 Analyzing logs from: {log_file_path}")
    
    total_requests = 0
    success_count = 0
    error_count = 0
    response_times = []
    users = set()
    model_usage = Counter() # Extracted from separate log lines
    
    # Analytics data storage
    analytics_entries = []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # 1. Parse Structured Analytics Logs
                if "ANALYTICS: {" in line:
                    try:
                        json_str = line.split("ANALYTICS: ", 1)[1].strip()
                        data = json.loads(json_str)
                        analytics_entries.append(data)
                        
                        total_requests += 1
                        if data.get("success"):
                            success_count += 1
                            response_times.append(data.get("response_time", 0))
                        else:
                            error_count += 1
                            
                        users.add(data.get("ip"))
                    except Exception as e:
                        print(f"⚠️ Failed to parse analytics line: {e}")
                
                # 2. Parse Model Usage (from ai_service logs)
                # Log format: "📨 返信モデル: {used_model}"
                if "📨 返信モデル:" in line:
                    model = line.split("📨 返信モデル:", 1)[1].strip()
                    model_usage[model] += 1
                    
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_file_path}")
        return

    # --- Generate Report ---
    print("\n" + "="*50)
    print("📊 AI Mau Bot Analytics Report")
    print("="*50)
    
    print(f"\n📈 Traffic Overview")
    print(f"Total Requests: {total_requests}")
    print(f"Success Rate:   {success_count}/{total_requests} ({(success_count/total_requests*100) if total_requests else 0:.1f}%)")
    print(f"Unique Users:   {len(users)}")
    
    print(f"\n⏱️ Performance")
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        print(f"Avg Response Time: {avg_time:.3f}s")
        print(f"Max Response Time: {max_time:.3f}s")
        print(f"Min Response Time: {min_time:.3f}s")
    else:
        print("No response time data available.")
        
    print(f"\n🤖 AI Model Usage")
    if model_usage:
        total_ai_calls = sum(model_usage.values())
        for model, count in model_usage.most_common():
            percentage = (count / total_ai_calls) * 100
            print(f"- {model}: {count} ({percentage:.1f}%)")
    else:
        print("No model usage data found (check log level).")

    print(f"\n❌ Error Analysis")
    if error_count > 0:
        print(f"Total Errors: {error_count}")
        # Could analyze common errors here if needed
    else:
        print("No errors recorded! 🎉")

    print("\n" + "="*50)

if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else "logs/app.log"
    analyze_logs(log_file)
