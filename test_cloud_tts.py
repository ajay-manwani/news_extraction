#!/usr/bin/env python3
"""
Test script to verify Google TTS configuration in cloud
"""

import requests
import json

def test_cloud_tts():
    """Test the TTS configuration via a simple endpoint call"""
    base_url = "https://news-extractor-1098617772781.us-central1.run.app"
    
    # First test basic health
    health_response = requests.get(f"{base_url}/health")
    print(f"Health check: {health_response.status_code}")
    print(f"Health response: {health_response.json()}")
    
    # Test pipeline components
    test_response = requests.get(f"{base_url}/test-pipeline")
    print(f"\nPipeline test: {test_response.status_code}")
    result = test_response.json()
    print(f"TTS Generator working: {result['test_results']['tts_generator']}")
    
    if result['test_results']['errors']:
        print(f"Errors: {result['test_results']['errors']}")

if __name__ == "__main__":
    test_cloud_tts()