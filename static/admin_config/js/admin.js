// Admin Configuration Dashboard JavaScript

// Global variables
let currentUser = null;
let csrfToken = null;

// Initialize on document ready
$(document).ready(function() {
    initializeAdmin();
});

// Initialize admin dashboard
function initializeAdmin() {
    // Get CSRF token
    csrfToken = $('[name=csrfmiddlewaretoken]').val() || getCookie('csrftoken');
    
    // Set up AJAX defaults
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            }
        }
    });
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set up global error handling
    $(document).ajaxError(function(event, xhr, settings, thrownError) {
        hideLoading();
        if (xhr.status === 403) {
            showAlert('Permission denied. You do not have access to perform this action.', 'danger');
        } else if (xhr.status === 500) {
            showAlert('Server error occurred. Please try again later.', 'danger');
        } else if (xhr.status !== 0) { // Ignore aborted requests
            showAlert('An error occurred: ' + (xhr.responseJSON?.error || thrownError), 'danger');
        }
    });
}

// Utility Functions

// Get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Check if HTTP method is CSRF safe
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// Show loading overlay
function showLoading(message = 'Processing...') {
    const overlay = $('#loadingOverlay');
    if (message !== 'Processing...') {
        overlay.find('.loading-spinner div:last-child').text(message);
    }
    overlay.removeClass('d-none');
}

// Hide loading overlay
function hideLoading() {
    $('#loadingOverlay').addClass('d-none');
}

// Show alert message
function showAlert(message, type = 'info', duration = 5000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Find or create alerts container
    let alertsContainer = $('.alerts-container');
    if (alertsContainer.length === 0) {
        alertsContainer = $('<div class="alerts-container"></div>');
        $('.container-fluid').prepend(alertsContainer);
    }
    
    const alertElement = $(alertHtml);
    alertsContainer.append(alertElement);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            alertElement.alert('close');
        }, duration);
    }
    
    return alertElement;
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Format relative time
function formatRelativeTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    return formatDate(dateString);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Get status badge HTML
function getStatusBadge(status) {
    const statusClasses = {
        'active': 'bg-success',
        'inactive': 'bg-danger',
        'draft': 'bg-warning text-dark',
        'error': 'bg-danger',
        'testing': 'bg-info'
    };
    
    const statusLabels = {
        'active': 'Active',
        'inactive': 'Inactive',
        'draft': 'Draft',
        'error': 'Error',
        'testing': 'Testing'
    };
    
    const badgeClass = statusClasses[status] || 'bg-secondary';
    const label = statusLabels[status] || status;
    
    return `<span class="badge ${badgeClass}">${label}</span>`;
}

// Get health status HTML
function getHealthStatus(healthStatus) {
    const healthClasses = {
        'healthy': 'text-success',
        'warning': 'text-warning',
        'critical': 'text-danger',
        'unknown': 'text-muted'
    };
    
    const healthIcons = {
        'healthy': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'critical': 'fas fa-times-circle',
        'unknown': 'fas fa-question-circle'
    };
    
    const healthClass = healthClasses[healthStatus] || 'text-muted';
    const healthIcon = healthIcons[healthStatus] || 'fas fa-question-circle';
    
    return `<i class="${healthIcon} ${healthClass}" title="${healthStatus}"></i>`;
}

// API Helper Functions

// Make API request
function apiRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    if (finalOptions.data && finalOptions.method !== 'GET') {
        finalOptions.body = JSON.stringify(finalOptions.data);
    }
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        });
}

// Get dashboard data
function getDashboardData() {
    return apiRequest('/admin-config/api/dashboard/');
}

// Get integrations
function getIntegrations(filters = {}) {
    const params = new URLSearchParams(filters);
    return apiRequest(`/admin-config/api/integrations/?${params}`);
}

// Get workflows
function getWorkflows(filters = {}) {
    const params = new URLSearchParams(filters);
    return apiRequest(`/admin-config/api/workflows/?${params}`);
}

// Get templates
function getTemplates(filters = {}) {
    const params = new URLSearchParams(filters);
    return apiRequest(`/admin-config/api/templates/?${params}`);
}

// Get backups
function getBackups(filters = {}) {
    const params = new URLSearchParams(filters);
    return apiRequest(`/admin-config/api/backups/?${params}`);
}

// Get audit logs
function getAuditLogs(filters = {}) {
    const params = new URLSearchParams(filters);
    return apiRequest(`/admin-config/api/audit-logs/?${params}`);
}

// Form Validation

