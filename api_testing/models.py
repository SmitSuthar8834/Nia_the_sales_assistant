"""
Models for Dynamic API Testing Platform

This module provides models for storing API test configurations,
authentication flows, and test results with focus on AI core functionality.
"""

import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class APITestCollection(models.Model):
    """Collection of related API tests (e.g., AI Core Tests, CRM Integration Tests)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255, help_text="Collection name (e.g., 'AI Core Tests')"
    )
    description = models.TextField(
        blank=True, help_text="Description of the test collection"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="test_collections"
    )
    is_ai_core = models.BooleanField(
        default=False, help_text="Mark as AI core functionality test"
    )
    is_public = models.BooleanField(
        default=False, help_text="Make collection available to all users"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["created_by", "is_ai_core"]),
            models.Index(fields=["is_public", "is_ai_core"]),
        ]

    def __str__(self):
        return f"{self.name} ({'AI Core' if self.is_ai_core else 'General'})"


class APITestCase(models.Model):
    """Individual API test case with request/response configuration"""

    class HTTPMethod(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"
        OPTIONS = "OPTIONS", "OPTIONS"
        HEAD = "HEAD", "HEAD"

    class AuthType(models.TextChoices):
        NONE = "none", "No Authentication"
        BEARER = "bearer", "Bearer Token"
        BASIC = "basic", "Basic Auth"
        API_KEY = "api_key", "API Key"
        OAUTH2 = "oauth2", "OAuth 2.0"
        SESSION = "session", "Session Cookies"
        CUSTOM = "custom", "Custom Headers"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(
        APITestCollection, on_delete=models.CASCADE, related_name="test_cases"
    )
    name = models.CharField(max_length=255, help_text="Test case name")
    description = models.TextField(blank=True, help_text="Test case description")

    # Request Configuration
    url = models.URLField(help_text="API endpoint URL")
    method = models.CharField(
        max_length=10, choices=HTTPMethod.choices, default=HTTPMethod.GET
    )
    headers = models.JSONField(default=dict, help_text="Request headers as JSON")
    query_params = models.JSONField(default=dict, help_text="Query parameters as JSON")
    request_body = models.TextField(
        blank=True, help_text="Request body (JSON, XML, etc.)"
    )

    # Authentication Configuration
    auth_type = models.CharField(
        max_length=20, choices=AuthType.choices, default=AuthType.NONE
    )
    auth_config = models.JSONField(
        default=dict, help_text="Authentication configuration"
    )

    # Test Configuration
    expected_status_code = models.IntegerField(
        default=200, help_text="Expected HTTP status code"
    )
    expected_response_schema = models.JSONField(
        default=dict, blank=True, help_text="Expected response schema"
    )
    response_assertions = models.JSONField(
        default=list, help_text="Response validation rules"
    )

    # Execution Order and Dependencies
    execution_order = models.IntegerField(
        default=0, help_text="Order of execution in collection"
    )
    depends_on = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Test case this depends on",
    )

    # Data Extraction for Chaining
    extract_data = models.JSONField(
        default=dict, help_text="Data to extract from response for next calls"
    )

    # Metadata
    is_active = models.BooleanField(
        default=True, help_text="Whether this test is active"
    )
    timeout_seconds = models.IntegerField(
        default=30, help_text="Request timeout in seconds"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["collection", "execution_order", "name"]
        indexes = [
            models.Index(fields=["collection", "execution_order"]),
            models.Index(fields=["collection", "is_active"]),
        ]

    def __str__(self):
        return f"{self.collection.name} - {self.name}"


class APITestExecution(models.Model):
    """Record of API test execution with results"""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"
        ERROR = "error", "Error"
        TIMEOUT = "timeout", "Timeout"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_case = models.ForeignKey(
        APITestCase, on_delete=models.CASCADE, related_name="executions"
    )
    executed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="test_executions"
    )

    # Execution Details
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(
        null=True, blank=True, help_text="Execution duration in milliseconds"
    )

    # Request Details (actual sent)
    actual_url = models.URLField(help_text="Actual URL called")
    actual_headers = models.JSONField(default=dict, help_text="Actual headers sent")
    actual_body = models.TextField(blank=True, help_text="Actual request body sent")

    # Response Details
    response_status_code = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(
        default=dict, help_text="Response headers received"
    )
    response_body = models.TextField(blank=True, help_text="Response body received")
    response_size_bytes = models.IntegerField(null=True, blank=True)

    # Extracted Data (for chaining)
    extracted_data = models.JSONField(
        default=dict, help_text="Data extracted from response"
    )

    # Validation Results
    assertion_results = models.JSONField(
        default=list, help_text="Results of response assertions"
    )
    error_message = models.TextField(
        blank=True, help_text="Error message if execution failed"
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["test_case", "status"]),
            models.Index(fields=["executed_by", "started_at"]),
            models.Index(fields=["status", "started_at"]),
        ]

    def __str__(self):
        return f"{self.test_case.name} - {self.status} ({self.started_at})"


class APIAuthFlow(models.Model):
    """Authentication flow configuration for API testing"""

    class FlowType(models.TextChoices):
        SIMPLE = "simple", "Simple (single request)"
        OAUTH2_CLIENT_CREDENTIALS = "oauth2_cc", "OAuth2 Client Credentials"
        OAUTH2_AUTHORIZATION_CODE = "oauth2_ac", "OAuth2 Authorization Code"
        SESSION_LOGIN = "session_login", "Session-based Login"
        CUSTOM_CHAIN = "custom_chain", "Custom Authentication Chain"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Authentication flow name")
    description = models.TextField(blank=True, help_text="Flow description")
    flow_type = models.CharField(
        max_length=20, choices=FlowType.choices, default=FlowType.SIMPLE
    )

    # Authentication Steps Configuration
    auth_steps = models.JSONField(
        default=list, help_text="Ordered list of authentication steps"
    )

    # Token/Cookie Storage Configuration
    token_extraction = models.JSONField(
        default=dict, help_text="How to extract tokens/cookies from responses"
    )
    token_storage = models.JSONField(
        default=dict, help_text="Where to store extracted tokens"
    )

    # Validation Configuration
    success_indicators = models.JSONField(
        default=list, help_text="How to determine if auth was successful"
    )

    # Usage Configuration
    token_lifetime_minutes = models.IntegerField(
        default=60, help_text="Expected token lifetime"
    )
    auto_refresh = models.BooleanField(
        default=False, help_text="Auto-refresh expired tokens"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="auth_flows"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_flow_type_display()})"


class APITestSession(models.Model):
    """Test session for managing state across multiple API calls"""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Session name")
    collection = models.ForeignKey(
        APITestCollection, on_delete=models.CASCADE, related_name="sessions"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="test_sessions"
    )

    # Session State
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    session_data = models.JSONField(
        default=dict, help_text="Session variables and extracted data"
    )
    cookies = models.JSONField(default=dict, help_text="Session cookies")
    headers = models.JSONField(default=dict, help_text="Session headers")

    # Authentication State
    auth_flow = models.ForeignKey(
        APIAuthFlow, on_delete=models.SET_NULL, null=True, blank=True
    )
    auth_tokens = models.JSONField(default=dict, help_text="Authentication tokens")
    auth_expires_at = models.DateTimeField(null=True, blank=True)

    # Session Metadata
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["collection", "status"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.status}"


class AITestScenario(models.Model):
    """Pre-configured test scenarios for AI core functionality"""

    class ScenarioType(models.TextChoices):
        CONVERSATION_ANALYSIS = "conversation_analysis", "Conversation Analysis"
        LEAD_EXTRACTION = "lead_extraction", "Lead Information Extraction"
        QUALITY_SCORING = "quality_scoring", "Lead Quality Scoring"
        RECOMMENDATIONS = "recommendations", "AI Recommendations"
        OPPORTUNITY_INTELLIGENCE = (
            "opportunity_intelligence",
            "Opportunity Conversion Intelligence",
        )
        VOICE_PROCESSING = "voice_processing", "Voice Processing"
        SPEECH_TO_TEXT = "speech_to_text", "Speech-to-Text"
        TEXT_TO_SPEECH = "text_to_speech", "Text-to-Speech"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Scenario name")
    scenario_type = models.CharField(max_length=30, choices=ScenarioType.choices)
    description = models.TextField(
        help_text="Scenario description and expected behavior"
    )

    # Test Data
    test_data = models.JSONField(
        default=dict, help_text="Sample input data for testing"
    )
    expected_outputs = models.JSONField(default=dict, help_text="Expected AI outputs")
    validation_rules = models.JSONField(
        default=list, help_text="Rules to validate AI responses"
    )

    # Performance Expectations
    max_response_time_ms = models.IntegerField(
        default=5000, help_text="Maximum acceptable response time"
    )
    min_confidence_score = models.FloatField(
        default=0.7, help_text="Minimum acceptable confidence score"
    )

    # Configuration
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="Test priority (1=highest)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["scenario_type", "is_active"]),
            models.Index(fields=["priority", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_scenario_type_display()})"


class APIPerformanceMetric(models.Model):
    """Performance metrics for API calls"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_execution = models.OneToOneField(
        APITestExecution, on_delete=models.CASCADE, related_name="performance"
    )

    # Timing Metrics
    dns_lookup_ms = models.IntegerField(null=True, blank=True)
    tcp_connect_ms = models.IntegerField(null=True, blank=True)
    ssl_handshake_ms = models.IntegerField(null=True, blank=True)
    request_sent_ms = models.IntegerField(null=True, blank=True)
    first_byte_ms = models.IntegerField(null=True, blank=True)
    content_download_ms = models.IntegerField(null=True, blank=True)
    total_time_ms = models.IntegerField(null=True, blank=True)

    # Size Metrics
    request_size_bytes = models.IntegerField(null=True, blank=True)
    response_size_bytes = models.IntegerField(null=True, blank=True)
    headers_size_bytes = models.IntegerField(null=True, blank=True)

    # Network Metrics
    redirect_count = models.IntegerField(default=0)
    retry_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Performance for {self.test_execution.test_case.name}"
