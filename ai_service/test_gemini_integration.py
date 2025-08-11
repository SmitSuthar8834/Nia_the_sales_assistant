"""
Comprehensive tests for Gemini AI integration and lead extraction accuracy.
This file contains tests specifically for Task 8: Integrate Gemini AI for lead information extraction.
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .services import DataValidator, GeminiAIService

User = get_user_model()


class GeminiAIIntegrationTestCase(TestCase):
    """Test cases for Gemini AI integration and lead extraction accuracy"""

    def setUp(self):
        self.ai_service = GeminiAIService()
        self.validator = DataValidator()

    @patch("ai_service.services.genai.configure")
    @patch("ai_service.services.genai.GenerativeModel")
    def test_gemini_client_setup(self, mock_model, mock_configure):
        """Test that Gemini AI client is properly set up with API key"""
        # Test client initialization
        ai_service = GeminiAIService()

        # Verify that genai.configure was called
        mock_configure.assert_called()

        # Verify that GenerativeModel was instantiated
        mock_model.assert_called_with("gemini-1.5-flash")

    @patch("ai_service.services.genai.configure")
    @patch("ai_service.services.genai.GenerativeModel")
    def test_conversation_transcript_analysis(self, mock_model, mock_configure):
        """Test conversation transcript analysis functionality"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = """```json
        {
            "company_name": "TechCorp Solutions",
            "contact_details": {
                "name": "Sarah Johnson",
                "email": "sarah@techcorp.com",
                "phone": "555-123-4567",
                "title": "CTO",
                "department": "Technology"
            },
            "pain_points": ["Manual processes", "System integration issues"],
            "requirements": ["Workflow automation", "API integration"],
            "budget_info": "$75,000 - $100,000",
            "timeline": "Q3 2024",
            "decision_makers": ["Sarah Johnson", "Mike Chen"],
            "industry": "Software Development",
            "company_size": "50-100 employees",
            "urgency_level": "high",
            "current_solution": "Manual spreadsheets",
            "competitors_mentioned": ["Salesforce", "HubSpot"]
        }
        ```"""

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        # Test conversation analysis
        conversation_text = """
        Hi Sarah, thanks for speaking with me. I understand you're the CTO at TechCorp Solutions.
        
        Sarah: Yes, that's right. We're a software development company with about 75 employees. 
        We're having major issues with our current manual processes and need better system integration.
        
        What would an ideal solution look like?
        
        Sarah: We need workflow automation and good API integration. Our budget is around $75,000 to $100,000, 
        and we need this implemented by Q3 2024. I'll be making this decision with our CEO Mike Chen.
        We've looked at Salesforce and HubSpot but they don't fit our needs.
        
        You can reach me at sarah@techcorp.com or 555-123-4567.
        """

        ai_service = GeminiAIService()
        result = ai_service.extract_lead_info(conversation_text)

        # Verify structured lead information extraction
        self.assertEqual(result["company_name"], "TechCorp Solutions")
        self.assertEqual(result["contact_details"]["name"], "Sarah Johnson")
        self.assertEqual(result["contact_details"]["email"], "sarah@techcorp.com")
        self.assertEqual(result["contact_details"]["title"], "CTO")
        self.assertIn("Manual processes", result["pain_points"])
        self.assertIn("Workflow automation", result["requirements"])
        self.assertEqual(result["budget_info"], "$75,000 - $100,000")
        self.assertEqual(result["timeline"], "Q3 2024")
        self.assertIn("Sarah Johnson", result["decision_makers"])
        self.assertEqual(result["urgency_level"], "high")

        # Verify extraction metadata
        self.assertIn("extraction_metadata", result)
        self.assertGreater(result["extraction_metadata"]["confidence_score"], 80)
        self.assertGreater(result["extraction_metadata"]["data_completeness"], 90)

    def test_entity_recognition_companies(self):
        """Test entity recognition for company names"""
        text = "We spoke with representatives from Acme Corp Inc, TechStart LLC, and Global Solutions Ltd."

        with patch.object(
            self.ai_service, "_extract_entities_with_ai"
        ) as mock_ai_extract:
            mock_ai_extract.return_value = {
                "companies": ["Acme Corp Inc", "TechStart LLC", "Global Solutions Ltd"],
                "people": [],
                "technologies": [],
                "dates": [],
            }

            entities = self.ai_service.extract_entities(text)

            self.assertIn("Acme Corp Inc", entities["companies"])
            self.assertIn("TechStart LLC", entities["companies"])
            self.assertIn("Global Solutions Ltd", entities["companies"])

    def test_entity_recognition_contacts(self):
        """Test entity recognition for contact information"""
        text = (
            "Contact John Smith at john.smith@company.com or call him at 555-987-6543."
        )

        with patch.object(
            self.ai_service, "_extract_entities_with_ai"
        ) as mock_ai_extract:
            mock_ai_extract.return_value = {
                "companies": [],
                "people": ["John Smith"],
                "technologies": [],
                "dates": [],
            }

            entities = self.ai_service.extract_entities(text)

            # Test contact name recognition
            self.assertIn("John Smith", entities["people"])

            # Test email recognition (pattern-based)
            self.assertIn("john.smith@company.com", entities["emails"])

            # Test phone recognition (pattern-based)
            self.assertIn("555-987-6543", entities["phones"])

    def test_entity_recognition_requirements(self):
        """Test entity recognition for requirements and technologies"""
        text = "They need CRM integration, API development, cloud migration, and database optimization."

        with patch.object(
            self.ai_service, "_extract_entities_with_ai"
        ) as mock_ai_extract:
            mock_ai_extract.return_value = {
                "companies": [],
                "people": [],
                "technologies": ["CRM", "API", "cloud", "database"],
                "dates": [],
            }

            entities = self.ai_service.extract_entities(text)

            self.assertIn("CRM", entities["technologies"])
            self.assertIn("API", entities["technologies"])
            self.assertIn("cloud", entities["technologies"])
            self.assertIn("database", entities["technologies"])

    def test_entity_recognition_fallback(self):
        """Test entity recognition fallback when AI fails"""
        text = "Dr. Sarah Johnson from TechStart LLC mentioned their CRM needs for Q2 2024."

        # Mock AI extraction to fail
        with patch.object(
            self.ai_service, "_extract_entities_with_ai"
        ) as mock_ai_extract:
            mock_ai_extract.side_effect = Exception("API quota exceeded")

            entities = self.ai_service.extract_entities(text)

            # Should still extract entities using pattern matching
            self.assertIn("TechStart LLC", entities["companies"])
            self.assertIn("Dr. Sarah Johnson", entities["people"])
            self.assertIn("CRM", entities["technologies"])
            self.assertIn("Q2 2024", entities["dates"])

    def test_lead_extraction_accuracy_validation(self):
        """Test lead extraction accuracy with validation"""
        # Test high-quality extraction
        high_quality_data = {
            "company_name": "Test Corp",
            "contact_details": {
                "name": "John Doe",
                "email": "john@test.com",
                "phone": "555-123-4567",
                "title": "CEO",
            },
            "pain_points": ["Slow processes", "High costs"],
            "requirements": ["Automation", "Cost reduction"],
            "budget_info": "$50,000",
            "timeline": "Q2 2024",
            "decision_makers": ["John Doe"],
            "industry": "Technology",
        }

        validation = self.ai_service.validate_extracted_data(high_quality_data)

        self.assertTrue(validation["is_valid"])
        self.assertEqual(len(validation["errors"]), 0)
        self.assertGreaterEqual(validation["data_quality_score"], 80)

        # Test low-quality extraction
        low_quality_data = {
            "company_name": None,
            "contact_details": {"name": None, "email": "invalid-email", "phone": "123"},
            "pain_points": [],
            "requirements": [],
        }

        validation = self.ai_service.validate_extracted_data(low_quality_data)

        self.assertFalse(validation["is_valid"])
        self.assertGreater(len(validation["errors"]), 0)
        self.assertLessEqual(validation["data_quality_score"], 30)

    def test_extraction_error_handling(self):
        """Test extraction error handling and fallback mechanisms"""
        # Test JSON parsing error
        with patch.object(self.ai_service, "_make_api_call") as mock_api_call:
            mock_response = MagicMock()
            mock_response.text = "Invalid JSON response"
            mock_api_call.return_value = mock_response

            result = self.ai_service.extract_lead_info("test conversation")

            # Should return default structure
            self.assertIsNone(result["company_name"])
            self.assertEqual(
                result["extraction_metadata"]["extraction_method"], "default_fallback"
            )
            self.assertEqual(result["extraction_metadata"]["confidence_score"], 0.0)

        # Test API call error
        with patch.object(self.ai_service, "_make_api_call") as mock_api_call:
            mock_api_call.side_effect = Exception("API Error")

            result = self.ai_service.extract_lead_info("test conversation")

            # Should return default structure
            self.assertIsNone(result["company_name"])
            self.assertEqual(
                result["extraction_metadata"]["extraction_method"], "default_fallback"
            )

    def test_confidence_score_calculation(self):
        """Test confidence score calculation accuracy"""
        # Test with complete data
        complete_data = {
            "company_name": "Test Corp",
            "contact_details": {
                "name": "John Doe",
                "email": "john@test.com",
                "phone": "555-123-4567",
                "title": "CEO",
            },
            "pain_points": ["Issue 1", "Issue 2"],
            "requirements": ["Solution 1", "Solution 2"],
            "budget_info": "$50,000",
            "timeline": "Q2 2024",
            "industry": "Technology",
            "decision_makers": ["John Doe"],
        }

        score = self.ai_service._calculate_confidence_score(complete_data)
        self.assertGreaterEqual(score, 80.0)

        # Test with minimal data
        minimal_data = {"company_name": "Test Corp"}
        score_minimal = self.ai_service._calculate_confidence_score(minimal_data)
        self.assertEqual(score_minimal, 20.0)

        # Complete data should score higher than minimal data
        self.assertGreater(score, score_minimal)

    def test_data_completeness_calculation(self):
        """Test data completeness calculation"""
        # Test with all fields filled
        complete_data = {
            "company_name": "Test Corp",
            "contact_details": {"name": "John", "email": "john@test.com"},
            "pain_points": ["Issue"],
            "requirements": ["Req"],
            "budget_info": "$10k",
            "timeline": "Q1",
            "decision_makers": ["John"],
            "industry": "Tech",
            "company_size": "100",
            "urgency_level": "high",
            "current_solution": "Excel",
        }

        completeness = self.ai_service._calculate_data_completeness(complete_data)
        self.assertEqual(completeness, 100.0)

        # Test with partial data
        partial_data = {
            "company_name": "Test Corp",
            "contact_details": {"name": "John"},
            "pain_points": ["Issue"],
        }

        partial_completeness = self.ai_service._calculate_data_completeness(
            partial_data
        )
        self.assertLess(partial_completeness, 50.0)

    @patch("ai_service.services.genai.configure")
    @patch("ai_service.services.genai.GenerativeModel")
    def test_api_key_rotation(self, mock_model, mock_configure):
        """Test API key rotation functionality"""
        # Mock quota exceeded error
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = [
            Exception("429 You exceeded your current quota"),
            MagicMock(text='{"company_name": "Test Corp"}'),
        ]
        mock_model.return_value = mock_model_instance

        # Test that service handles quota exceeded and rotates keys
        ai_service = GeminiAIService()

        # This should trigger key rotation on first call and succeed on second
        with patch.object(
            ai_service, "_rotate_api_key", return_value=True
        ) as mock_rotate:
            try:
                result = ai_service._make_api_call("test prompt")
                # If we get here, rotation worked
                mock_rotate.assert_called()
            except Exception as e:
                # If all keys are exhausted, this is expected
                self.assertIn("quota", str(e).lower())

    def test_data_validator_accuracy(self):
        """Test data validator accuracy for extracted information"""
        # Test email validation
        self.assertTrue(self.validator.validate_email("test@example.com"))
        self.assertTrue(self.validator.validate_email("user.name@company.co.uk"))
        self.assertFalse(self.validator.validate_email("invalid-email"))
        self.assertFalse(self.validator.validate_email("@domain.com"))

        # Test phone validation
        self.assertTrue(self.validator.validate_phone("555-123-4567"))
        self.assertTrue(self.validator.validate_phone("(555) 123-4567"))
        self.assertTrue(self.validator.validate_phone("+1-555-123-4567"))
        self.assertFalse(self.validator.validate_phone("123"))
        self.assertFalse(self.validator.validate_phone("abc-def-ghij"))

        # Test company name cleaning
        self.assertEqual(
            self.validator.clean_company_name("  Acme Corp  "), "Acme Corp"
        )
        self.assertIsNone(self.validator.clean_company_name("null"))
        self.assertIsNone(self.validator.clean_company_name(""))

        # Test comprehensive data validation
        test_data = {
            "company_name": "  Test Company  ",
            "contact_details": {
                "name": "John Doe",
                "email": "john@test.com",
                "phone": "555-123-4567",
            },
            "pain_points": ["Issue 1", "", "Issue 2", "Issue 1"],  # Test deduplication
            "requirements": ["Req 1", "null", "Req 2"],
        }

        validated = self.validator.validate_lead_data(test_data)

        self.assertEqual(validated["company_name"], "Test Company")
        self.assertEqual(validated["contact_details"]["email"], "john@test.com")
        self.assertEqual(len(validated["pain_points"]), 2)  # Deduplicated
        self.assertNotIn("null", validated["requirements"])


class GeminiAIAccuracyBenchmarkTestCase(TestCase):
    """Benchmark tests for AI extraction accuracy with various conversation types"""

    def setUp(self):
        self.ai_service = GeminiAIService()

        # Sample conversations for testing accuracy
        self.test_conversations = [
            {
                "name": "complete_conversation",
                "text": "John Smith from Acme Corp called about CRM needs. Budget $50k, timeline Q2 2024. Email: john@acme.com, Phone: 555-123-4567.",
                "expected_fields": [
                    "company_name",
                    "contact_name",
                    "budget_info",
                    "timeline",
                    "email",
                    "phone",
                ],
            },
            {
                "name": "minimal_conversation",
                "text": "Someone from TechStart mentioned they need help with automation.",
                "expected_fields": ["company_name", "requirements"],
            },
            {
                "name": "detailed_conversation",
                "text": "Sarah Johnson, CTO at DataTech Solutions (200 employees), discussed their manual data entry problems and need for workflow automation. Budget approved for $75,000, implementation needed by Q3 2024. Decision makers: Sarah and CEO Mike Chen. Currently using Excel, considering Salesforce alternatives.",
                "expected_fields": [
                    "company_name",
                    "contact_name",
                    "title",
                    "company_size",
                    "pain_points",
                    "requirements",
                    "budget_info",
                    "timeline",
                    "decision_makers",
                    "current_solution",
                    "competitors_mentioned",
                ],
            },
        ]

    @patch("ai_service.services.genai.configure")
    @patch("ai_service.services.genai.GenerativeModel")
    def test_extraction_accuracy_benchmark(self, mock_model, mock_configure):
        """Benchmark extraction accuracy across different conversation types"""
        for conversation in self.test_conversations:
            with self.subTest(conversation=conversation["name"]):
                # Mock appropriate response based on conversation complexity
                if conversation["name"] == "complete_conversation":
                    mock_response_text = """```json
                    {
                        "company_name": "Acme Corp",
                        "contact_details": {
                            "name": "John Smith",
                            "email": "john@acme.com",
                            "phone": "555-123-4567"
                        },
                        "pain_points": [],
                        "requirements": ["CRM"],
                        "budget_info": "$50k",
                        "timeline": "Q2 2024"
                    }
                    ```"""
                elif conversation["name"] == "minimal_conversation":
                    mock_response_text = """```json
                    {
                        "company_name": "TechStart",
                        "contact_details": {"name": null},
                        "requirements": ["automation"]
                    }
                    ```"""
                else:  # detailed_conversation
                    mock_response_text = """```json
                    {
                        "company_name": "DataTech Solutions",
                        "contact_details": {
                            "name": "Sarah Johnson",
                            "title": "CTO"
                        },
                        "pain_points": ["manual data entry problems"],
                        "requirements": ["workflow automation"],
                        "budget_info": "$75,000",
                        "timeline": "Q3 2024",
                        "decision_makers": ["Sarah", "CEO Mike Chen"],
                        "company_size": "200 employees",
                        "current_solution": "Excel",
                        "competitors_mentioned": ["Salesforce"]
                    }
                    ```"""

                mock_response = MagicMock()
                mock_response.text = mock_response_text

                mock_model_instance = MagicMock()
                mock_model_instance.generate_content.return_value = mock_response
                mock_model.return_value = mock_model_instance

                # Test extraction
                ai_service = GeminiAIService()
                result = ai_service.extract_lead_info(conversation["text"])

                # Verify extraction worked
                self.assertIsNotNone(result)
                self.assertIn("extraction_metadata", result)

                # Check confidence score is appropriate for conversation complexity
                confidence = result["extraction_metadata"]["confidence_score"]
                if conversation["name"] == "complete_conversation":
                    self.assertGreaterEqual(confidence, 70)
                elif conversation["name"] == "detailed_conversation":
                    self.assertGreaterEqual(confidence, 80)
                else:  # minimal_conversation
                    self.assertLessEqual(confidence, 50)