// Validate form
function validateForm(formElement) {
    const form = $(formElement);
    let isValid = true;
    
    // Clear previous validation
    form.find('.is-invalid').removeClass('is-invalid');
    form.find('.invalid-feedback').remove();
    
    // Check required fields
    form.find('[required]').each(function() {
        const field = $(this);
        const value = field.val().trim();
        
        if (!value) {
            field.addClass('is-invalid');
            field.after('<div class="invalid-feedback">This field is required.</div>');
            isValid = false;
        }
    });
    
    // Check email fields
    form.find('[type="email"]').each(function() {
        const field = $(this);
        const value = field.val().trim();
        
        if (value && !isValidEmail(value)) {
            field.addClass('is-invalid');
            field.after('<div class="invalid-feedback">Please enter a valid email address.</div>');
            isValid = false;
        }
    });
    
    // Check URL fields
    form.find('[type="url"], .url-field').each(function() {
        const field = $(this);
        const value = field.val().trim();
        
        if (value && !isValidUrl(value)) {
            field.addClass('is-invalid');
            field.after('<div class="invalid-feedback">Please enter a valid URL.</div>');
            isValid = false;
        }
    });
    
    return isValid;
}

// Validate email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validate URL
function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// Dynamic Form Generation

// Generate dynamic form
function generateDynamicForm(schema, uiSchema = {}, formData = {}, containerId = 'dynamicFields') {
    const container = $(`#${containerId}`);
    container.empty();
    
    if (!schema || !schema.properties) {
        container.html('<p class="text-muted">No configuration fields available.</p>');
        return;
    }
    
    const properties = schema.properties;
    const required = schema.required || [];
    
    Object.keys(properties).forEach(fieldName => {
        const fieldSchema = properties[fieldName];
        const fieldUiSchema = uiSchema[fieldName] || {};
        const fieldValue = formData[fieldName] || fieldSchema.default || '';
        const isRequired = required.includes(fieldName);
        
        const fieldHtml = generateFormField(fieldName, fieldSchema, fieldUiSchema, fieldValue, isRequired);
        container.append(fieldHtml);
    });
}

// Generate form field
function generateFormField(name, schema, uiSchema, value, required) {
    const label = schema.title || name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    const description = schema.description || '';
    const type = schema.type || 'string';
    const widget = uiSchema['ui:widget'] || getDefaultWidget(schema);
    const requiredAttr = required ? 'required' : '';
    const requiredLabel = required ? ' *' : '';
    
    let fieldHtml = `
        <div class="mb-3">
            <label class="form-label" for="${name}">${label}${requiredLabel}</label>
    `;
    
    switch (widget) {
        case 'password':
            fieldHtml += `<input type="password" class="form-control" name="${name}" id="${name}" value="${value}" ${requiredAttr}>`;
            break;
        case 'textarea':
            fieldHtml += `<textarea class="form-control" name="${name}" id="${name}" rows="3" ${requiredAttr}>${value}</textarea>`;
            break;
        case 'select':
            fieldHtml += `<select class="form-select" name="${name}" id="${name}" ${requiredAttr}>`;
            if (schema.enum) {
                schema.enum.forEach(option => {
                    const selected = option === value ? 'selected' : '';
                    fieldHtml += `<option value="${option}" ${selected}>${option}</option>`;
                });
            }
            fieldHtml += `</select>`;
            break;
        case 'checkbox':
            const checked = value ? 'checked' : '';
            fieldHtml += `
                <div class="form-check">
                    <input type="checkbox" class="form-check-input" name="${name}" id="${name}" ${checked}>
                    <label class="form-check-label" for="${name}">${label}</label>
                </div>
            `;
            break;
        case 'number':
            fieldHtml += `<input type="number" class="form-control" name="${name}" id="${name}" value="${value}" ${requiredAttr}>`;
            break;
        case 'uri':
            fieldHtml += `<input type="url" class="form-control url-field" name="${name}" id="${name}" value="${value}" ${requiredAttr}>`;
            break;
        default:
            fieldHtml += `<input type="text" class="form-control" name="${name}" id="${name}" value="${value}" ${requiredAttr}>`;
    }
    
    if (description) {
        fieldHtml += `<div class="form-text">${description}</div>`;
    }
    
    fieldHtml += `</div>`;
    
    return fieldHtml;
}

// Get default widget for schema
function getDefaultWidget(schema) {
    if (schema.enum) return 'select';
    if (schema.type === 'boolean') return 'checkbox';
    if (schema.type === 'integer' || schema.type === 'number') return 'number';
    if (schema.format === 'password') return 'password';
    if (schema.format === 'uri') return 'uri';
    if (schema.type === 'string' && schema.maxLength > 100) return 'textarea';
    return 'text';
}

// Export functions for global use
window.AdminConfig = {
    showLoading,
    hideLoading,
    showAlert,
    formatDate,
    formatRelativeTime,
    formatFileSize,
    getStatusBadge,
    getHealthStatus,
    apiRequest,
    getDashboardData,
    getIntegrations,
    getWorkflows,
    getTemplates,
    getBackups,
    getAuditLogs,
    validateForm,
    generateDynamicForm
};