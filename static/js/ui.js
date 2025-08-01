// UI Utilities for NIA Sales Assistant

class UIManager {
    constructor() {
        this.currentView = 'leads';
        this.currentLead = null;
        this.analysisResults = null;
        this.currentDetailTab = 'info';
        this.viewMode = 'list'; // 'list' or 'grid'
        this.searchTerm = '';
        this.filters = {
            status: '',
            score: '',
            sortBy: 'created_at'
        };
        this.allLeads = [];
        this.filteredLeads = [];
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.setupRealTimeUpdates();
        this.showView('leads');
    }

    setupRealTimeUpdates() {
        // Setup real-time updates for lead changes
        if (window.apiService.setupWebSocketUpdates) {
            this.websocket = window.apiService.setupWebSocketUpdates((data) => {
                this.handleRealTimeUpdate(data);
            });
        }
    }

    handleRealTimeUpdate(data) {
        switch (data.type) {
            case 'lead_updated':
                this.handleLeadUpdate(data.lead);
                break;
            case 'lead_created':
                this.handleLeadCreated(data.lead);
                break;
            case 'lead_deleted':
                this.handleLeadDeleted(data.lead_id);
                break;
            case 'lead_status_changed':
                this.handleLeadStatusChange(data.lead_id, data.new_status);
                break;
        }
    }

    handleLeadUpdate(updatedLead) {
        // Update lead in local data
        const leadIndex = this.allLeads.findIndex(l => l.id === updatedLead.id);
        if (leadIndex !== -1) {
            this.allLeads[leadIndex] = updatedLead;
            this.applyFiltersAndSearch();
            
            // Update detail view if this lead is currently displayed
            if (this.currentLead && this.currentLead.id === updatedLead.id) {
                this.currentLead = updatedLead;
                this.renderLeadDetail(updatedLead);
            }
            
            this.showAlert(`Lead "${updatedLead.company_name}" was updated`, 'info');
        }
    }

    handleLeadCreated(newLead) {
        this.allLeads.unshift(newLead);
        this.applyFiltersAndSearch();
        this.showAlert(`New lead "${newLead.company_name}" was created`, 'success');
    }

    handleLeadDeleted(leadId) {
        this.allLeads = this.allLeads.filter(l => l.id !== leadId);
        this.applyFiltersAndSearch();
        
        // If the deleted lead is currently displayed, go back to leads view
        if (this.currentLead && this.currentLead.id === leadId) {
            this.showView('leads');
        }
        
        this.showAlert('A lead was deleted', 'warning');
    }

