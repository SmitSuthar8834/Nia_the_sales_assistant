"""
Voice processing services for NIA Sales Assistant
"""

import asyncio
import io
import json
import logging
import time
from datetime import datetime
from typing import Dict, List

from aiortc import RTCPeerConnection, RTCSessionDescription
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from google.cloud import speech, texttospeech

from .models import AudioChunk, CallSession, ConversationTurn, VoiceConfiguration

User = get_user_model()
logger = logging.getLogger(__name__)


class ConversationSummaryService:
    """Service for generating conversation summaries and extracting lead information"""

    def __init__(self):
        # Import here to avoid circular imports
        try:
            import google.generativeai as genai

            self.genai = genai
            # Configure with API key from settings
            if hasattr(settings, "GEMINI_API_KEY"):
                genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = None
        except ImportError:
            logger.warning("Google Generative AI not available")
            self.genai = None

    @property
    def model(self):
        """Lazy-load Gemini model"""
        if self._model is None and self.genai:
            self._model = self.genai.GenerativeModel("gemini-pro")
        return self._model

    async def generate_conversation_summary(self, session_id: str) -> Dict:
        """Generate comprehensive conversation summary"""
        try:
            from asgiref.sync import sync_to_async

            # Get conversation turns
            session = await CallSession.objects.aget(session_id=session_id)

            @sync_to_async
            def get_turns():
                return list(
                    ConversationTurn.objects.filter(session=session).order_by(
                        "turn_number"
                    )
                )

            turns = await get_turns()

            if not turns:
                return {
                    "summary": "No conversation content available",
                    "lead_information": {},
                    "key_points": [],
                    "action_items": [],
                    "next_steps": [],
                }

            # Build conversation transcript
            transcript = []

            for turn in turns:
                speaker = (
                    "Sales Rep"
                    if turn.speaker == ConversationTurn.Speaker.USER
                    else "NIA"
                )
                transcript.append(f"{speaker}: {turn.content}")

            conversation_text = "\n".join(transcript)

            # Generate summary using AI
            if self.model:
                summary_data = await self._generate_ai_summary(conversation_text)
            else:
                summary_data = await self._generate_basic_summary(
                    conversation_text, turns
                )

            return summary_data

        except Exception as e:
            logger.error(f"Error generating conversation summary: {str(e)}")
            return {
                "error": str(e),
                "summary": "Error generating summary",
                "lead_information": {},
                "key_points": [],
                "action_items": [],
                "next_steps": [],
            }

    async def _generate_ai_summary(self, conversation_text: str) -> Dict:
        """Generate AI-powered conversation summary"""
        try:
            prompt = f"""
            Analyze this sales conversation and provide a comprehensive summary in JSON format:

            Conversation:
            {conversation_text}

            Please provide:
            1. A brief summary of the conversation
            2. Extracted lead information (company name, contact details, pain points, requirements, budget, timeline)
            3. Key discussion points
            4. Action items mentioned
            5. Suggested next steps for the sales representative

            Format the response as JSON with these keys:
            - summary: string
            - lead_information: object with company_name, contact_details, pain_points, requirements, budget_info, timeline
            - key_points: array of strings
            - action_items: array of strings  
            - next_steps: array of strings
            - lead_quality_score: number (0-100)
            - conversion_probability: number (0-1)
            """

            response = await self.model.generate_content_async(prompt)

            # Parse JSON response
            import json

            try:
                summary_data = json.loads(response.text)
                return summary_data
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                return {
                    "summary": response.text,
                    "lead_information": {},
                    "key_points": [],
                    "action_items": [],
                    "next_steps": [],
                    "lead_quality_score": 50,
                    "conversion_probability": 0.5,
                }

        except Exception as e:
            logger.error(f"Error generating AI summary: {str(e)}")
            return await self._generate_basic_summary(conversation_text, None)

    async def _generate_basic_summary(self, conversation_text: str, turns) -> Dict:
        """Generate basic summary without AI"""
        try:
            # Basic text analysis
            words = conversation_text.lower().split()
            word_count = len(words)

            # Extract potential company names (capitalized words)
            import re

            company_matches = re.findall(
                r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", conversation_text
            )

            # Extract potential contact information
            email_matches = re.findall(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                conversation_text,
            )
            phone_matches = re.findall(
                r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", conversation_text
            )

            # Basic keyword extraction for pain points
            pain_keywords = [
                "problem",
                "issue",
                "challenge",
                "difficulty",
                "struggle",
                "pain",
                "concern",
            ]
            pain_points = [word for word in words if word in pain_keywords]

            return {
                "summary": f"Conversation with {word_count} words. Potential lead discussion.",
                "lead_information": {
                    "company_name": company_matches[0] if company_matches else "",
                    "contact_details": {
                        "emails": email_matches,
                        "phones": phone_matches,
                    },
                    "pain_points": list(set(pain_points)),
                    "requirements": [],
                    "budget_info": {},
                    "timeline": "",
                },
                "key_points": company_matches[:3],
                "action_items": ["Follow up with lead"],
                "next_steps": ["Schedule follow-up call", "Send proposal"],
                "lead_quality_score": 50,
                "conversion_probability": 0.5,
            }

        except Exception as e:
            logger.error(f"Error generating basic summary: {str(e)}")
            return {
                "summary": "Error generating summary",
                "lead_information": {},
                "key_points": [],
                "action_items": [],
                "next_steps": [],
                "lead_quality_score": 0,
                "conversion_probability": 0.0,
            }


