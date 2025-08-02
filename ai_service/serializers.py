from rest_framework import serializers
from .models import Lead, AIInsights, ConversationAnalysis, Opportunity, OpportunityIntelligence


class AIInsightsSerializer(serializers.ModelSerializer):
    """Serializer for AI insights with comprehensive recommendations"""
    
    is_high_quality = serializers.ReadOnlyField()
    needs_immediate_attention = serializers.ReadOnlyField()
    
    class Meta:
        model = AIInsights
        fields = [
            'id', 'lead_score', 'conversion_probability', 'quality_tier',
            'score_breakdown', 'estimated_deal_size', 'sales_cycle_prediction',
            'key_strengths', 'improvement_areas', 'competitive_risk',
            'recommended_actions', 'next_steps', 'next_best_action',
            'risk_factors', 'opportunities', 'primary_strategy',
            'key_messaging', 'objection_handling', 'industry_insights',
            'confidence_score', 'data_completeness', 'last_analyzed',
            'is_high_quality', 'needs_immediate_attention'
        ]
        read_only_fields = [
            'id', 'last_analyzed', 'is_high_quality', 'needs_immediate_attention'
        ]


class LeadSerializer(serializers.ModelSerializer):
    """Serializer for Lead model with AI insights integration"""
    
    ai_insights = AIInsightsSerializer(read_only=True)
    contact_name = serializers.ReadOnlyField()
    contact_email = serializers.ReadOnlyField()
    contact_phone = serializers.ReadOnlyField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'company_name', 'industry', 'company_size',
            'contact_info', 'contact_name', 'contact_email', 'contact_phone',
            'status', 'source', 'pain_points', 'requirements',
            'budget_info', 'timeline', 'decision_makers',
            'urgency_level', 'current_solution', 'competitors_mentioned',
            'crm_record_id', 'crm_system', 'conversation_history',
            'created_at', 'updated_at', 'ai_insights'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            'contact_name', 'contact_email', 'contact_phone'
        ]
    
    def validate_contact_info(self, value):
        """Validate contact information structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Contact info must be a dictionary")
        
        # Validate email format if provided
        email = value.get('email')
        if email:
            email_validator = serializers.EmailField()
            try:
                email_validator.run_validation(email)
            except serializers.ValidationError:
                raise serializers.ValidationError("Invalid email format in contact_info")
        
        return value
    
    def validate_pain_points(self, value):
        """Validate pain points are a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Pain points must be a list")
        
        for point in value:
            if not isinstance(point, str):
                raise serializers.ValidationError("Each pain point must be a string")
        
        return value
    
    def validate_requirements(self, value):
        """Validate requirements are a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Requirements must be a list")
        
        for req in value:
            if not isinstance(req, str):
                raise serializers.ValidationError("Each requirement must be a string")
        
        return value


class LeadCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leads with conversation text for AI analysis"""
    
    conversation_text = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Conversation transcript to analyze for lead information"
    )
    
    class Meta:
        model = Lead
        fields = [
            'company_name', 'industry', 'company_size',
            'contact_info', 'status', 'source',
            'pain_points', 'requirements', 'budget_info',
            'timeline', 'decision_makers', 'urgency_level',
            'current_solution', 'competitors_mentioned',
            'conversation_history', 'conversation_text'
        ]
    
    def validate_contact_info(self, value):
        """Validate contact information structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Contact info must be a dictionary")
        
        # Require at least company name or contact name
        if not value.get('name') and not self.initial_data.get('company_name'):
            raise serializers.ValidationError(
                "Either contact name or company name must be provided"
            )
        
        return value
    
    def create(self, validated_data):
        """Create lead and trigger AI analysis if conversation text provided"""
        conversation_text = validated_data.pop('conversation_text', None)
        
        # Set the user from the request context, or create a test user for demo
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            # For testing without authentication, create or get a test user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            test_user, created = User.objects.get_or_create(
                username='test_user',
                defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
            )
            validated_data['user'] = test_user
        
        # Store conversation text in conversation_history if provided
        if conversation_text and not validated_data.get('conversation_history'):
            validated_data['conversation_history'] = conversation_text
        
        # Create the lead
        lead = Lead.objects.create(**validated_data)
        
        # If conversation text is provided, trigger AI analysis
        if conversation_text:
            try:
                from .tasks import analyze_lead_with_ai
                # Try async AI analysis first
                analyze_lead_with_ai.delay(lead.id, conversation_text)
            except Exception as e:
                # If Celery is not available, skip async analysis for now
                # The analysis can be done later or synchronously if needed
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Async AI analysis failed, skipping: {e}")
                # Could add synchronous analysis here if needed
        
        return lead


class ConversationAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for conversation analysis results"""
    
    class Meta:
        model = ConversationAnalysis
        fields = [
            'id', 'conversation_text', 'extracted_data', 'analysis_timestamp'
        ]
        read_only_fields = ['id', 'user', 'analysis_timestamp']


