#!/usr/bin/env python3
"""
Test script for monitoring endpoints
Run this while the backend is running to verify the monitoring dashboard works
"""
import os
import requests
import json
import time

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def test_endpoint(endpoint, description):
    """Test a single endpoint"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        print(f"\n=== Testing {description} ===")
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: {response.status_code}")
            
            # Print relevant summary info
            if endpoint == "/agents/health":
                summary = data.get('summary', {})
                print(f"Agents: {summary.get('total_agents', 0)} total, {summary.get('healthy_agents', 0)} healthy")
            elif endpoint == "/agents/status":
                agents = data.get('agents', {})
                print(f"Registered agents: {len(agents)}")
            elif endpoint == "/resources/status":
                summary = data.get('summary', {})
                print(f"Thread capacity: {summary.get('total_thread_capacity', 0)}, Active: {summary.get('active_threads', 0)}")
            
            return True
        else:
            print(f"❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Backend not running at {BACKEND_URL}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print("🔍 Testing Hexar Monitoring Endpoints")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 50)
    
    # Test basic health endpoint
    success_count = 0
    total_tests = 4
    
    if test_endpoint("/health", "Basic Health Check"):
        success_count += 1
    
    if test_endpoint("/agents/health", "Agent Health Monitor"):
        success_count += 1
    
    if test_endpoint("/agents/status", "Agent Status"):
        success_count += 1
    
    if test_endpoint("/resources/status", "Resource Status"):
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: {success_count}/{total_tests} endpoints working")
    
    if success_count == total_tests:
        print("🎉 All monitoring endpoints are working!")
        print("🚀 You can now access the monitoring dashboard at:")
        print(f"   Frontend: http://{os.getenv('FRONTEND_HOST', 'localhost')}:{os.getenv('FRONTEND_PORT', '3000')}/monitoring")
        print("   (Make sure to start the frontend with: npm run dev)")
    else:
        print("⚠️  Some endpoints failed. Make sure the backend is running:")
        print("   cd hexar-backend && python main.py")

if __name__ == "__main__":
    main()