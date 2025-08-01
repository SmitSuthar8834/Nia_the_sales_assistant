#!/usr/bin/env python
"""
Debug script to identify the 500 error in frontend
"""
import requests
import json

def test_all_endpoints():
    """Test all the endpoints the frontend might be calling"""
    print("🔍 Testing All Frontend API Endpoints")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/api/ai"
    
    endpoints_to_test = [
        ("GET", "/debug-test/", None),
        ("POST", "/debug-test/", {"conversation_text": "test"}),
        ("GET", "/leads/", None),
        ("POST", "/leads/", {
            "company_name": "Test Company",
            "contact_info": {"name": "Test"},
            "source": "test"
        }),
        ("GET", "/analytics/", None),
        ("GET", "/test-connection/", None),
    ]
    
    for method, endpoint, data in endpoints_to_test:
        try:
            url = base_url + endpoint
            print(f"\n{method} {url}")
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(
                    url, 
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code >= 400:
                print(f"Error: {response.text[:200]}...")
            else:
                print("✅ Success")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

def test_static_files():
    """Test if static files are accessible"""
    print("\n🔍 Testing Static Files")
    print("=" * 30)
    
    static_files = [
        "/static/js/api.js",
        "/static/js/ui.js", 
        "/static/js/main.js",
        "/static/css/main.css",
        "/static/images/nia-logo.jpg"
    ]
    
    for file_path in static_files:
        try:
            url = f"http://127.0.0.1:8000{file_path}"
            response = requests.get(url, timeout=5)
            print(f"{file_path}: {response.status_code}")
            
            if response.status_code >= 400:
                print(f"  Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"{file_path}: ❌ {e}")

def test_csrf_token():
    """Test CSRF token handling"""
    print("\n🔍 Testing CSRF Token")
    print("=" * 25)
    
    try:
        # First get the main page to get CSRF token
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"Main page status: {response.status_code}")
        
        # Check if CSRF token is in cookies
        csrf_token = None
        for cookie in response.cookies:
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value
                break
        
        print(f"CSRF token found: {csrf_token is not None}")
        
        if csrf_token:
            # Test API call with CSRF token
            test_response = requests.post(
                "http://127.0.0.1:8000/api/ai/debug-test/",
                json={"conversation_text": "test"},
                headers={
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf_token
                },
                cookies=response.cookies,
                timeout=10
            )
            print(f"API call with CSRF: {test_response.status_code}")
        
    except Exception as e:
        print(f"CSRF test failed: {e}")

if __name__ == "__main__":
    test_all_endpoints()
    test_static_files()
    test_csrf_token()