class LeadListSerializer(serializers.ModelSerializer):
    """Simplified serializer for lead list views"""
    
    ai_insights = serializers.SerializerMethodField()
    contact_name = serializers.ReadOnlyField()
    contact_email = serializers.ReadOnlyField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'company_name', 'contact_name', 'contact_email',
            'status', 'created_at', 'updated_at', 'ai_insights'
        ]
    
    def get_ai_insights(self, obj):
        """Get simplified AI insights for list view"""
        if hasattr(obj, 'ai_insights'):
            return {
                'lead_score': obj.ai_insights.lead_score,
                'quality_tier': obj.ai_insights.quality_tier,
                'conversion_probability': obj.ai_insights.conversion_probability,
                'needs_immediate_attention': obj.ai_insights.needs_immediate_attention
            }
        return None


class LeadUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating leads with optional AI re-analysis"""
    
    trigger_ai_analysis = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
        help_text="Set to true to trigger AI re-analysis after update"
    )
    
    class Meta:
        model = Lead
        fields = [
            'company_name', 'industry', 'company_size',
            'contact_info', 'status', 'source',
            'pain_points', 'requirements', 'budget_info',
            'timeline', 'decision_makers', 'urgency_level',
            'current_solution', 'competitors_mentioned',
            'conversation_history', 'trigger_ai_analysis'
        ]
    
    def update(self, instance, validated_data):
        """Update lead and optionally trigger AI re-analysis"""
        trigger_analysis = validated_data.pop('trigger_ai_analysis', False)
        
        # Update the lead
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Trigger AI re-analysis if requested
        if trigger_analysis and instance.conversation_history:
            from .tasks import analyze_lead_with_ai
            analyze_lead_with_ai.delay(instance.id, instance.conversation_history)
        
        return instance

# Opportunity Conversion Intelligence Serializers

class OpportunitySerializer(serializers.ModelSerializer):
    """Serializer for Opportunity model"""
    
    lead_company_name = serializers.CharField(source='lead.company_name', read_only=True)
    lead_contact_name = serializers.SerializerMethodField()
    days_to_close = serializers.ReadOnlyField()
    is_high_value = serializers.ReadOnlyField()
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'lead', 'user', 'name', 'description',
            'estimated_value', 'probability', 'expected_close_date',
            'sales_cycle_days', 'stage', 'priority',
            'crm_record_id', 'crm_system',
            'lead_company_name', 'lead_contact_name',
            'days_to_close', 'is_high_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_lead_contact_name(self, obj):
        """Get contact name from related lead"""
        if obj.lead and obj.lead.contact_info:
            return obj.lead.contact_info.get('name', '')
        return ''


class OpportunityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating opportunities"""
    
    class Meta:
        model = Opportunity
        fields = [
            'lead', 'name', 'description', 'estimated_value',
            'probability', 'expected_close_date', 'sales_cycle_days',
            'stage', 'priority', 'crm_record_id', 'crm_system'
        ]
    
    def create(self, validated_data):
        """Create opportunity and set user from request"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class OpportunityListSerializer(serializers.ModelSerializer):
    """Simplified serializer for opportunity lists"""
    
    lead_company_name = serializers.CharField(source='lead.company_name', read_only=True)
    lead_contact_name = serializers.SerializerMethodField()
    days_to_close = serializers.ReadOnlyField()
    conversion_probability = serializers.SerializerMethodField()
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'name', 'estimated_value', 'probability',
            'expected_close_date', 'stage', 'priority',
            'lead_company_name', 'lead_contact_name',
            'days_to_close', 'conversion_probability',
            'created_at', 'updated_at'
        ]
    
    def get_lead_contact_name(self, obj):
        """Get contact name from related lead"""
        if obj.lead and obj.lead.contact_info:
            return obj.lead.contact_info.get('name', '')
        return ''
    
    def get_conversion_probability(self, obj):
        """Get conversion probability from intelligence if available"""
        if hasattr(obj, 'intelligence'):
            return obj.intelligence.conversion_probability
        return None


class OpportunityIntelligenceSerializer(serializers.ModelSerializer):
    """Serializer for OpportunityIntelligence model"""
    
    opportunity_name = serializers.CharField(source='opportunity.name', read_only=True)
    opportunity_stage = serializers.CharField(source='opportunity.stage', read_only=True)
    is_high_probability = serializers.ReadOnlyField()
    needs_attention = serializers.ReadOnlyField()
    
    class Meta:
        model = OpportunityIntelligence
        fields = [
            'id', 'opportunity', 'conversion_probability',
            'conversion_likelihood', 'conversion_confidence',
            'predicted_deal_size_min', 'predicted_deal_size_max',
            'predicted_close_date', 'sales_cycle_prediction_days',
            'recommended_stage', 'next_stage_probability',
            'stage_advancement_timeline', 'overall_risk_level',
            'risk_factors', 'risk_mitigation_strategies',
            'competitive_threats', 'competitive_advantages',
            'win_strategy', 'similar_deals_count',
            'historical_win_rate', 'benchmark_metrics',
            'priority_actions', 'next_best_actions',
            'resource_requirements', 'opportunity_name',
            'opportunity_stage', 'is_high_probability',
            'needs_attention', 'last_analyzed', 'created_at'
        ]
        read_only_fields = ['id', 'last_analyzed', 'created_at']


class OpportunityWithIntelligenceSerializer(serializers.ModelSerializer):
    """Serializer for Opportunity with embedded intelligence data"""
    
    intelligence = OpportunityIntelligenceSerializer(read_only=True)
    lead_company_name = serializers.CharField(source='lead.company_name', read_only=True)
    lead_contact_name = serializers.SerializerMethodField()
    days_to_close = serializers.ReadOnlyField()
    is_high_value = serializers.ReadOnlyField()
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'lead', 'user', 'name', 'description',
            'estimated_value', 'probability', 'expected_close_date',
            'sales_cycle_days', 'stage', 'priority',
            'crm_record_id', 'crm_system',
            'lead_company_name', 'lead_contact_name',
            'days_to_close', 'is_high_value',
            'intelligence', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_lead_contact_name(self, obj):
        """Get contact name from related lead"""
        if obj.lead and obj.lead.contact_info:
            return obj.lead.contact_info.get('name', '')
        return ''


# Enhanced Lead Serializer with Opportunity Conversion Intelligence

class LeadWithOpportunityIntelligenceSerializer(serializers.ModelSerializer):
    """Enhanced lead serializer with opportunity conversion intelligence"""
    
    ai_insights = AIInsightsSerializer(read_only=True)
    opportunities = OpportunityListSerializer(many=True, read_only=True)
    contact_name = serializers.ReadOnlyField()
    contact_email = serializers.ReadOnlyField()
    contact_phone = serializers.ReadOnlyField()
    
    # Opportunity conversion fields
    should_convert_to_opportunity = serializers.SerializerMethodField()
    conversion_readiness_score = serializers.SerializerMethodField()
    recommended_opportunity_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'company_name', 'industry', 'company_size',
            'contact_info', 'status', 'source',
            'pain_points', 'requirements', 'budget_info',
            'timeline', 'decision_makers', 'urgency_level',
            'current_solution', 'competitors_mentioned',
            'crm_record_id', 'crm_system',
            'contact_name', 'contact_email', 'contact_phone',
            'ai_insights', 'opportunities',
            'should_convert_to_opportunity', 'conversion_readiness_score',
            'recommended_opportunity_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_should_convert_to_opportunity(self, obj):
        """Check if lead should be converted to opportunity"""
        if hasattr(obj, 'ai_insights') and obj.ai_insights:
            return obj.ai_insights.should_convert_to_opportunity
        return False
    
    def get_conversion_readiness_score(self, obj):
        """Get opportunity conversion readiness score"""
        if hasattr(obj, 'ai_insights') and obj.ai_insights:
            return obj.ai_insights.opportunity_conversion_score
        return 0.0
    
    def get_recommended_opportunity_value(self, obj):
        """Get recommended opportunity value from AI insights"""
        if hasattr(obj, 'ai_insights') and obj.ai_insights:
            return obj.ai_insights.estimated_deal_size
        return None