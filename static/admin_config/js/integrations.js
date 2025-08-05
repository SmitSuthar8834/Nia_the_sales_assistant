// Integrations management JavaScript

let integrations = [];
let templates = [];
let currentEditingIntegration = null;

$(document).ready(function() {
    loadIntegrations();
    loadTemplates();
    
    // Set up event listeners
    $('#typeFilter, #statusFilter').change(applyFilters);
    $('#searchFilter').on('input', debounce(applyFilters, 300));
    $('#addIntegrationModal select[name="integration_type"]').change(onIntegrationTypeChange);
    $('#templateSelect').change(onTemplateSelect);
});

// Load integrations
function loadIntegrations() {
    AdminConfig.showLoading('Loading integrations...');
    
    AdminConfig.getIntegrations()
        .then(data => {
            integrations = data.results || data;
            renderIntegrationsTable();
            AdminConfig.hideLoading();
        })
        .catch(error => {
            AdminConfig.hideLoading();
            AdminConfig.showAlert('Failed to load integrations: ' + error.message, 'danger');
        });
}

// Load templates
function loadTemplates() {
    AdminConfig.getTemplates()
        .then(data => {
            templates = data.results || data;
            populateTemplateSelect();
        })
        .catch(error => {
            console.error('Failed to load templates:', error);
        });
}

