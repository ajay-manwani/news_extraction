#!/usr/bin/env python3
"""
Quick test script for the Flask app endpoints
"""

import requests
import json
import sys
import time

def test_endpoints():
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Flask App Endpoints")
    print("=" * 50)
    
    # Test 1: Health Check
    try:
        print("\n1️⃣ Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("   ✅ Health check PASSED")
        else:
            print("   ❌ Health check FAILED")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check ERROR: {e}")
        return False
    
    # Test 2: Index Route
    try:
        print("\n2️⃣ Testing / (index) endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("   ✅ Index endpoint PASSED")
        else:
            print("   ❌ Index endpoint FAILED")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Index endpoint ERROR: {e}")
    
    # Test 3: Process News (should work but return placeholder)
    try:
        print("\n3️⃣ Testing /process-news endpoint...")
        response = requests.post(f"{base_url}/process-news", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("   ✅ Process news endpoint PASSED")
        else:
            print("   ❌ Process news endpoint FAILED")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Process news endpoint ERROR: {e}")
    
    print("\n🎉 Flask App Test Complete!")
    return True

if __name__ == "__main__":
    # Wait a bit for server to be ready
    print("⏳ Waiting for Flask server to be ready...")
    time.sleep(2)
    
    success = test_endpoints()
    sys.exit(0 if success else 1)