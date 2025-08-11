// Minimal UI Manager for NIA Sales Assistant - Fixed Version

class UIManager {
    constructor() {
        this.currentView = 'leads';
        this.allLeads = [];
        this.filteredLeads = [];
        this.currentLead = null;
        this.currentSort = 'created_at';
        this.currentFilters = {};
        this.viewMode = 'grid';
        
        // Set up form handlers
        this.setupFormHandlers();
    }

    setupFormHandlers() {
        // Handle create lead form submission
        const createForm = document.getElementById('create-lead-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.confirmCreateLead();
            });
        }
    }

    // View Management
    showView(viewName) {
        this.currentView = viewName;
        
        // Hide all views
        const views = ['leads-view', 'create-view', 'analysis-view'];
        views.forEach(view => {
            const element = document.getElementById(view);
            if (element) element.style.display = 'none';
        });
        
        // Show selected view
        const targetView = document.getElementById(viewName + '-view');
        if (targetView) {
            targetView.style.display = 'block';
        }
        
        // Update navigation
        this.updateNavigation(viewName);
    }

    updateNavigation(activeView) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === activeView) {
                item.classList.add('active');
            }
        });
    }

    // Lead Management
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
        }
    }

    applyFiltersAndSearch() {
        let filtered = [...this.allLeads];
        
        // Apply search
        const searchTerm = document.getElementById('lead-search')?.value?.toLowerCase();
        if (searchTerm) {
            filtered = filtered.filter(lead => 
                lead.company_name?.toLowerCase().includes(searchTerm) ||
                lead.contact_info?.name?.toLowerCase().includes(searchTerm) ||
                lead.contact_info?.email?.toLowerCase().includes(searchTerm)
            );
        }
        
        // Apply filters
        Object.keys(this.currentFilters).forEach(key => {
            const value = this.currentFilters[key];
            if (value && value !== 'all') {
                filtered = filtered.filter(lead => lead[key] === value);
            }
        });
        
        // Apply sorting
        filtered.sort((a, b) => {
            const aVal = a[this.currentSort];
            const bVal = b[this.currentSort];
            if (aVal < bVal) return -1;
            if (aVal > bVal) return 1;
            return 0;
        });
        
        this.filteredLeads = filtered;
        this.renderLeads();
    }

    renderLeads() {
        const container = document.getElementById('leads-container');
        if (!container) return;
        
        if (this.filteredLeads.length === 0) {
            container.innerHTML = '<div class="no-leads">No leads found</div>';
            return;
        }
        
        const leadsHTML = this.filteredLeads.map(lead => this.renderLeadCard(lead)).join('');
        container.innerHTML = leadsHTML;
    }

    renderLeadCard(lead) {
        const statusClass = this.getStatusClass(lead.status);
        const createdDate = new Date(lead.created_at).toLocaleDateString();
        
        return `
            <div class="lead-card" onclick="window.uiManager.showLeadDetails('${lead.id}')">
                <div class="lead-header">
                    <h3>${lead.company_name || 'Unknown Company'}</h3>
                    <span class="status-badge ${statusClass}">${lead.status || 'new'}</span>
                </div>
                <div class="lead-content">
                    <p><strong>Contact:</strong> ${lead.contact_info?.name || 'N/A'}</p>
                    <p><strong>Email:</strong> ${lead.contact_info?.email || 'N/A'}</p>
                    <p><strong>Industry:</strong> ${lead.industry || 'N/A'}</p>
                    <p><strong>Created:</strong> ${createdDate}</p>
                </div>
                <div class="lead-actions">
                    <button onclick="event.stopPropagation(); window.uiManager.editLead('${lead.id}')" class="btn-edit">Edit</button>
                    <button onclick="event.stopPropagation(); window.uiManager.deleteLead('${lead.id}')" class="btn-delete">Delete</button>
                </div>
            </div>
        `;
    }

    getStatusClass(status) {
        const statusClasses = {
            'new': 'status-new',
            'contacted': 'status-contacted',
            'qualified': 'status-qualified',
            'proposal': 'status-proposal',
            'closed': 'status-closed'
        };
        return statusClasses[status] || 'status-new';
    }

    // Create Lead Functionality
    async confirmCreateLead() {
        const form = document.getElementById('create-lead-form');
        if (!form) return;
        
        const conversationText = document.getElementById('conversation-text')?.value;
        const leadSource = document.getElementById('lead-source')?.value;
        const urgency = document.getElementById('urgency')?.value;
        
        if (!conversationText) {
            this.showAlert('Please enter conversation text to analyze', 'error');
            return;
        }
        
        try {
            this.showLoading(document.getElementById('create-loading'));
            
            // First, analyze the conversation to extract lead information
            const analysisResult = await window.apiService.analyzeConversation(conversationText, {
                source: leadSource,
                urgency: urgency
            });
            
            // Extract lead information from the analysis
            const extractedInfo = await window.apiService.extractLeadInfo(conversationText, {
                source: leadSource,
                urgency: urgency
            });
            
            // Create lead data from extracted information
            const leadData = {
                company_name: extractedInfo.company_name || 'Unknown Company',
                contact_info: {
                    name: extractedInfo.contact_name || '',
                    email: extractedInfo.contact_email || '',
                    phone: extractedInfo.contact_phone || ''
                },
                industry: extractedInfo.industry || '',
                notes: conversationText,
                conversation_text: conversationText,
                source: leadSource || 'unknown',
                urgency: urgency || 'medium',
                ai_analysis: analysisResult,
                extracted_info: extractedInfo
            };
            
            // Create the lead
            const newLead = await window.apiService.createLead(leadData);
            this.hideLoading(document.getElementById('create-loading'));
            
            this.showAlert('Lead created successfully!', 'success');
            this.allLeads.unshift(newLead);
            this.applyFiltersAndSearch();
            
            // Show analysis results
            this.showAnalysisResults(analysisResult, extractedInfo);
            
            // Reset form and go back to leads view after a delay
            setTimeout(() => {
                form.reset();
                this.showView('leads');
            }, 3000);
            
        } catch (error) {
            this.hideLoading(document.getElementById('create-loading'));
            this.showAlert('Error creating lead: ' + error.message, 'error');
            console.error('Create lead error:', error);
        }
    }

    showAnalysisResults(analysisResult, extractedInfo) {
        const resultsDiv = document.getElementById('analysis-results');
        const contentDiv = document.getElementById('analysis-content');
        
        if (!resultsDiv || !contentDiv) return;
        
        contentDiv.innerHTML = `
            <div class="analysis-section">
                <h4>Extracted Lead Information</h4>
                <div class="extracted-info">
                    <p><strong>Company:</strong> ${extractedInfo.company_name || 'Not detected'}</p>
                    <p><strong>Contact:</strong> ${extractedInfo.contact_name || 'Not detected'}</p>
                    <p><strong>Email:</strong> ${extractedInfo.contact_email || 'Not detected'}</p>
                    <p><strong>Phone:</strong> ${extractedInfo.contact_phone || 'Not detected'}</p>
                    <p><strong>Industry:</strong> ${extractedInfo.industry || 'Not detected'}</p>
                </div>
            </div>
            <div class="analysis-section">
                <h4>AI Analysis</h4>
                <div class="ai-analysis">
                    <p><strong>Summary:</strong> ${analysisResult.summary || 'Analysis completed'}</p>
                    <p><strong>Recommendations:</strong> ${analysisResult.recommendations || 'See detailed analysis'}</p>
                </div>
            </div>
        `;
        
        resultsDiv.classList.remove('hidden');
        resultsDiv.style.display = 'block';
    }

    // Utility Functions
    showLoading(element) {
        if (element) {
            element.style.display = 'block';
        }
    }

    hideLoading(element) {
        if (element) {
            element.style.display = 'none';
        }
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        // Add to page
        const container = document.getElementById('alerts-container') || document.body;
        container.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }

    hideAnalysisResults() {
        const element = document.getElementById('analysis-results');
        if (element) {
            element.style.display = 'none';
        }
    }

    // Search and Filter Functions
    handleLeadSearch() {
        this.applyFiltersAndSearch();
    }

    handleFilterChange() {
        const statusFilter = document.getElementById('status-filter')?.value;
        const industryFilter = document.getElementById('industry-filter')?.value;
        
        this.currentFilters = {
            status: statusFilter,
            industry: industryFilter
        };
        
        this.applyFiltersAndSearch();
    }

    handleSortChange() {
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            this.currentSort = sortSelect.value;
            this.applyFiltersAndSearch();
        }
    }

    toggleViewMode() {
        this.viewMode = this.viewMode === 'grid' ? 'list' : 'grid';
        const container = document.getElementById('leads-container');
        if (container) {
            container.className = `leads-container ${this.viewMode}-view`;
        }
        this.renderLeads();
    }

    exportLeads() {
        if (this.filteredLeads.length === 0) {
            this.showAlert('No leads to export', 'warning');
            return;
        }
        
        const csvContent = this.generateCSV(this.filteredLeads);
        this.downloadCSV(csvContent, 'leads-export.csv');
    }

    generateCSV(leads) {
        const headers = ['Company Name', 'Contact Name', 'Email', 'Phone', 'Industry', 'Status', 'Created Date'];
        const rows = leads.map(lead => [
            lead.company_name || '',
            lead.contact_info?.name || '',
            lead.contact_info?.email || '',
            lead.contact_info?.phone || '',
            lead.industry || '',
            lead.status || '',
            new Date(lead.created_at).toLocaleDateString()
        ]);
        
        const csvContent = [headers, ...rows]
            .map(row => row.map(field => `"${field}"`).join(','))
            .join('\n');
        
        return csvContent;
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

// Test API Connection
async function testAPIConnection() {
    try {
        console.log('Testing API connection...');
        
        // Test leads endpoint
        const leadsResponse = await window.apiService.getLeads();
        console.log('Leads response:', leadsResponse);
        
        window.uiManager.showAlert('API connection test completed - check console for results', 'success');
    } catch (error) {
        console.error('API test failed:', error);
        window.uiManager.showAlert('API test failed: ' + error.message, 'error');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (!window.uiManager) {
        window.uiManager = new UIManager();
    }
    
    // Set up form handlers after DOM is loaded
    setTimeout(() => {
        if (window.uiManager && window.uiManager.setupFormHandlers) {
            window.uiManager.setupFormHandlers();
        }
    }, 100);
});