// Render integrations table
function renderIntegrationsTable() {
    const tbody = $('#integrationsTable tbody');
    tbody.empty();
    
    if (integrations.length === 0) {
        tbody.html(`
            <tr>
                <td colspan="7" class="text-center text-muted">
                    <i class="fas fa-info-circle me-2"></i>No integrations found
                </td>
            </tr>
        `);
        return;
    }
    
    integrations.forEach(integration => {
        const row = `
            <tr>
                <td>
                    <div class="fw-bold">${integration.name}</div>
                    <small class="text-muted">${integration.description || 'No description'}</small>
                </td>
                <td>
                    <span class="badge bg-info">${integration.integration_type_display}</span>
                </td>
                <td>${AdminConfig.getStatusBadge(integration.status)}</td>
                <td>${AdminConfig.getHealthStatus(integration.health_status)}</td>
                <td>${AdminConfig.formatRelativeTime(integration.last_tested)}</td>
                <td>${AdminConfig.formatRelativeTime(integration.created_at)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-outline-primary" onclick="editIntegration('${integration.id}')" 
                                title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-success" onclick="testIntegration('${integration.id}')" 
                                title="Test">
                            <i class="fas fa-vial"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="toggleIntegrationStatus('${integration.id}')" 
                                title="${integration.status === 'active' ? 'Deactivate' : 'Activate'}">
                            <i class="fas fa-${integration.status === 'active' ? 'pause' : 'play'}"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteIntegration('${integration.id}')" 
                                title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

// Apply filters
function applyFilters() {
    const typeFilter = $('#typeFilter').val();
    const statusFilter = $('#statusFilter').val();
    const searchFilter = $('#searchFilter').val().toLowerCase();
    
    let filteredIntegrations = integrations;
    
    if (typeFilter) {
        filteredIntegrations = filteredIntegrations.filter(i => i.integration_type === typeFilter);
    }
    
    if (statusFilter) {
        filteredIntegrations = filteredIntegrations.filter(i => i.status === statusFilter);
    }
    
    if (searchFilter) {
        filteredIntegrations = filteredIntegrations.filter(i => 
            i.name.toLowerCase().includes(searchFilter) ||
            i.description?.toLowerCase().includes(searchFilter) ||
            i.integration_type_display.toLowerCase().includes(searchFilter)
        );
    }
    
    // Temporarily replace integrations for rendering
    const originalIntegrations = integrations;
    integrations = filteredIntegrations;
    renderIntegrationsTable();
    integrations = originalIntegrations;
}

// Refresh integrations
function refreshIntegrations() {
    loadIntegrations();
}

// Populate template select
function populateTemplateSelect() {
    const select = $('#templateSelect');
    select.find('option:not(:first)').remove();
    
    templates.forEach(template => {
        select.append(`<option value="${template.id}">${template.name}</option>`);
    });
}

// Handle integration type change
function onIntegrationTypeChange() {
    const integrationType = $(this).val();
    const templateSelect = $('#templateSelect');
    
    // Filter templates by category
    templateSelect.find('option:not(:first)').remove();
    
    const categoryMap = {
        'crm_': 'crm',
        'meeting_': 'meeting',
        'ai_': 'workflow'
    };
    
    let category = 'workflow';
    for (const [prefix, cat] of Object.entries(categoryMap)) {
        if (integrationType.startsWith(prefix)) {
            category = cat;
            break;
        }
    }
    
    const filteredTemplates = templates.filter(t => t.category === category);
    filteredTemplates.forEach(template => {
        templateSelect.append(`<option value="${template.id}">${template.name}</option>`);
    });
    
    // Show configuration form
    $('#configurationForm').show();
    generateConfigurationForm(integrationType);
}

// Handle template selection
function onTemplateSelect() {
    const templateId = $(this).val();
    if (!templateId) return;
    
    const template = templates.find(t => t.id === templateId);
    if (template) {
        AdminConfig.generateDynamicForm(
            template.configuration_schema,
            template.ui_schema,
            template.default_configuration
        );
    }
}

// Generate configuration form based on integration type
function generateConfigurationForm(integrationType) {
    // Default schemas for different integration types
    const schemas = {
        'crm_salesforce': {
            type: 'object',
            properties: {
                api_url: { type: 'string', title: 'API URL', format: 'uri' },
                api_version: { type: 'string', title: 'API Version', default: 'v52.0' },
                client_id: { type: 'string', title: 'Client ID' },
                client_secret: { type: 'string', title: 'Client Secret', format: 'password' },
                timeout: { type: 'integer', title: 'Timeout (seconds)', default: 30 }
            },
            required: ['api_url', 'client_id', 'client_secret']
        },
        'crm_hubspot': {
            type: 'object',
            properties: {
                api_key: { type: 'string', title: 'API Key', format: 'password' },
                portal_id: { type: 'string', title: 'Portal ID' },
                timeout: { type: 'integer', title: 'Timeout (seconds)', default: 30 }
            },
            required: ['api_key']
        },
        'meeting_google': {
            type: 'object',
            properties: {
                client_id: { type: 'string', title: 'Client ID' },
                client_secret: { type: 'string', title: 'Client Secret', format: 'password' },
                redirect_uri: { type: 'string', title: 'Redirect URI', format: 'uri' },
                scopes: { type: 'string', title: 'Scopes', default: 'https://www.googleapis.com/auth/calendar' }
            },
            required: ['client_id', 'client_secret', 'redirect_uri']
        },
        'ai_gemini': {
            type: 'object',
            properties: {
                api_key: { type: 'string', title: 'API Key', format: 'password' },
                model: { type: 'string', title: 'Model', default: 'gemini-pro' },
                temperature: { type: 'number', title: 'Temperature', default: 0.7 },
                max_tokens: { type: 'integer', title: 'Max Tokens', default: 1000 }
            },
            required: ['api_key']
        }
    };
    
    const schema = schemas[integrationType] || {
        type: 'object',
        properties: {
            api_url: { type: 'string', title: 'API URL', format: 'uri' },
            api_key: { type: 'string', title: 'API Key', format: 'password' }
        },
        required: ['api_url']
    };
    
    AdminConfig.generateDynamicForm(schema);
}

// Save integration
function saveIntegration() {
    const form = $('#addIntegrationForm');
    
    if (!AdminConfig.validateForm(form)) {
        return;
    }
    
    const formData = new FormData(form[0]);
    const data = Object.fromEntries(formData.entries());
    
    // Collect dynamic configuration fields
    const configuration = {};
    $('#dynamicFields input, #dynamicFields select, #dynamicFields textarea').each(function() {
        const field = $(this);
        const name = field.attr('name');
        let value = field.val();
        
        if (field.attr('type') === 'checkbox') {
            value = field.is(':checked');
        } else if (field.attr('type') === 'number') {
            value = parseFloat(value) || 0;
        }
        
        configuration[name] = value;
    });
    
    data.configuration = configuration;
    
    AdminConfig.showLoading('Saving integration...');
    
    AdminConfig.apiRequest('/admin-config/api/integrations/', {
        method: 'POST',
        data: data
    })
    .then(response => {
        AdminConfig.hideLoading();
        $('#addIntegrationModal').modal('hide');
        AdminConfig.showAlert('Integration saved successfully', 'success');
        loadIntegrations();
        form[0].reset();
        $('#configurationForm').hide();
    })
    .catch(error => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Failed to save integration: ' + error.message, 'danger');
    });
}

// Edit integration
function editIntegration(integrationId) {
    const integration = integrations.find(i => i.id === integrationId);
    if (!integration) return;
    
    currentEditingIntegration = integration;
    
    // Populate edit form
    $('#editIntegrationId').val(integration.id);
    
    const editFormContent = `
        <div class="row g-3">
            <div class="col-md-6">
                <label class="form-label">Integration Name *</label>
                <input type="text" class="form-control" name="name" value="${integration.name}" required>
            </div>
            <div class="col-md-6">
                <label class="form-label">Status</label>
                <select class="form-select" name="status">
                    <option value="draft" ${integration.status === 'draft' ? 'selected' : ''}>Draft</option>
                    <option value="active" ${integration.status === 'active' ? 'selected' : ''}>Active</option>
                    <option value="inactive" ${integration.status === 'inactive' ? 'selected' : ''}>Inactive</option>
                </select>
            </div>
            <div class="col-12">
                <label class="form-label">Description</label>
                <textarea class="form-control" name="description" rows="3">${integration.description || ''}</textarea>
            </div>
        </div>
        <div class="mt-4">
            <h6><i class="fas fa-cog me-2"></i>Configuration</h6>
            <div id="editDynamicFields"></div>
        </div>
    `;
    
    $('#editFormContent').html(editFormContent);
    
    // Generate configuration form
    if (integration.template) {
        const template = templates.find(t => t.id === integration.template);
        if (template) {
            AdminConfig.generateDynamicForm(
                template.configuration_schema,
                template.ui_schema,
                integration.configuration,
                'editDynamicFields'
            );
        }
    } else {
        // Generate based on integration type
        generateConfigurationForm(integration.integration_type, 'editDynamicFields');
        // Populate with existing values
        setTimeout(() => {
            Object.keys(integration.configuration).forEach(key => {
                const field = $(`#editDynamicFields [name="${key}"]`);
                if (field.length) {
                    if (field.attr('type') === 'checkbox') {
                        field.prop('checked', integration.configuration[key]);
                    } else {
                        field.val(integration.configuration[key]);
                    }
                }
            });
        }, 100);
    }
    
    $('#editIntegrationModal').modal('show');
}