class ConversationContextManager:
    """Manages conversation context and state across turns"""

    def __init__(self):
        self.contexts: Dict[str, Dict] = {}

    def initialize_context(self, session_id: str, user_id: str) -> Dict:
        """Initialize conversation context for a session"""
        context = {
            "session_id": session_id,
            "user_id": user_id,
            "conversation_state": "greeting",
            "extracted_entities": {},
            "lead_information": {},
            "conversation_flow": [],
            "last_intent": None,
            "context_history": [],
            "current_topic": None,
            "pending_confirmations": [],
            "conversation_summary": {
                "key_points": [],
                "action_items": [],
                "lead_details": {},
                "next_steps": [],
            },
        }
        self.contexts[session_id] = context
        return context

    def update_context(self, session_id: str, updates: Dict) -> Dict:
        """Update conversation context with new information"""
        if session_id not in self.contexts:
            raise ValueError(f"Context for session {session_id} not found")

        context = self.contexts[session_id]

        # Update context with new information
        for key, value in updates.items():
            if key == "extracted_entities":
                context["extracted_entities"].update(value)
            elif key == "lead_information":
                context["lead_information"].update(value)
            elif key == "conversation_flow":
                context["conversation_flow"].extend(
                    value if isinstance(value, list) else [value]
                )
            elif key == "context_history":
                context["context_history"].extend(
                    value if isinstance(value, list) else [value]
                )
            elif key == "conversation_summary":
                for summary_key, summary_value in value.items():
                    if isinstance(
                        context["conversation_summary"].get(summary_key), list
                    ):
                        context["conversation_summary"][summary_key].extend(
                            summary_value
                            if isinstance(summary_value, list)
                            else [summary_value]
                        )
                    else:
                        context["conversation_summary"][summary_key] = summary_value
            else:
                context[key] = value

        return context

    def get_context(self, session_id: str) -> Dict:
        """Get conversation context for a session"""
        return self.contexts.get(session_id, {})

    def clear_context(self, session_id: str):
        """Clear conversation context for ended session"""
        if session_id in self.contexts:
            del self.contexts[session_id]