    handleLeadStatusChange(leadId, newStatus) {
        const lead = this.allLeads.find(l => l.id === leadId);
        if (lead) {
            lead.status = newStatus;
            this.applyFiltersAndSearch();
            
            if (this.currentLead && this.currentLead.id === leadId) {
                this.currentLead.status = newStatus;
                this.renderLeadDetail(this.currentLead);
            }
        }
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = link.getAttribute('data-view');
                this.showView(view);
                this.updateActiveNav(link);
            });
        });
    }

    setupEventListeners() {
        // Create lead form submission
        const createForm = document.getElementById('create-lead-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleCreateLeadSubmission();
            });
        }

        // Edit lead form submission
        const editForm = document.getElementById('edit-lead-form');
        if (editForm) {
            editForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleEditLeadSubmission();
            });
        }

        // Add note form submission
        const noteForm = document.getElementById('add-note-form');
        if (noteForm) {
            noteForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleAddNoteSubmission();
            });
        }

        // Search input debouncing
        let searchTimeout;
        const searchInput = document.getElementById('lead-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => this.handleLeadSearch(), 300);
            });
        }

        // Modal close on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.add('hidden');
            }
        });
    }

    updateActiveNav(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }

    showView(viewName) {
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.add('hidden');
        });

        // Show/hide welcome section based on view
        const welcomeSection = document.querySelector('.welcome-section');
        if (welcomeSection) {
            if (viewName === 'leads') {
                welcomeSection.style.display = 'block';
            } else {
                welcomeSection.style.display = 'none';
            }
        }

        // Show selected view
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.remove('hidden');
            this.currentView = viewName;

            // Load data for specific views
            if (viewName === 'leads') {
                this.loadLeads();
            } else if (viewName === 'analytics') {
                this.loadAnalytics();
            }
        }
    }

    async loadLeads() {
        const loadingElement = document.getElementById('leads-loading');
        
        try {
            this.showLoading(loadingElement);
            const response = await window.apiService.getLeads();
            this.hideLoading(loadingElement);
            
            if (response.results && response.results.length > 0) {
                this.renderLeadsList(response.results);
            } else {
                this.renderEmptyLeadsList();
            }
        } catch (error) {
            this.hideLoading(loadingElement);
            this.showAlert('Error loading leads: ' + error.message, 'error');
            this.renderEmptyLeadsList();
        }
    }

    renderLeadsList(leads) {
        const listElement = document.getElementById('leads-list');
        
        if (leads.length === 0) {
            this.renderEmptyLeadsList();
            return;
        }

        listElement.innerHTML = leads.map(lead => `
            <div class="lead-item" onclick="uiManager.showLeadDetail('${lead.id}')">
                <div class="lead-header">
                    <div>
                        <div class="lead-company">${this.escapeHtml(lead.company_name || 'Unknown Company')}</div>
                        <div class="lead-contact">${this.escapeHtml(lead.contact_info?.email || lead.contact_info?.phone || 'No contact info')}</div>
                    </div>
                    <div class="lead-score">
                        <span class="score-badge ${this.getScoreClass((lead.ai_insights?.lead_score || 0) / 100)}">
                            Score: ${Math.round(lead.ai_insights?.lead_score || 0)}%
                        </span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="lead-status ${this.getStatusClass(lead.status)}">${lead.status}</span>
                    <small style="color: var(--text-secondary);">
                        ${this.formatDate(lead.created_at)}
                    </small>
                </div>
            </div>
        `).join('');
    }

    renderEmptyLeadsList() {
        const listElement = document.getElementById('leads-list');
        listElement.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📋</div>
                <h3>No leads yet</h3>
                <p>Create your first lead by clicking the "Create New Lead" button above.</p>
            </div>
        `;
    }

    async handleCreateLeadSubmission() {
        const conversationText = document.getElementById('conversation-text').value.trim();
        const leadSource = document.getElementById('lead-source').value;
        const urgency = document.getElementById('urgency').value;

        if (!conversationText) {
            this.showAlert('Please enter conversation notes', 'error');
            return;
        }

        try {
            // Show analysis in progress
            this.showAnalysisLoading();

            console.log('Starting conversation analysis...', {
                conversationText: conversationText.substring(0, 100) + '...',
                source: leadSource,
                urgency: urgency
            });

            // Analyze conversation - use debug endpoint for testing
            const analysis = await window.apiService.request('/debug-test/', {
                method: 'POST',
                body: JSON.stringify({
                    conversation_text: conversationText,
                    context: {
                        source: leadSource,
                        urgency: urgency
                    }
                })
            });

            console.log('Analysis completed:', analysis);
            console.log('Analysis type:', typeof analysis);
            console.log('Analysis keys:', Object.keys(analysis || {}));

            if (!analysis) {
                throw new Error('No analysis response received');
            }

            if (!analysis.success) {
                throw new Error(analysis.error || 'Analysis failed');
            }

            this.analysisResults = analysis;
            this.showAnalysisResults(analysis);

        } catch (error) {
            console.error('Analysis failed:', error);
            this.hideAnalysisResults();
            this.showAlert('Error analyzing conversation: ' + error.message, 'error');
        }
    }

    showAnalysisLoading() {
        const resultsElement = document.getElementById('analysis-results');
        const contentElement = document.getElementById('analysis-content');
        
        resultsElement.classList.remove('hidden');
        contentElement.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                Analyzing conversation with AI...
            </div>
        `;
    }

    showAnalysisResults(analysis) {
        const contentElement = document.getElementById('analysis-content');
        
        console.log('Showing analysis results:', analysis);
        
        let analysisHTML = '';

        // Extracted Lead Information - check all possible response structures
        const leadInfo = analysis.lead_information || analysis.lead_info || analysis.result;
        if (leadInfo) {
            const info = leadInfo;
            analysisHTML += `
                <div class="insight-card">
                    <h4>Extracted Lead Information</h4>
                    <div class="grid grid-2">
                        <div>
                            <p><strong>Company:</strong> ${this.escapeHtml(info.company_name || 'Not detected')}</p>
                            <p><strong>Contact:</strong> ${this.escapeHtml(info.contact_details?.name || 'Not detected')}</p>
                            <p><strong>Email:</strong> ${this.escapeHtml(info.contact_details?.email || 'Not detected')}</p>
                            <p><strong>Phone:</strong> ${this.escapeHtml(info.contact_details?.phone || 'Not detected')}</p>
                        </div>
                        <div>
                            <p><strong>Industry:</strong> ${this.escapeHtml(info.industry || 'Not detected')}</p>
                            <p><strong>Company Size:</strong> ${this.escapeHtml(info.company_size || 'Not detected')}</p>
                            <p><strong>Budget:</strong> ${this.escapeHtml(info.budget_info || 'Not detected')}</p>
                            <p><strong>Timeline:</strong> ${this.escapeHtml(info.timeline || 'Not detected')}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // Pain Points - check multiple possible locations
        const painPoints = analysis.pain_points || leadInfo?.pain_points || [];
        if (painPoints && painPoints.length > 0) {
            analysisHTML += `
                <div class="insight-card">
                    <h4>Identified Pain Points</h4>
                    <ul>
                        ${painPoints.map(point => `<li>${this.escapeHtml(point)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Requirements - check multiple possible locations
        const requirements = analysis.requirements || leadInfo?.requirements || [];
        if (requirements && requirements.length > 0) {
            analysisHTML += `
                <div class="insight-card">
                    <h4>Requirements</h4>
                    <ul>
                        ${requirements.map(req => `<li>${this.escapeHtml(req)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Quality Score
        if (analysis.quality_score !== undefined) {
            const score = Math.round(analysis.quality_score * 100);
            analysisHTML += `
                <div class="insight-card">
                    <h4>Lead Quality Score</h4>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold;" class="${this.getScoreClass(analysis.quality_score)}">${score}%</div>
                    </div>
                </div>
            `;
        }

        if (analysisHTML === '') {
            analysisHTML = `
                <div class="insight-card">
                    <h4>Debug Information</h4>
                    <p>No analysis data found. Raw response:</p>
                    <pre style="background: #f1f5f9; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px;">
${JSON.stringify(analysis, null, 2)}
                    </pre>
                </div>
            `;
        }
        
        contentElement.innerHTML = analysisHTML;
    }

    async confirmCreateLead() {
        if (!this.analysisResults) {
            this.showAlert('No analysis results available', 'error');
            return;
        }

        console.log('Creating lead with analysis results:', this.analysisResults);

        try {
            // Get lead information from the correct response structure
            const leadInfo = this.analysisResults.lead_information || this.analysisResults.lead_info || this.analysisResults.result || {};
            
            const leadData = {
                company_name: leadInfo.company_name || 'Unknown Company',
                contact_info: {
                    name: leadInfo.contact_details?.name || '',
                    email: leadInfo.contact_details?.email || '',
                    phone: leadInfo.contact_details?.phone || ''
                },
                pain_points: leadInfo.pain_points || this.analysisResults.pain_points || [],
                requirements: leadInfo.requirements || this.analysisResults.requirements || [],
                source: document.getElementById('lead-source').value || 'conversation',
                conversation_text: document.getElementById('conversation-text').value,
                industry: leadInfo.industry || '',
                company_size: leadInfo.company_size || '',
                budget_info: leadInfo.budget_info || '',
                timeline: leadInfo.timeline || '',
                urgency_level: leadInfo.urgency_level || 'medium'
            };

            console.log('Lead data to create:', leadData);

            const newLead = await window.apiService.createLead(leadData);
            
            console.log('Lead created successfully:', newLead);
            this.showAlert('Lead created successfully!', 'success');
            this.resetCreateForm();
            this.showView('leads');
            
        } catch (error) {
            console.error('Lead creation failed:', error);
            this.showAlert('Error creating lead: ' + error.message, 'error');
            
            // Show detailed error information
            const errorDetails = `
                <div class="insight-card">
                    <h4>Lead Creation Error</h4>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <p><strong>Analysis Data Available:</strong> ${this.analysisResults ? 'Yes' : 'No'}</p>
                    ${this.analysisResults ? `
                        <p><strong>Analysis Keys:</strong> ${Object.keys(this.analysisResults).join(', ')}</p>
                        <details>
                            <summary>Full Analysis Data</summary>
                            <pre style="background: #f1f5f9; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px;">
${JSON.stringify(this.analysisResults, null, 2)}
                            </pre>
                        </details>
                    ` : ''}
                </div>
            `;
            
            const contentElement = document.getElementById('analysis-content');
            if (contentElement) {
                contentElement.innerHTML = errorDetails;
            }
        }
    }

    hideAnalysisResults() {
        document.getElementById('analysis-results').classList.add('hidden');
    }

    resetCreateForm() {
        document.getElementById('create-lead-form').reset();
        this.hideAnalysisResults();
        this.analysisResults = null;
    }

    async loadAnalytics() {
        try {
            const analytics = await window.apiService.getLeadAnalytics();
            this.renderAnalytics(analytics);
        } catch (error) {
            this.showAlert('Error loading analytics: ' + error.message, 'error');
        }
    }

    renderAnalytics(analytics) {
        document.getElementById('total-leads').textContent = analytics.total_leads || 0;
        document.getElementById('high-quality-leads').textContent = analytics.high_quality_leads || 0;
        document.getElementById('avg-lead-score').textContent = 
            analytics.average_lead_score ? Math.round(analytics.average_lead_score * 100) + '%' : 'N/A';
    }

    // Utility methods
    showLoading(element) {
        if (element) element.classList.remove('hidden');
    }

    hideLoading(element) {
        if (element) element.classList.add('hidden');
    }

    getScoreClass(score) {
        if (score >= 0.7) return 'score-high';
        if (score >= 0.4) return 'score-medium';
        return 'score-low';
    }

    getStatusClass(status) {
        return `status-${status.toLowerCase().replace(' ', '-')}`;
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        const alertId = 'alert-' + Date.now();
        
        const alertHTML = `
            <div id="${alertId}" class="alert alert-${type}">
                ${this.escapeHtml(message)}
                <button onclick="document.getElementById('${alertId}').remove()" style="float: right; background: none; border: none; font-size: 1.2rem; cursor: pointer;">&times;</button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHTML);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alertElement = document.getElementById(alertId);
            if (alertElement) alertElement.remove();
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function showCreateForm() {
    window.uiManager.showView('create');
}

function showLeadsView() {
    window.uiManager.showView('leads');
}

function refreshLeads() {
    window.uiManager.loadLeads();
}

function hideAnalysisResults() {
    window.uiManager.hideAnalysisResults();
}

function confirmCreateLead() {
    window.uiManager.confirmCreateLead();
}

async function testAPIConnection() {
    console.log('Testing API connection...');
    
    try {
        // Test the debug endpoint first
        const debugResponse = await window.apiService.request('/debug-test/');
        console.log('Debug endpoint response:', debugResponse);
        
        // Test conversation analysis with simple text
        const testText = "I spoke with John from Acme Corp. They need a CRM system.";
        const analysisResponse = await window.apiService.request('/debug-test/', {
            method: 'POST',
            body: JSON.stringify({
                conversation_text: testText,
                context: { source: 'meeting' }
            })
        });
        console.log('Analysis response:', analysisResponse);
        
        window.uiManager.showAlert('API test completed - check console for results', 'success');
    } catch (error) {
        console.error('API test failed:', error);
        window.uiManager.showAlert('API test failed: ' + error.message, 'error');
    }
}

    // Enhanced Lead Management Functions
    async loadLeads() {
        const loadingElement = document.getElementById('leads-loading');
        
        try {
            this.showLoading(loadingElement);
            const response = await window.apiService.getLeads();
            this.hideLoading(loadingElement);
            
            this.allLeads = response.results || [];
            this.applyFiltersAndSearch();
            
        } catch (error) {
            this.hideLoading(loadingElement);
            this.showAlert('Error loading leads: ' + error.message, 'error');
            this.renderEmptyLeadsList();
        }
    }

    applyFiltersAndSearch() {
        let filtered = [...this.allLeads];

        // Apply search filter
        if (this.searchTerm) {
            const term = this.searchTerm.toLowerCase();
            filtered = filtered.filter(lead => 
                (lead.company_name || '').toLowerCase().includes(term) ||
                (lead.contact_info?.name || '').toLowerCase().includes(term) ||
                (lead.contact_info?.email || '').toLowerCase().includes(term)
            );
        }

        // Apply status filter
        if (this.filters.status) {
            filtered = filtered.filter(lead => lead.status === this.filters.status);
        }

        // Apply score filter
        if (this.filters.score) {
            filtered = filtered.filter(lead => {
                const score = (lead.ai_insights?.lead_score || 0) / 100;
                switch (this.filters.score) {
                    case 'high': return score >= 0.7;
                    case 'medium': return score >= 0.4 && score < 0.7;
                    case 'low': return score < 0.4;
                    default: return true;
                }
            });
        }

        // Apply sorting
        filtered.sort((a, b) => {
            switch (this.filters.sortBy) {
                case 'score':
                    return (b.ai_insights?.lead_score || 0) - (a.ai_insights?.lead_score || 0);
                case 'company_name':
                    return (a.company_name || '').localeCompare(b.company_name || '');
                case 'status':
                    return (a.status || '').localeCompare(b.status || '');
                case 'created_at':
                default:
                    return new Date(b.created_at) - new Date(a.created_at);
            }
        });

        this.filteredLeads = filtered;
        this.renderFilteredLeads();
    }

    renderFilteredLeads() {
        if (this.filteredLeads.length === 0) {
            this.renderEmptyLeadsList();
            return;
        }

        if (this.viewMode === 'grid') {
            this.renderLeadsGrid(this.filteredLeads);
        } else {
            this.renderLeadsList(this.filteredLeads);
        }
    }

    renderLeadsGrid(leads) {
        const listElement = document.getElementById('leads-list');
        listElement.className = 'leads-grid';
        
        listElement.innerHTML = leads.map(lead => `
            <div class="lead-card" onclick="uiManager.showLeadDetail('${lead.id}')">
                <div class="lead-card-header">
                    <div>
                        <div class="lead-card-company">${this.escapeHtml(lead.company_name || 'Unknown Company')}</div>
                        <div class="lead-card-contact">${this.escapeHtml(lead.contact_info?.email || lead.contact_info?.phone || 'No contact info')}</div>
                    </div>
                    <div class="lead-card-score">
                        <span class="score-badge ${this.getScoreClass((lead.ai_insights?.lead_score || 0) / 100)}">
                            ${Math.round(lead.ai_insights?.lead_score || 0)}%
                        </span>
                    </div>
                </div>
                <div class="lead-card-body">
                    <div class="lead-card-tags">
                        <span class="lead-tag">${lead.industry || 'Unknown Industry'}</span>
                        <span class="lead-tag">${lead.source || 'Unknown Source'}</span>
                    </div>
                </div>
                <div class="lead-card-footer">
                    <span class="lead-status ${this.getStatusClass(lead.status)}">${lead.status}</span>
                    <small style="color: var(--text-secondary);">
                        ${this.formatDate(lead.created_at)}
                    </small>
                </div>
            </div>
        `).join('');
    }

    async showLeadDetail(leadId) {
        try {
            // Find lead in current data or fetch from API
            let lead = this.allLeads.find(l => l.id === leadId);
            if (!lead) {
                lead = await window.apiService.getLead(leadId);
            }
            
            this.currentLead = lead;
            this.showView('detail');
            this.renderLeadDetail(lead);
            
        } catch (error) {
            this.showAlert('Error loading lead details: ' + error.message, 'error');
        }
    }

    renderLeadDetail(lead) {
        // Update header
        document.getElementById('detail-company-name').textContent = lead.company_name || 'Unknown Company';
        
        const statusBadge = document.getElementById('detail-status-badge');
        statusBadge.className = `lead-status-badge status-${lead.status}`;
        statusBadge.textContent = lead.status;

        // Update overview cards
        const score = lead.ai_insights?.lead_score || 0;
        document.getElementById('detail-lead-score').innerHTML = `
            <span class="${this.getScoreClass(score / 100)}">${Math.round(score)}%</span>
        `;
        
        document.getElementById('detail-last-contact').textContent = 
            lead.last_contact_date ? this.formatDate(lead.last_contact_date) : 'Never';
        
        document.getElementById('detail-source').textContent = lead.source || 'Unknown';
        
        document.getElementById('detail-next-action').textContent = 
            lead.ai_insights?.next_steps?.[0] || 'No action defined';

        // Render tab content
        this.renderInfoTab(lead);
        this.renderConversationTab(lead);
        this.renderInsightsTab(lead);
        this.renderActivityTab(lead);
    }

    renderInfoTab(lead) {
        // Company Information
        document.getElementById('company-info').innerHTML = `
            <p><strong>Company Name:</strong> ${this.escapeHtml(lead.company_name || 'Not specified')}</p>
            <p><strong>Industry:</strong> ${this.escapeHtml(lead.industry || 'Not specified')}</p>
            <p><strong>Company Size:</strong> ${this.escapeHtml(lead.company_size || 'Not specified')}</p>
            <p><strong>Website:</strong> ${lead.website ? `<a href="${lead.website}" target="_blank">${this.escapeHtml(lead.website)}</a>` : 'Not specified'}</p>
        `;

        // Contact Information
        const contact = lead.contact_info || {};
        document.getElementById('contact-info').innerHTML = `
            <p><strong>Name:</strong> ${this.escapeHtml(contact.name || 'Not specified')}</p>
            <p><strong>Email:</strong> ${contact.email ? `<a href="mailto:${contact.email}">${this.escapeHtml(contact.email)}</a>` : 'Not specified'}</p>
            <p><strong>Phone:</strong> ${contact.phone ? `<a href="tel:${contact.phone}">${this.escapeHtml(contact.phone)}</a>` : 'Not specified'}</p>
            <p><strong>Title:</strong> ${this.escapeHtml(contact.title || 'Not specified')}</p>
        `;

        // Requirements & Pain Points
        const painPoints = lead.pain_points || [];
        const requirements = lead.requirements || [];
        document.getElementById('requirements-info').innerHTML = `
            <div>
                <strong>Pain Points:</strong>
                ${painPoints.length > 0 ? `
                    <ul style="margin-top: 0.5rem;">
                        ${painPoints.map(point => `<li>${this.escapeHtml(point)}</li>`).join('')}
                    </ul>
                ` : '<p style="color: var(--text-secondary); margin-top: 0.5rem;">None identified</p>'}
            </div>
            <div style="margin-top: 1rem;">
                <strong>Requirements:</strong>
                ${requirements.length > 0 ? `
                    <ul style="margin-top: 0.5rem;">
                        ${requirements.map(req => `<li>${this.escapeHtml(req)}</li>`).join('')}
                    </ul>
                ` : '<p style="color: var(--text-secondary); margin-top: 0.5rem;">None specified</p>'}
            </div>
        `;

        // Budget & Timeline
        document.getElementById('budget-timeline-info').innerHTML = `
            <p><strong>Budget:</strong> ${this.escapeHtml(lead.budget_info || 'Not specified')}</p>
            <p><strong>Timeline:</strong> ${this.escapeHtml(lead.timeline || 'Not specified')}</p>
            <p><strong>Urgency:</strong> ${this.escapeHtml(lead.urgency_level || 'Medium')}</p>
            <p><strong>Decision Maker:</strong> ${this.escapeHtml(lead.decision_maker || 'Not identified')}</p>
        `;
    }

    renderConversationTab(lead) {
        const conversationHistory = lead.conversation_history || [];
        const historyElement = document.getElementById('conversation-history');
        
        if (conversationHistory.length === 0) {
            historyElement.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">💬</div>
                    <h3>No Conversation History</h3>
                    <p>No conversations have been recorded for this lead yet.</p>
                </div>
            `;
            return;
        }

        historyElement.innerHTML = conversationHistory.map(conv => `
            <div class="conversation-item">
                <div class="conversation-meta">
                    <span class="conversation-type">${conv.type || 'note'}</span>
                    <span>${this.formatDate(conv.date || conv.created_at)}</span>
                </div>
                <div class="conversation-content">
                    ${this.escapeHtml(conv.content || conv.notes)}
                </div>
                ${conv.outcome ? `
                    <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                        <strong>Outcome:</strong> ${this.escapeHtml(conv.outcome)}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    renderInsightsTab(lead) {
        const insights = lead.ai_insights || {};
        const insightsElement = document.getElementById('insights-content');
        
        let insightsHTML = '';

        // Lead Quality Score
        if (insights.lead_score !== undefined) {
            const score = Math.round(insights.lead_score);
            insightsHTML += `
                <div class="insight-card">
                    <h4>Lead Quality Score</h4>
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; font-weight: bold;" class="${this.getScoreClass(insights.lead_score / 100)}">${score}%</div>
                        <p style="margin-top: 0.5rem; color: var(--text-secondary);">
                            ${score >= 70 ? 'High quality lead with strong potential' : 
                              score >= 40 ? 'Medium quality lead worth pursuing' : 
                              'Low quality lead requiring nurturing'}
                        </p>
                    </div>
                </div>
            `;
        }

        // Sales Strategy
        if (insights.primary_strategy) {
            insightsHTML += `
                <div class="insight-card">
                    <h4>Recommended Sales Strategy</h4>
                    <p><strong>Strategy:</strong> ${this.escapeHtml(insights.primary_strategy)}</p>
                    ${insights.key_messaging && insights.key_messaging.length > 0 ? `
                        <p><strong>Key Messages:</strong></p>
                        <ul>
                            ${insights.key_messaging.map(msg => `<li>${this.escapeHtml(msg)}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            `;
        }

        // Next Steps
        if (insights.next_steps && insights.next_steps.length > 0) {
            insightsHTML += `
                <div class="insight-card">
                    <h4>Recommended Next Steps</h4>
                    <ul class="recommendation-list">
                        ${insights.next_steps.map(step => `
                            <li class="recommendation-item">${this.escapeHtml(step)}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Industry Insights
        if (insights.industry_insights && Object.keys(insights.industry_insights).length > 0) {
            insightsHTML += `
                <div class="insight-card">
                    <h4>Industry Insights</h4>
                    ${insights.industry_insights.trend ? `<p><strong>Trend:</strong> ${this.escapeHtml(insights.industry_insights.trend)}</p>` : ''}
                    ${insights.industry_insights.priority ? `<p><strong>Priority:</strong> ${this.escapeHtml(insights.industry_insights.priority)}</p>` : ''}
                </div>
            `;
        }

        if (insightsHTML === '') {
            insightsHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🤖</div>
                    <h3>No AI Insights Available</h3>
                    <p>Click "Refresh AI" to generate insights for this lead.</p>
                </div>
            `;
        }

        insightsElement.innerHTML = insightsHTML;
    }

    renderActivityTab(lead) {
        const activities = lead.activity_timeline || [];
        const timelineElement = document.getElementById('activity-timeline');
        
        if (activities.length === 0) {
            timelineElement.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📈</div>
                    <h3>No Activity History</h3>
                    <p>No activities have been recorded for this lead yet.</p>
                </div>
            `;
            return;
        }

        timelineElement.innerHTML = activities.map(activity => `
            <div class="timeline-item">
                <div class="timeline-date">${this.formatDate(activity.date || activity.created_at)}</div>
                <div class="timeline-content">${this.escapeHtml(activity.description || activity.activity)}</div>
            </div>
        `).join('');
    }

    showDetailTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[onclick="showDetailTab('${tabName}')"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');
        
        this.currentDetailTab = tabName;
    }

    // Search and Filter Functions
    handleLeadSearch() {
        const searchInput = document.getElementById('lead-search');
        this.searchTerm = searchInput.value.trim();
        this.applyFiltersAndSearch();
    }

    handleFilterChange() {
        this.filters.status = document.getElementById('status-filter').value;
        this.filters.score = document.getElementById('score-filter').value;
        this.applyFiltersAndSearch();
    }

    handleSortChange() {
        this.filters.sortBy = document.getElementById('sort-by').value;
        this.applyFiltersAndSearch();
    }

    toggleViewMode() {
        this.viewMode = this.viewMode === 'list' ? 'grid' : 'list';
        
        const icon = document.getElementById('view-mode-icon');
        const text = document.getElementById('view-mode-text');
        
        if (this.viewMode === 'grid') {
            icon.textContent = '📋';
            text.textContent = 'Grid View';
        } else {
            icon.textContent = '⊞';
            text.textContent = 'List View';
        }
        
        this.renderFilteredLeads();
    }

    // Modal Functions
    editLead() {
        if (!this.currentLead) return;
        
        // Populate edit form
        document.getElementById('edit-company-name').value = this.currentLead.company_name || '';
        document.getElementById('edit-status').value = this.currentLead.status || 'new';
        document.getElementById('edit-contact-name').value = this.currentLead.contact_info?.name || '';
        document.getElementById('edit-contact-email').value = this.currentLead.contact_info?.email || '';
        document.getElementById('edit-contact-phone').value = this.currentLead.contact_info?.phone || '';
        document.getElementById('edit-industry').value = this.currentLead.industry || '';
        document.getElementById('edit-notes').value = this.currentLead.notes || '';
        
        // Show modal
        document.getElementById('edit-modal').classList.remove('hidden');
    }

    closeEditModal() {
        document.getElementById('edit-modal').classList.add('hidden');
    }

    addConversationNote() {
        document.getElementById('note-modal').classList.remove('hidden');
    }

    closeNoteModal() {
        document.getElementById('note-modal').classList.add('hidden');
        document.getElementById('add-note-form').reset();
    }

    async refreshInsights() {
        if (!this.currentLead) return;
        
        try {
            this.showAlert('Refreshing AI insights...', 'info');
            const updatedLead = await window.apiService.refreshLeadInsights(this.currentLead.id);
            this.currentLead = updatedLead;
            this.renderInsightsTab(updatedLead);
            this.showAlert('AI insights refreshed successfully!', 'success');
        } catch (error) {
            this.showAlert('Error refreshing insights: ' + error.message, 'error');
        }
    }

    async convertToOpportunity() {
        if (!this.currentLead) return;
        
        const confirmed = confirm('Convert this lead to an opportunity? This action cannot be undone.');
        if (!confirmed) return;
        
        try {
            const opportunityData = {
                name: `${this.currentLead.company_name} Opportunity`,
                value: this.currentLead.budget_info || 0,
                stage: 'qualification',
                probability: Math.round((this.currentLead.ai_insights?.lead_score || 0.5) * 100)
            };
            
            await window.apiService.convertLeadToOpportunity(this.currentLead.id, opportunityData);
            this.showAlert('Lead converted to opportunity successfully!', 'success');
            this.showView('leads');
            this.loadLeads();
        } catch (error) {
            this.showAlert('Error converting lead: ' + error.message, 'error');
        }
    }

    async exportLeads() {
        try {
            const leads = this.filteredLeads.length > 0 ? this.filteredLeads : this.allLeads;
            const csvContent = this.generateCSV(leads);
            this.downloadCSV(csvContent, 'leads-export.csv');
            this.showAlert('Leads exported successfully!', 'success');
        } catch (error) {
            this.showAlert('Error exporting leads: ' + error.message, 'error');
        }
    }

    generateCSV(leads) {
        const headers = ['Company Name', 'Contact Name', 'Email', 'Phone', 'Status', 'Score', 'Industry', 'Source', 'Created Date'];
        const rows = leads.map(lead => [
            lead.company_name || '',
            lead.contact_info?.name || '',
            lead.contact_info?.email || '',
            lead.contact_info?.phone || '',
            lead.status || '',
            Math.round((lead.ai_insights?.lead_score || 0) * 100) + '%',
            lead.industry || '',
            lead.source || '',
            this.formatDate(lead.created_at)
        ]);
        
        return [headers, ...rows].map(row => 
            row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
        ).join('\n');
    }

    downloadCSV(content, filename) {
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

// Global functions for HTML onclick handlers (Enhanced)
function handleLeadSearch() {
    window.uiManager.handleLeadSearch();
}

function handleFilterChange() {
    window.uiManager.handleFilterChange();
}

function handleSortChange() {
    window.uiManager.handleSortChange();
}

function toggleViewMode() {
    window.uiManager.toggleViewMode();
}

function exportLeads() {
    window.uiManager.exportLeads();
}

function showDetailTab(tabName) {
    window.uiManager.showDetailTab(tabName);
}

function editLead() {
    window.uiManager.editLead();
}

function closeEditModal() {
    window.uiManager.closeEditModal();
}

function addConversationNote() {
    window.uiManager.addConversationNote();
}

function closeNoteModal() {
    window.uiManager.closeNoteModal();
}

function refreshInsights() {
    window.uiManager.refreshInsights();
}

function convertToOpportunity() {
    window.uiManager.convertToOpportunity();
}

    async handleEditLeadSubmission() {
        if (!this.currentLead) return;

        try {
            const formData = {
                company_name: document.getElementById('edit-company-name').value,
                status: document.getElementById('edit-status').value,
                contact_info: {
                    name: document.getElementById('edit-contact-name').value,
                    email: document.getElementById('edit-contact-email').value,
                    phone: document.getElementById('edit-contact-phone').value
                },
                industry: document.getElementById('edit-industry').value,
                notes: document.getElementById('edit-notes').value
            };

            const updatedLead = await window.apiService.updateLead(this.currentLead.id, formData);
            this.currentLead = updatedLead;
            this.renderLeadDetail(updatedLead);
            this.closeEditModal();
            this.showAlert('Lead updated successfully!', 'success');
            
            // Update the lead in the list
            const leadIndex = this.allLeads.findIndex(l => l.id === updatedLead.id);
            if (leadIndex !== -1) {
                this.allLeads[leadIndex] = updatedLead;
                this.applyFiltersAndSearch();
            }
            
        } catch (error) {
            this.showAlert('Error updating lead: ' + error.message, 'error');
        }
    }

    async handleAddNoteSubmission() {
        if (!this.currentLead) return;

        try {
            const noteData = {
                type: document.getElementById('note-type').value,
                content: document.getElementById('note-content').value,
                outcome: document.getElementById('note-outcome').value,
                date: new Date().toISOString()
            };

            // Add note to lead's conversation history
            const updatedHistory = [...(this.currentLead.conversation_history || []), noteData];
            const updatedLead = await window.apiService.updateLead(this.currentLead.id, {
                conversation_history: updatedHistory
            });

            this.currentLead = updatedLead;
            this.renderConversationTab(updatedLead);
            this.closeNoteModal();
            this.showAlert('Conversation note added successfully!', 'success');
            
        } catch (error) {
            this.showAlert('Error adding note: ' + error.message, 'error');
        }
    }