// Update integration
function updateIntegration() {
    const form = $('#editIntegrationForm');
    
    if (!AdminConfig.validateForm(form)) {
        return;
    }
    
    const formData = new FormData(form[0]);
    const data = Object.fromEntries(formData.entries());
    
    // Collect dynamic configuration fields
    const configuration = {};
    $('#editDynamicFields input, #editDynamicFields select, #editDynamicFields textarea').each(function() {
        const field = $(this);
        const name = field.attr('name');
        let value = field.val();
        
        if (field.attr('type') === 'checkbox') {
            value = field.is(':checked');
        } else if (field.attr('type') === 'number') {
            value = parseFloat(value) || 0;
        }
        
        configuration[name] = value;
    });
    
    data.configuration = configuration;
    
    AdminConfig.showLoading('Updating integration...');
    
    AdminConfig.apiRequest(`/admin-config/api/integrations/${data.id}/`, {
        method: 'PUT',
        data: data
    })
    .then(response => {
        AdminConfig.hideLoading();
        $('#editIntegrationModal').modal('hide');
        AdminConfig.showAlert('Integration updated successfully', 'success');
        loadIntegrations();
    })
    .catch(error => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Failed to update integration: ' + error.message, 'danger');
    });
}

// Test integration
function testIntegration(integrationId) {
    const integration = integrations.find(i => i.id === integrationId);
    if (!integration) return;
    
    $('#testIntegrationId').val(integrationId);
    $('#testIntegrationModal .modal-title').html(`<i class="fas fa-vial me-2"></i>Test ${integration.name}`);
    $('#testResults').hide();
    $('#testIntegrationModal').modal('show');
}

