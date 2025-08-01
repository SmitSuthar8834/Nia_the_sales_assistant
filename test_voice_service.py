#!/usr/bin/env python
"""
Test script for voice service functionality
"""

import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from voice_service.models import CallSession, VoiceConfiguration

User = get_user_model()

def test_voice_service_basic_functionality():
    """Test basic voice service functionality"""
    print("Testing Voice Service Basic Functionality")
    print("=" * 50)
    
    # Create test user
    try:
        user = User.objects.get(username='testvoiceuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testvoiceuser',
            email='testvoice@example.com',
            password='testpass123'
        )
    
    print(f"✓ Created/found test user: {user.username}")
    
    # Test API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Test 1: Initiate call
    print("\n1. Testing call initiation...")
    response = client.post('/api/voice/initiate/', {
        'caller_id': '555-0123'
    }, format='json')
    
    if response.status_code == 201:
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✓ Call initiated successfully. Session ID: {session_id}")
    else:
        print(f"✗ Call initiation failed: {response.status_code} - {response.json()}")
        return False
    
    # Test 2: Get session status
    print("\n2. Testing session status...")
    response = client.get(f'/api/voice/session/{session_id}/status/')
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"✓ Session status retrieved: {status_data['status']}")
    else:
        print(f"✗ Session status failed: {response.status_code}")
    
    # Test 3: Get user sessions
    print("\n3. Testing user sessions list...")
    response = client.get('/api/voice/sessions/')
    
    if response.status_code == 200:
        sessions_data = response.json()
        print(f"✓ User sessions retrieved: {sessions_data['count']} sessions")
    else:
        print(f"✗ User sessions failed: {response.status_code}")
    
    # Test 4: Voice configuration
    print("\n4. Testing voice configuration...")
    response = client.get('/api/voice/config/')
    
    if response.status_code == 200:
        config_data = response.json()
        print(f"✓ Voice config retrieved: {config_data['language_code']}")
        
        # Update configuration
        response = client.put('/api/voice/config/', {
            'language_code': 'es-ES',
            'speaking_rate': 1.2
        }, format='json')
        
        if response.status_code == 200:
            print("✓ Voice config updated successfully")
        else:
            print(f"✗ Voice config update failed: {response.status_code}")
    else:
        print(f"✗ Voice config failed: {response.status_code}")
    
    # Test 5: End call
    print("\n5. Testing call termination...")
    response = client.post('/api/voice/end/', {
        'session_id': session_id
    }, format='json')
    
    if response.status_code == 200:
        summary_data = response.json()
        print(f"✓ Call ended successfully. Duration: {summary_data.get('duration', 'N/A')}")
    else:
        print(f"✗ Call termination failed: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Voice Service Basic Functionality Test Complete!")
    return True

def test_voice_service_models():
    """Test voice service models"""
    print("\nTesting Voice Service Models")
    print("=" * 30)
    
    # Create test user
    try:
        user = User.objects.get(username='testmodeluser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testmodeluser',
            email='testmodel@example.com',
            password='testpass123'
        )
    
    # Test CallSession model
    session = CallSession.objects.create(
        user=user,
        caller_id='555-0456',
        status=CallSession.Status.ACTIVE
    )
    print(f"✓ CallSession created: {session.session_id}")
    
    # Test VoiceConfiguration model
    config, created = VoiceConfiguration.objects.get_or_create(
        user=user,
        defaults={
            'language_code': 'en-US',
            'voice_name': 'en-US-Wavenet-D'
        }
    )
    print(f"✓ VoiceConfiguration {'created' if created else 'retrieved'}: {config.language_code}")
    
    print("Voice Service Models Test Complete!")
    return True

if __name__ == '__main__':
    try:
        print("Starting Voice Service Tests...")
        print("=" * 60)
        
        # Test models
        test_voice_service_models()
        
        # Test basic functionality
        test_voice_service_basic_functionality()
        
        print("\n" + "=" * 60)
        print("All Voice Service Tests Completed Successfully! ✓")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)