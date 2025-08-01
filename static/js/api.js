// API Service for NIA Sales Assistant

class APIService {
    constructor() {
        this.baseURL = '/api/ai';
        this.token = this.getAuthToken();
    }

    // Get authentication token (for now, we'll use a simple approach)
    getAuthToken() {
        // In a real implementation, this would handle JWT tokens
        // For now, we'll assume the user is authenticated via Django sessions
        return null;
    }

    // Generic API request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                ...options.headers
            },
            ...options
        };

        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        console.log('Making API request:', url, config);

        try {
            const response = await fetch(url, config);

            console.log('API response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error response:', errorText);

                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch {
                    errorData = { error: errorText };
                }

                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const responseData = await response.json();
            console.log('API response data:', responseData);
            return responseData;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Get CSRF token for Django
    getCSRFToken() {
        // First try to get from meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }

        // Fallback to cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    // Lead Management APIs
    async getLeads(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/leads/${queryString ? '?' + queryString : ''}`;
        return this.request(endpoint);
    }

    async getLead(leadId) {
        return this.request(`/leads/${leadId}/`);
    }

    async createLead(leadData) {
        return this.request('/leads/', {
            method: 'POST',
            body: JSON.stringify(leadData)
        });
    }

    async updateLead(leadId, leadData) {
        return this.request(`/leads/${leadId}/`, {
            method: 'PATCH',
            body: JSON.stringify(leadData)
        });
    }

    async deleteLead(leadId) {
        return this.request(`/leads/${leadId}/`, {
            method: 'DELETE'
        });
    }

    // AI Analysis APIs
    async analyzeConversation(conversationText, context = {}) {
        return this.request('/analyze/', {
            method: 'POST',
            body: JSON.stringify({
                conversation_text: conversationText,
                context: context,
                extract_entities: true,
                generate_recommendations: true
            })
        });
    }

    async extractLeadInfo(conversationText, context = {}) {
        return this.request('/extract-lead/', {
            method: 'POST',
            body: JSON.stringify({
                conversation_text: conversationText,
                context: context
            })
        });
    }

    async getLeadQualityScore(leadData) {
        return this.request('/lead-quality-score/', {
            method: 'POST',
            body: JSON.stringify({
                lead_data: leadData
            })
        });
    }

    async getSalesStrategy(leadData, qualityScore = null) {
        return this.request('/sales-strategy/', {
            method: 'POST',
            body: JSON.stringify({
                lead_data: leadData,
                quality_score: qualityScore
            })
        });
    }

    async getIndustryInsights(leadData) {
        return this.request('/industry-insights/', {
            method: 'POST',
            body: JSON.stringify({
                lead_data: leadData
            })
        });
    }

    async getComprehensiveRecommendations(leadData) {
        return this.request('/comprehensive-recommendations/', {
            method: 'POST',
            body: JSON.stringify({
                lead_data: leadData,
                include_quality_score: true,
                include_sales_strategy: true,
                include_industry_insights: true,
                include_next_steps: true
            })
        });
    }

    // Lead Analytics
    async getLeadAnalytics() {
        return this.request('/analytics/');
    }

    // Utility APIs
    async testConnection() {
        return this.request('/test-connection/');
    }

    async getQuotaStatus() {
        return this.request('/quota-status/');
    }

    async getConversationHistory(limit = 10, offset = 0) {
        return this.request(`/history/?limit=${limit}&offset=${offset}`);
    }

    // Lead Actions (for AI recommendations)
    async refreshLeadInsights(leadId) {
        return this.request(`/leads/${leadId}/refresh-insights/`, {
            method: 'POST'
        });
    }

    async updateLeadStatus(leadId, status) {
        return this.updateLead(leadId, { status: status });
    }

    async convertLeadToOpportunity(leadId, opportunityData) {
        return this.request(`/leads/${leadId}/convert-to-opportunity/`, {
            method: 'POST',
            body: JSON.stringify(opportunityData)
        });
    }
}

// Create global API service instance
window.apiService = new APIService();    // E
nhanced Lead Management APIs
    async searchLeads(query, filters = {}) {
        const params = new URLSearchParams({
            search: query,
            ...filters
        });
        return this.request(`/leads/search/?${params}`);
    }

    async getLeadActivity(leadId) {
        return this.request(`/leads/${leadId}/activity/`);
    }

    async addLeadNote(leadId, noteData) {
        return this.request(`/leads/${leadId}/notes/`, {
            method: 'POST',
            body: JSON.stringify(noteData)
        });
    }

    async getLeadNotes(leadId) {
        return this.request(`/leads/${leadId}/notes/`);
    }

    async bulkUpdateLeads(leadIds, updateData) {
        return this.request('/leads/bulk-update/', {
            method: 'POST',
            body: JSON.stringify({
                lead_ids: leadIds,
                update_data: updateData
            })
        });
    }

    async exportLeadsData(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/leads/export/?${params}`);
    }

    // Real-time updates using Server-Sent Events
    setupRealTimeUpdates(callback) {
        if (typeof EventSource === 'undefined') {
            console.warn('Server-Sent Events not supported');
            return null;
        }

        const eventSource = new EventSource(`${this.baseURL}/leads/updates/`);
        
        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                callback(data);
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };

        eventSource.onerror = function(error) {
            console.error('SSE connection error:', error);
        };

        return eventSource;
    }

    // WebSocket connection for real-time updates (alternative to SSE)
    setupWebSocketUpdates(callback) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/leads/`;
        
        try {
            const socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                console.log('WebSocket connection established');
            };
            
            socket.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    callback(data);
                } catch (error) {
                    console.error('Error parsing WebSocket data:', error);
                }
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
            
            socket.onclose = function(event) {
                console.log('WebSocket connection closed');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    console.log('Attempting to reconnect WebSocket...');
                    this.setupWebSocketUpdates(callback);
                }, 5000);
            };
            
            return socket;
        } catch (error) {
            console.error('Error setting up WebSocket:', error);
            return null;
        }
    }

    // Lead status workflow management
    async getLeadStatusWorkflow() {
        return this.request('/leads/status-workflow/');
    }

    async updateLeadStatusWithWorkflow(leadId, newStatus, workflowData = {}) {
        return this.request(`/leads/${leadId}/status/`, {
            method: 'POST',
            body: JSON.stringify({
                status: newStatus,
                workflow_data: workflowData
            })
        });
    }

    // Lead scoring and analytics
    async getLeadScoringFactors(leadId) {
        return this.request(`/leads/${leadId}/scoring-factors/`);
    }

    async recalculateLeadScore(leadId) {
        return this.request(`/leads/${leadId}/recalculate-score/`, {
            method: 'POST'
        });
    }

    async getLeadTrends(timeframe = '30d') {
        return this.request(`/analytics/lead-trends/?timeframe=${timeframe}`);
    }

    async getConversionFunnel() {
        return this.request('/analytics/conversion-funnel/');
    }

    // Lead assignment and ownership
    async assignLead(leadId, userId) {
        return this.request(`/leads/${leadId}/assign/`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    async getLeadAssignments() {
        return this.request('/leads/assignments/');
    }

    // Lead templates and automation
    async getLeadTemplates() {
        return this.request('/leads/templates/');
    }

    async createLeadFromTemplate(templateId, customData = {}) {
        return this.request('/leads/from-template/', {
            method: 'POST',
            body: JSON.stringify({
                template_id: templateId,
                custom_data: customData
            })
        });
    }

    // Integration with external systems
    async syncWithCRM(leadId, crmSystem) {
        return this.request(`/leads/${leadId}/sync-crm/`, {
            method: 'POST',
            body: JSON.stringify({ crm_system: crmSystem })
        });
    }

    async getCRMSyncStatus(leadId) {
        return this.request(`/leads/${leadId}/crm-sync-status/`);
    }
}