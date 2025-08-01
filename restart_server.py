#!/usr/bin/env python
"""
Simple script to test if the server needs to be restarted
"""
import requests
import time

def test_server():
    """Test if the server is responding"""
    try:
        response = requests.get('http://127.0.0.1:8000', timeout=3)
        return response.status_code == 200
    except:
        return False

def test_api():
    """Test the API endpoint"""
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/ai/debug-test/',
            json={'test': 'data'},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🔍 Testing server status...")
    
    if test_server():
        print("✅ Server is running")
        
        if test_api():
            print("✅ API is responding")
            print("\n🚀 Server is ready! You can now test the frontend.")
            print("📝 Instructions:")
            print("1. Open http://127.0.0.1:8000 in your browser")
            print("2. Go to Create Lead tab")
            print("3. Paste conversation text and click 'Analyze & Create Lead'")
            print("4. Check browser console (F12) for detailed logs")
        else:
            print("❌ API is not responding - server may need restart")
            print("💡 Please restart with: python manage.py runserver")
    else:
        print("❌ Server is not running")
        print("💡 Please start with: python manage.py runserver")