class VoiceProcessingService:
    """Main service for handling voice call processing"""

    def __init__(self):
        self._speech_client = None
        self._tts_client = None
        self.active_sessions: Dict[str, CallSession] = {}
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.context_manager = ConversationContextManager()
        self.summary_service = ConversationSummaryService()
        self.audio_storage = AudioFileStorageService()

    @property
    def speech_client(self):
        """Lazy-load speech client"""
        if self._speech_client is None:
            self._speech_client = speech.SpeechClient()
        return self._speech_client

    @property
    def tts_client(self):
        """Lazy-load TTS client"""
        if self._tts_client is None:
            self._tts_client = texttospeech.TextToSpeechClient()
        return self._tts_client

    async def initiate_call(self, user_id: str, caller_id: str = "") -> CallSession:
        """Initialize a new voice call session"""
        try:
            user = await User.objects.aget(id=user_id)

            # Create new call session
            session = await CallSession.objects.acreate(
                user=user,
                caller_id=caller_id,
                status=CallSession.Status.ACTIVE,
                conversation_context={},
                session_metadata={
                    "initiated_at": timezone.now().isoformat(),
                    "caller_id": caller_id,
                },
            )

            # Initialize conversation context
            context = self.context_manager.initialize_context(
                str(session.session_id), str(user_id)
            )

            # Update session with initial context
            session.conversation_context = context
            await session.asave()

            # Store in active sessions
            self.active_sessions[str(session.session_id)] = session

            logger.info(
                f"Initiated call session {session.session_id} for user {user.username}"
            )
            return session

        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            raise ValueError(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            raise

    async def setup_webrtc_connection(self, session_id: str, offer: dict) -> dict:
        """Setup WebRTC peer connection for voice call"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Create peer connection
            pc = RTCPeerConnection()
            self.peer_connections[session_id] = pc

            # Handle incoming audio track
            @pc.on("track")
            async def on_track(track):
                logger.info(f"Received {track.kind} track for session {session_id}")
                if track.kind == "audio":
                    # Start processing audio stream
                    asyncio.create_task(self._process_audio_track(session_id, track))

            # Set remote description
            await pc.setRemoteDescription(
                RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
            )

            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

        except Exception as e:
            logger.error(f"Error setting up WebRTC connection: {str(e)}")
            raise

    async def _process_audio_track(self, session_id: str, track):
        """Process incoming audio track from WebRTC"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            chunk_number = 0

            async for frame in track:
                # Convert audio frame to bytes
                audio_data = frame.to_ndarray().tobytes()

                # Store audio chunk
                await AudioChunk.objects.acreate(
                    session=session,
                    chunk_number=chunk_number,
                    audio_data=audio_data,
                    audio_format="pcm",
                    sample_rate=16000,
                    duration_ms=len(audio_data) // 32,  # Approximate duration
                )

                # Process chunk for transcription
                asyncio.create_task(
                    self._transcribe_audio_chunk(session_id, chunk_number)
                )

                chunk_number += 1

        except Exception as e:
            logger.error(f"Error processing audio track: {str(e)}")

    async def process_audio_stream(self, session_id: str, audio_data: bytes) -> dict:
        """Process incoming audio stream and return transcription"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Get user's voice configuration
            try:
                voice_config = await VoiceConfiguration.objects.aget(user=session.user)
            except VoiceConfiguration.DoesNotExist:
                # Create default configuration
                voice_config = await VoiceConfiguration.objects.acreate(
                    user=session.user
                )

            # Configure speech recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=voice_config.language_code,
                enable_automatic_punctuation=voice_config.enable_automatic_punctuation,
                enable_word_time_offsets=voice_config.enable_word_time_offsets,
            )

            # Add speech contexts if available
            if voice_config.speech_contexts:
                config.speech_contexts = [
                    speech.SpeechContext(phrases=voice_config.speech_contexts)
                ]

            # Create audio object
            audio = speech.RecognitionAudio(content=audio_data)

            # Perform speech recognition
            response = self.speech_client.recognize(config=config, audio=audio)

            # Process results
            transcription = ""
            confidence = 0.0

            if response.results:
                result = response.results[0]
                if result.alternatives:
                    alternative = result.alternatives[0]
                    transcription = alternative.transcript
                    confidence = alternative.confidence

            # Store conversation turn
            turn_count = await ConversationTurn.objects.filter(session=session).acount()
            conversation_turn = await ConversationTurn.objects.acreate(
                session=session,
                turn_number=turn_count + 1,
                speaker=ConversationTurn.Speaker.USER,
                content=transcription,
                confidence_score=confidence,
                processing_time_ms=int(time.time() * 1000),
            )

            # Store audio file
            audio_file_path = await self.audio_storage.store_audio_file(
                session_id,
                audio_data,
                "wav",
                {
                    "turn_number": turn_count + 1,
                    "speaker": "user",
                    "confidence": confidence,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            # Update conversation turn with audio URL
            conversation_turn.audio_url = audio_file_path
            await conversation_turn.asave()

            # Update conversation context
            context_updates = {
                "conversation_flow": [
                    {
                        "turn": turn_count + 1,
                        "speaker": "user",
                        "content": transcription,
                        "timestamp": timezone.now().isoformat(),
                    }
                ],
                "last_intent": "user_input",
            }

            # Basic entity extraction (can be enhanced with NLP)
            entities = self._extract_basic_entities(transcription)
            if entities:
                context_updates["extracted_entities"] = entities

            self.context_manager.update_context(session_id, context_updates)

            return {
                "transcription": transcription,
                "confidence": confidence,
                "session_id": session_id,
                "timestamp": timezone.now().isoformat(),
                "audio_file_path": audio_file_path,
                "entities": entities,
            }

        except Exception as e:
            logger.error(f"Error processing audio stream: {str(e)}")
            return {
                "error": str(e),
                "session_id": session_id,
                "timestamp": timezone.now().isoformat(),
            }

    async def _transcribe_audio_chunk(self, session_id: str, chunk_number: int):
        """Transcribe a specific audio chunk"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # Get audio chunk
            chunk = await AudioChunk.objects.aget(
                session=session, chunk_number=chunk_number
            )

            if chunk.is_processed:
                return

            # Process transcription
            result = await self.process_audio_stream(session_id, chunk.audio_data)

            # Update chunk with transcription
            chunk.transcription = result.get("transcription", "")
            chunk.confidence_score = result.get("confidence", 0.0)
            chunk.is_processed = True
            await chunk.asave()

        except Exception as e:
            logger.error(f"Error transcribing audio chunk: {str(e)}")

    def _extract_basic_entities(self, text: str) -> Dict:
        """Extract basic entities from text"""
        try:
            import re

            entities = {}

            # Extract potential company names (capitalized words)
            company_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Ltd|Company)\.?)?\b"
            companies = re.findall(company_pattern, text)
            if companies:
                entities["companies"] = list(set(companies))

            # Extract email addresses
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            emails = re.findall(email_pattern, text)
            if emails:
                entities["emails"] = emails

            # Extract phone numbers
            phone_pattern = r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
            phones = re.findall(phone_pattern, text)
            if phones:
                entities["phones"] = ["-".join(phone) for phone in phones]

            # Extract monetary amounts
            money_pattern = r"\$[\d,]+(?:\.\d{2})?"
            amounts = re.findall(money_pattern, text)
            if amounts:
                entities["monetary_amounts"] = amounts

            # Extract dates
            date_pattern = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
            dates = re.findall(date_pattern, text)
            if dates:
                entities["dates"] = dates

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {}

    async def generate_speech_response(self, text: str, session_id: str) -> bytes:
        """Generate audio response using Text-to-Speech"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Get user's voice configuration
            try:
                voice_config = await VoiceConfiguration.objects.aget(user=session.user)
            except VoiceConfiguration.DoesNotExist:
                voice_config = await VoiceConfiguration.objects.acreate(
                    user=session.user
                )

            # Configure synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config.language_code, name=voice_config.voice_name
            )

            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=voice_config.speaking_rate,
                pitch=voice_config.pitch,
                volume_gain_db=voice_config.volume_gain_db,
            )

            # Perform text-to-speech
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Store conversation turn
            turn_count = await ConversationTurn.objects.filter(session=session).acount()
            conversation_turn = await ConversationTurn.objects.acreate(
                session=session,
                turn_number=turn_count + 1,
                speaker=ConversationTurn.Speaker.NIA,
                content=text,
                processing_time_ms=int(time.time() * 1000),
            )

            # Store audio response file
            audio_file_path = await self.audio_storage.store_audio_file(
                session_id,
                response.audio_content,
                "wav",
                {
                    "turn_number": turn_count + 1,
                    "speaker": "nia",
                    "text": text,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            # Update conversation turn with audio URL
            conversation_turn.audio_url = audio_file_path
            await conversation_turn.asave()

            # Update conversation context
            context_updates = {
                "conversation_flow": [
                    {
                        "turn": turn_count + 1,
                        "speaker": "nia",
                        "content": text,
                        "timestamp": timezone.now().isoformat(),
                    }
                ],
                "last_intent": "nia_response",
            }

            self.context_manager.update_context(session_id, context_updates)

            return response.audio_content

        except Exception as e:
            logger.error(f"Error generating speech response: {str(e)}")
            raise

    async def end_call(self, session_id: str) -> dict:
        """End call session and return comprehensive summary"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                # Try to get from database
                try:
                    session = await CallSession.objects.aget(session_id=session_id)
                except CallSession.DoesNotExist:
                    raise ValueError(f"Session {session_id} not found")

            # Update session status
            session.status = CallSession.Status.ENDED
            session.end_time = timezone.now()
            session.call_duration = session.end_time - session.start_time

            # Generate comprehensive conversation summary
            conversation_summary = (
                await self.summary_service.generate_conversation_summary(session_id)
            )

            # Update session with final conversation context and summary
            final_context = self.context_manager.get_context(session_id)
            final_context["conversation_summary"] = conversation_summary
            session.conversation_context = final_context

            await session.asave()

            # Close WebRTC connection if exists
            if session_id in self.peer_connections:
                await self.peer_connections[session_id].close()
                del self.peer_connections[session_id]

            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

            # Clear conversation context
            self.context_manager.clear_context(session_id)

            # Get conversation statistics
            conversation_turns = await ConversationTurn.objects.filter(
                session=session
            ).acount()

            audio_chunks = await AudioChunk.objects.filter(session=session).acount()

            # Get audio files
            audio_files = await self.audio_storage.get_session_audio_files(session_id)

            # Prepare comprehensive summary
            summary = {
                "session_id": session_id,
                "duration": str(session.call_duration),
                "conversation_turns": conversation_turns,
                "audio_chunks_processed": audio_chunks,
                "audio_files_stored": len(audio_files),
                "end_time": session.end_time.isoformat(),
                "status": session.status,
                "conversation_summary": conversation_summary,
                "lead_information": conversation_summary.get("lead_information", {}),
                "key_points": conversation_summary.get("key_points", []),
                "action_items": conversation_summary.get("action_items", []),
                "next_steps": conversation_summary.get("next_steps", []),
                "lead_quality_score": conversation_summary.get("lead_quality_score", 0),
                "conversion_probability": conversation_summary.get(
                    "conversion_probability", 0.0
                ),
            }

            logger.info(f"Ended call session {session_id} with comprehensive summary")
            return summary

        except Exception as e:
            logger.error(f"Error ending call: {str(e)}")
            raise

    async def get_session_status(self, session_id: str) -> dict:
        """Get current status of a call session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                # Try to get from database
                try:
                    session = await CallSession.objects.aget(session_id=session_id)
                except CallSession.DoesNotExist:
                    raise ValueError(f"Session {session_id} not found")

            return {
                "session_id": session_id,
                "status": session.status,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "duration": (
                    str(session.call_duration) if session.call_duration else None
                ),
                "user": session.user.username,
            }

        except Exception as e:
            logger.error(f"Error getting session status: {str(e)}")
            raise

    async def get_conversation_context(self, session_id: str) -> dict:
        """Get current conversation context for a session"""
        try:
            context = self.context_manager.get_context(session_id)
            if not context:
                # Try to get from database
                try:
                    session = await CallSession.objects.aget(session_id=session_id)
                    context = session.conversation_context or {}
                except CallSession.DoesNotExist:
                    raise ValueError(f"Session {session_id} not found")

            return context

        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            raise

    async def get_conversation_summary(self, session_id: str) -> dict:
        """Get conversation summary for a session"""
        try:
            return await self.summary_service.generate_conversation_summary(session_id)

        except Exception as e:
            logger.error(f"Error getting conversation summary: {str(e)}")
            raise


class AudioFileStorageService:
    """Service for storing and retrieving audio files"""

    def __init__(self):
        self.storage_path = getattr(settings, "AUDIO_STORAGE_PATH", "media/audio/")
        import os

        os.makedirs(self.storage_path, exist_ok=True)

    async def store_audio_file(
        self,
        session_id: str,
        audio_data: bytes,
        file_type: str = "wav",
        metadata: Dict = None,
    ) -> str:
        """Store audio file and return file path"""
        try:
            import os
            from datetime import datetime

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session_id}_{timestamp}.{file_type}"
            file_path = os.path.join(self.storage_path, filename)

            # Write audio data to file
            with open(file_path, "wb") as f:
                f.write(audio_data)

            # Store metadata if provided
            if metadata:
                metadata_path = file_path.replace(f".{file_type}", "_metadata.json")
                import json

                with open(metadata_path, "w") as f:
                    json.dump(metadata, f)

            logger.info(f"Stored audio file: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error storing audio file: {str(e)}")
            raise

    async def retrieve_audio_file(self, file_path: str) -> bytes:
        """Retrieve audio file data"""
        try:
            import os

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            with open(file_path, "rb") as f:
                return f.read()

        except Exception as e:
            logger.error(f"Error retrieving audio file: {str(e)}")
            raise

    async def get_session_audio_files(self, session_id: str) -> List[str]:
        """Get all audio files for a session"""
        try:
            import glob
            import os

            pattern = os.path.join(self.storage_path, f"{session_id}_*.wav")
            files = glob.glob(pattern)
            return sorted(files)

        except Exception as e:
            logger.error(f"Error getting session audio files: {str(e)}")
            return []

    async def delete_session_audio_files(self, session_id: str):
        """Delete all audio files for a session"""
        try:
            files = await self.get_session_audio_files(session_id)
            import os

            for file_path in files:
                if os.path.exists(file_path):
                    os.remove(file_path)

                # Also remove metadata file if exists
                metadata_path = file_path.replace(".wav", "_metadata.json")
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)

            logger.info(f"Deleted {len(files)} audio files for session {session_id}")

        except Exception as e:
            logger.error(f"Error deleting session audio files: {str(e)}")


class AudioBufferManager:
    """Manages audio buffering for real-time processing"""

    def __init__(self, buffer_size: int = 4096):
        self.buffer_size = buffer_size
        self.buffers: Dict[str, io.BytesIO] = {}
        self.buffer_locks: Dict[str, asyncio.Lock] = {}

    async def add_audio_data(self, session_id: str, audio_data: bytes):
        """Add audio data to session buffer"""
        if session_id not in self.buffers:
            self.buffers[session_id] = io.BytesIO()
            self.buffer_locks[session_id] = asyncio.Lock()

        async with self.buffer_locks[session_id]:
            self.buffers[session_id].write(audio_data)

    async def get_buffered_audio(
        self, session_id: str, chunk_size: int = None
    ) -> bytes:
        """Get buffered audio data"""
        if session_id not in self.buffers:
            return b""

        chunk_size = chunk_size or self.buffer_size

        async with self.buffer_locks[session_id]:
            buffer = self.buffers[session_id]
            buffer.seek(0)
            data = buffer.read(chunk_size)

            # Keep remaining data in buffer
            remaining = buffer.read()
            buffer.seek(0)
            buffer.truncate()
            buffer.write(remaining)

            return data

    async def clear_buffer(self, session_id: str):
        """Clear audio buffer for session"""
        if session_id in self.buffers:
            async with self.buffer_locks[session_id]:
                self.buffers[session_id].seek(0)
                self.buffers[session_id].truncate()

    def remove_session_buffer(self, session_id: str):
        """Remove buffer for ended session"""
        if session_id in self.buffers:
            del self.buffers[session_id]
        if session_id in self.buffer_locks:
            del self.buffer_locks[session_id]


# Global instances
voice_service = VoiceProcessingService()
audio_buffer_manager = AudioBufferManager()
conversation_summary_service = ConversationSummaryService()
audio_storage_service = AudioFileStorageService()