// Run integration test
function runIntegrationTest() {
    const form = $('#testIntegrationForm');
    const formData = new FormData(form[0]);
    const data = Object.fromEntries(formData.entries());
    
    // Parse test data JSON
    try {
        if (data.test_data) {
            data.test_data = JSON.parse(data.test_data);
        }
    } catch (e) {
        AdminConfig.showAlert('Invalid JSON in test data', 'danger');
        return;
    }
    
    AdminConfig.showLoading('Running test...');
    
    AdminConfig.apiRequest(`/admin-config/api/integrations/${data.integration_id}/test_configuration/`, {
        method: 'POST',
        data: data
    })
    .then(response => {
        AdminConfig.hideLoading();
        displayTestResults(response);
    })
    .catch(error => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Test failed: ' + error.message, 'danger');
    });
}

// Display test results
function displayTestResults(results) {
    const resultsContainer = $('#testResultsContent');
    
    const statusClass = results.success ? 'success' : 'danger';
    const statusIcon = results.success ? 'check-circle' : 'times-circle';
    
    const html = `
        <div class="alert alert-${statusClass}">
            <i class="fas fa-${statusIcon} me-2"></i>
            Test ${results.success ? 'Passed' : 'Failed'}
        </div>
        <div class="row">
            <div class="col-md-6">
                <h6>Test Details</h6>
                <ul class="list-unstyled">
                    <li><strong>Type:</strong> ${results.test_type_display}</li>
                    <li><strong>Duration:</strong> ${results.duration_ms}ms</li>
                    <li><strong>Status:</strong> ${results.status_display}</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>Response Data</h6>
                <pre class="bg-light p-2 rounded"><code>${JSON.stringify(results.response_data, null, 2)}</code></pre>
            </div>
        </div>
        ${results.error_message ? `
            <div class="mt-3">
                <h6>Error Details</h6>
                <div class="alert alert-danger">${results.error_message}</div>
            </div>
        ` : ''}
    `;
    
    resultsContainer.html(html);
    $('#testResults').show();
}

// Toggle integration status
function toggleIntegrationStatus(integrationId) {
    const integration = integrations.find(i => i.id === integrationId);
    if (!integration) return;
    
    const newStatus = integration.status === 'active' ? 'inactive' : 'active';
    const action = newStatus === 'active' ? 'activate' : 'deactivate';
    
    AdminConfig.showLoading(`${action.charAt(0).toUpperCase() + action.slice(1)}ing integration...`);
    
    AdminConfig.apiRequest(`/admin-config/api/integrations/${integrationId}/${action}/`, {
        method: 'POST'
    })
    .then(response => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert(`Integration ${action}d successfully`, 'success');
        loadIntegrations();
    })
    .catch(error => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert(`Failed to ${action} integration: ` + error.message, 'danger');
    });
}

// Delete integration
function deleteIntegration(integrationId) {
    const integration = integrations.find(i => i.id === integrationId);
    if (!integration) return;
    
    if (!confirm(`Are you sure you want to delete "${integration.name}"? This action cannot be undone.`)) {
        return;
    }
    
    AdminConfig.showLoading('Deleting integration...');
    
    AdminConfig.apiRequest(`/admin-config/api/integrations/${integrationId}/`, {
        method: 'DELETE'
    })
    .then(response => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Integration deleted successfully', 'success');
        loadIntegrations();
    })
    .catch(error => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Failed to delete integration: ' + error.message, 'danger');
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}