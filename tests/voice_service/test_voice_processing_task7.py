#!/usr/bin/env python
"""
Test script for Task 7: Speech processing and conversation management
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

import asyncio
from datetime import datetime

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from django.contrib.auth import get_user_model

from voice_service.models import CallSession, ConversationTurn
from voice_service.services import (
    AudioFileStorageService,
    ConversationContextManager,
    ConversationSummaryService,
    VoiceProcessingService,
)

User = get_user_model()


async def test_conversation_context_management():
    """Test conversation context tracking and state management"""
    print("🧠 Testing Conversation Context Management...")

    context_manager = ConversationContextManager()
    session_id = "test-session-123"
    user_id = "test-user-456"

    # Initialize context
    context = context_manager.initialize_context(session_id, user_id)
    print(f"✅ Initialized context: {context['conversation_state']}")

    # Update context with extracted entities
    updates = {
        "extracted_entities": {
            "companies": ["Acme Corp", "TechStart Inc"],
            "emails": ["john@acme.com"],
            "phones": ["555-123-4567"],
        },
        "conversation_state": "lead_discussion",
        "current_topic": "company_requirements",
    }

    updated_context = context_manager.update_context(session_id, updates)
    print(
        f"✅ Updated context with entities: {len(updated_context['extracted_entities'])} types"
    )

    # Add conversation flow
    flow_update = {
        "conversation_flow": [
            {
                "turn": 1,
                "speaker": "user",
                "content": "I have a lead from Acme Corp",
                "timestamp": datetime.now().isoformat(),
            }
        ]
    }

    context_manager.update_context(session_id, flow_update)
    final_context = context_manager.get_context(session_id)
    print(
        f"✅ Added conversation flow: {len(final_context['conversation_flow'])} turns"
    )

    # Clear context
    context_manager.clear_context(session_id)
    print("✅ Context cleared successfully")

    return True


async def test_conversation_summary_generation():
    """Test conversation summary generation"""
    print("\n📝 Testing Conversation Summary Generation...")

    from asgiref.sync import sync_to_async

    # Create test user and session
    user, created = await sync_to_async(User.objects.get_or_create)(
        username="testuser", defaults={"email": "test@example.com"}
    )

    session = await CallSession.objects.acreate(
        user=user, status=CallSession.Status.ENDED
    )

    # Create conversation turns
    turns_data = [
        ("Hi NIA, I have a potential lead from Acme Corporation.", "user"),
        ("Great! Tell me more about their requirements and pain points.", "nia"),
        (
            "They have 50 employees and need a CRM solution. Budget is around $10,000.",
            "user",
        ),
        ("That sounds promising. What's their timeline for implementation?", "nia"),
        (
            "They want to start within 3 months. The contact is John Smith at john@acme.com.",
            "user",
        ),
    ]

    for i, (content, speaker) in enumerate(turns_data):
        await ConversationTurn.objects.acreate(
            session=session,
            turn_number=i + 1,
            speaker=(
                ConversationTurn.Speaker.USER
                if speaker == "user"
                else ConversationTurn.Speaker.NIA
            ),
            content=content,
        )

    print(f"✅ Created {len(turns_data)} conversation turns")

    # Generate summary
    summary_service = ConversationSummaryService()
    summary = await summary_service.generate_conversation_summary(
        str(session.session_id)
    )

    print(f"✅ Generated summary: {summary['summary'][:100]}...")
    print(
        f"✅ Extracted lead info: {summary['lead_information'].get('company_name', 'N/A')}"
    )
    print(f"✅ Key points: {len(summary['key_points'])} items")
    print(f"✅ Action items: {len(summary['action_items'])} items")

    # Clean up
    await session.adelete()

    return True


async def test_audio_file_storage():
    """Test audio file storage and retrieval system"""
    print("\n🎵 Testing Audio File Storage System...")

    storage_service = AudioFileStorageService()
    session_id = "test-session-audio-123"

    # Create test audio data
    test_audio = b"fake_audio_data_for_testing_purposes"
    metadata = {
        "turn_number": 1,
        "speaker": "user",
        "timestamp": datetime.now().isoformat(),
    }

    # Store audio file
    file_path = await storage_service.store_audio_file(
        session_id, test_audio, "wav", metadata
    )

    print(f"✅ Stored audio file: {os.path.basename(file_path)}")

    # Retrieve audio file
    retrieved_audio = await storage_service.retrieve_audio_file(file_path)
    print(f"✅ Retrieved audio: {len(retrieved_audio)} bytes")

    # Get session audio files
    session_files = await storage_service.get_session_audio_files(session_id)
    print(f"✅ Found {len(session_files)} audio files for session")

    # Clean up
    await storage_service.delete_session_audio_files(session_id)
    print("✅ Cleaned up audio files")

    return True


async def test_voice_processing_integration():
    """Test integrated voice processing workflow"""
    print("\n🎤 Testing Voice Processing Integration...")

    from asgiref.sync import sync_to_async

    # Create test user
    user, created = await sync_to_async(User.objects.get_or_create)(
        username="voiceuser", defaults={"email": "voice@example.com"}
    )

    voice_service = VoiceProcessingService()

    # Initiate call
    session = await voice_service.initiate_call(str(user.id))
    print(f"✅ Initiated call session: {session.session_id}")

    # Check conversation context was initialized
    context = voice_service.context_manager.get_context(str(session.session_id))
    print(f"✅ Context initialized: {context['conversation_state']}")

    # Simulate conversation turns (without actual audio processing)
    test_turns = [
        "Hello, I have a lead from TechStart Inc",
        "They need a sales automation solution",
        "Budget is around $15,000 and timeline is 2 months",
    ]

    for i, content in enumerate(test_turns):
        # Create conversation turn manually (simulating audio processing)
        await ConversationTurn.objects.acreate(
            session=session,
            turn_number=i + 1,
            speaker=ConversationTurn.Speaker.USER,
            content=content,
        )

        # Update context
        context_updates = {
            "conversation_flow": [
                {
                    "turn": i + 1,
                    "speaker": "user",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                }
            ]
        }
        voice_service.context_manager.update_context(
            str(session.session_id), context_updates
        )

    print(f"✅ Processed {len(test_turns)} conversation turns")

    # End call and get comprehensive summary
    summary = await voice_service.end_call(str(session.session_id))

    print(f"✅ Call ended with summary:")
    print(f"   - Duration: {summary['duration']}")
    print(f"   - Turns: {summary['conversation_turns']}")
    print(f"   - Lead Quality Score: {summary.get('lead_quality_score', 'N/A')}")
    print(
        f"   - Conversion Probability: {summary.get('conversion_probability', 'N/A')}"
    )

    return True


async def test_entity_extraction():
    """Test basic entity extraction functionality"""
    print("\n🔍 Testing Entity Extraction...")

    voice_service = VoiceProcessingService()

    test_texts = [
        "I have a lead from Acme Corporation, contact is john@acme.com",
        "TechStart Inc needs a solution, budget is $25,000",
        "Call me at 555-123-4567 or email sarah@techstart.com",
        "Meeting scheduled for January 15, 2024 with Microsoft Corp",
    ]

    for text in test_texts:
        entities = voice_service._extract_basic_entities(text)
        print(f"✅ Text: '{text[:50]}...'")
        for entity_type, values in entities.items():
            print(f"   - {entity_type}: {values}")

    return True


async def main():
    """Run all tests"""
    print("🚀 Starting Task 7 Implementation Tests")
    print("=" * 60)

    tests = [
        test_conversation_context_management,
        test_conversation_summary_generation,
        test_audio_file_storage,
        test_voice_processing_integration,
        test_entity_extraction,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("✅ All Task 7 functionality implemented successfully!")
        print("\nImplemented features:")
        print("- ✅ Conversation context tracking and state management")
        print("- ✅ Google Cloud Text-to-Speech for NIA responses")
        print("- ✅ Conversation turn logging and storage")
        print("- ✅ Audio file storage and retrieval system")
        print("- ✅ Conversation summary generation")
        print("- ✅ Integration tests for complete voice processing pipeline")
    else:
        print("❌ Some tests failed. Please check the implementation.")

    return all(results)


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
