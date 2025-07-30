from django.db import models
from django.conf import settings
import uuid


class ConversationAnalysis(models.Model):
    """Store conversation analysis results from Gemini AI"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conversation_text = models.TextField()
    extracted_data = models.JSONField(default=dict)
    analysis_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-analysis_timestamp']
    
    def __str__(self):
        return f"Analysis for {self.user.username} at {self.analysis_timestamp}"
