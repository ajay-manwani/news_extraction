#!/usr/bin/env python3
"""
Pre-flight check for News Extraction Service deployment
Verifies all requirements are met before deployment
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def print_status(message, success=True):
    """Print colored status message"""
    color = GREEN if success else RED
    symbol = "✅" if success else "❌"
    print(f"{color}{symbol} {message}{NC}")

def print_warning(message):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {message}{NC}")

def check_env_file():
    """Check if .env file exists and has required keys"""
    print("🔍 Checking .env file...")
    
    env_path = Path("../.env")
    if not env_path.exists():
        print_status(".env file not found in parent directory", False)
        return False
    
    print_status(".env file found")
    
    # Load and check keys
    required_keys = ["OPENROUTER_API_KEY"]
    optional_keys = ["TELEGRAM_HTTP_API_KEY", "GOOGLE_API_KEY"]
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    
    # Check required keys
    missing_required = []
    for key in required_keys:
        if key in env_vars and env_vars[key]:
            print_status(f"Required key {key}: Available")
        else:
            missing_required.append(key)
            print_status(f"Required key {key}: Missing", False)
    
    # Check optional keys
    for key in optional_keys:
        if key in env_vars and env_vars[key]:
            print_status(f"Optional key {key}: Available")
        else:
            print_warning(f"Optional key {key}: Not found (will use fallback)")
    
    return len(missing_required) == 0

def check_gcloud():
    """Check if gcloud CLI is installed and authenticated"""
    print("\n🌥️ Checking Google Cloud CLI...")
    
    try:
        # Check if gcloud is installed
        result = subprocess.run(['gcloud', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print_status("gcloud CLI not working", False)
            print("Install from: https://cloud.google.com/sdk/docs/install")
            return False
            
        print_status("gcloud CLI installed")
        
        # Check authentication
        result = subprocess.run(['gcloud', 'auth', 'list'], 
                              capture_output=True, text=True, timeout=10)
        if "ACTIVE" not in result.stdout:
            print_status("Not authenticated with Google Cloud", False)
            print("Run: gcloud auth login")
            return False
            
        print_status("Google Cloud authenticated")
        return True
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_status("gcloud CLI not found", False)
        print("Install from: https://cloud.google.com/sdk/docs/install")
        return False

def check_deployment_files():
    """Check if all deployment files are present"""
    print("\n📁 Checking deployment files...")
    
    required_files = [
        'Dockerfile',
        'requirements.txt',
        'main.py',
        'config/settings.py',
        'config/sources.yaml',
        'src/news_pipeline.py',
        'deploy-with-keys.sh'
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print_status(f"{file_path}: Present")
        else:
            missing_files.append(file_path)
            print_status(f"{file_path}: Missing", False)
    
    return len(missing_files) == 0

def check_flask_app():
    """Test if Flask app can be imported"""
    print("\n🌐 Checking Flask application...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, str(Path.cwd()))
        
        # Import main components
        from main import app
        print_status("Flask app imports successfully")
        
        from config.settings import get_config
        config = get_config()
        print_status(f"Configuration loads: {type(config).__name__}")
        
        return True
    except Exception as e:
        print_status(f"Flask app check failed: {e}", False)
        return False

def main():
    """Run all pre-flight checks"""
    print("🚁 Pre-Flight Check - News Extraction Service")
    print("=" * 50)
    
    checks = [
        ("Environment File & API Keys", check_env_file),
        ("Google Cloud CLI", check_gcloud),
        ("Deployment Files", check_deployment_files),
        ("Flask Application", check_flask_app)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print_status(f"{check_name} failed with exception: {e}", False)
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Pre-Flight Summary:")
    
    for i, (check_name, _) in enumerate(checks):
        status = "✅ READY" if results[i] else "❌ NEEDS FIX"
        print(f"  {check_name}: {status}")
    
    overall_ready = all(results)
    
    if overall_ready:
        print(f"\n🎯 Status: {GREEN}✅ READY FOR DEPLOYMENT{NC}")
        print(f"\n🚀 Next step: {YELLOW}./deploy-with-keys.sh{NC}")
        print("\nThis deployment will:")
        print("  • Use your existing API keys from .env")
        print("  • Create Google Cloud project resources")
        print("  • Build container using Google Cloud Build")
        print("  • Deploy to Cloud Run with auto-scaling")
        print("  • Set up daily automated processing")
    else:
        print(f"\n🎯 Status: {RED}❌ FIX ISSUES FIRST{NC}")
        print("\nPlease resolve the issues above before deploying.")
    
    return 0 if overall_ready else 1

if __name__ == "__main__":
    sys.exit(main())