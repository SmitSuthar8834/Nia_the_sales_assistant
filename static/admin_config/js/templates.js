// Admin Config Templates JavaScript

// Global variables
let currentTemplates = [];
let currentFilter = 'all';

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadTemplates();
    setupEventListeners();
});

function setupEventListeners() {
    // Template form submission
    const templateForm = document.getElementById('addTemplateForm');
    if (templateForm) {
        templateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveTemplate();
        });
    }
}

// Load templates from API
async function loadTemplates() {
    try {
        const response = await fetch('/admin-config/api/templates/');
        if (response.ok) {
            currentTemplates = await response.json();
            renderTemplates();
        } else {
            console.error('Failed to load templates');
            showError('Failed to load templates');
        }
    } catch (error) {
        console.error('Error loading templates:', error);
        showError('Error loading templates');
    }
}

// Render templates in the grid
function renderTemplates() {
    const grid = document.getElementById('templatesGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (!grid) return;
    
    // Filter templates
    let filteredTemplates = currentTemplates;
    if (currentFilter !== 'all') {
        filteredTemplates = currentTemplates.filter(template => 
            template.category === currentFilter || 
            (currentFilter === 'custom' && !template.is_official)
        );
    }
    
    if (filteredTemplates.length === 0) {
        grid.style.display = 'none';
        if (emptyState) emptyState.style.display = 'block';
        return;
    }
    
    grid.style.display = 'flex';
    if (emptyState) emptyState.style.display = 'none';
    
    // Clear existing content
    grid.innerHTML = '';
    
    // Render each template
    filteredTemplates.forEach(template => {
        const templateCard = createTemplateCard(template);
        grid.appendChild(templateCard);
    });
}

// Create template card HTML
function createTemplateCard(template) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4 mb-4 template-card';
    col.setAttribute('data-category', template.category);
    
    const categoryColors = {
        'crm': 'primary',
        'meeting': 'info',
        'workflow': 'secondary',
        'notification': 'warning',
        'security': 'danger'
    };
    
    const categoryIcons = {
        'crm': 'fas fa-users',
        'meeting': 'fas fa-video',
        'workflow': 'fas fa-cogs',
        'notification': 'fas fa-bell',
        'security': 'fas fa-shield-alt'
    };
    
    const color = categoryColors[template.category] || 'secondary';
    const icon = categoryIcons[template.category] || 'fas fa-file';
    
    col.innerHTML = `
        <div class="card h-100">
            <div class="card-header bg-${color} text-white">
                <h5 class="card-title mb-0">
                    <i class="${icon} me-2"></i>${template.name}
                </h5>
            </div>
            <div class="card-body">
                <p class="card-text">${template.description}</p>
                <div class="mb-3">
                    ${template.is_official ? '<span class="badge bg-success">Official</span>' : '<span class="badge bg-info">Custom</span>'}
                    <span class="badge bg-secondary">v${template.version}</span>
                    ${template.usage_count > 0 ? `<span class="badge bg-warning">${template.usage_count} uses</span>` : ''}
                </div>
                <div class="d-flex justify-content-between">
                    <button class="btn btn-outline-primary btn-sm" onclick="previewTemplate('${template.id}')">
                        <i class="fas fa-eye me-1"></i>Preview
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="useTemplate('${template.id}')">
                        <i class="fas fa-download me-1"></i>Use Template
                    </button>
                </div>
            </div>
        </div>
    `;
    
    return col;
}

// Filter templates by category
function filterTemplates(category, element) {
    currentFilter = category;
    
    // Update active button
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (element) {
        element.classList.add('active');
    }
    
    renderTemplates();
}

// Preview template
async function previewTemplate(templateId) {
    try {
        const response = await fetch(`/admin-config/api/templates/${templateId}/`);
        if (response.ok) {
            const template = await response.json();
            showTemplatePreview(template);
        } else {
            showError('Failed to load template details');
        }
    } catch (error) {
        console.error('Error loading template:', error);
        showError('Error loading template');
    }
}

// Show template preview modal
function showTemplatePreview(template) {
    const modal = document.getElementById('templatePreviewModal');
    const content = document.getElementById('templatePreviewContent');
    const title = document.getElementById('templatePreviewModalLabel');
    const useBtn = document.getElementById('useTemplateBtn');
    
    if (!modal || !content) return;
    
    title.textContent = `${template.name} Preview`;
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Template Information</h6>
                <table class="table table-sm">
                    <tr><td><strong>Name:</strong></td><td>${template.name}</td></tr>
                    <tr><td><strong>Category:</strong></td><td>${template.category}</td></tr>
                    <tr><td><strong>Version:</strong></td><td>${template.version}</td></tr>
                    <tr><td><strong>Official:</strong></td><td>${template.is_official ? 'Yes' : 'No'}</td></tr>
                    <tr><td><strong>Usage Count:</strong></td><td>${template.usage_count}</td></tr>
                </table>
                <h6>Description</h6>
                <p>${template.description}</p>
            </div>
            <div class="col-md-6">
                <h6>Configuration Schema</h6>
                <pre class="bg-light p-3 rounded"><code>${JSON.stringify(template.configuration_schema, null, 2)}</code></pre>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <h6>Default Configuration</h6>
                <pre class="bg-light p-3 rounded"><code>${JSON.stringify(template.default_configuration, null, 2)}</code></pre>
            </div>
        </div>
    `;
    
    useBtn.onclick = () => useTemplate(template.id);
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

// Use template to create new integration
async function useTemplate(templateId) {
    try {
        const name = prompt('Enter a name for this integration:');
        if (!name) return;
        
        const response = await fetch(`/admin-config/api/templates/${templateId}/use_template/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                name: name,
                integration_type: 'crm_salesforce' // This should be dynamic based on template
            })
        });
        
        if (response.ok) {
            const integration = await response.json();
            showSuccess(`Integration "${integration.name}" created successfully!`);
            // Optionally redirect to integrations page
            // window.location.href = '/admin-config/integrations/';
        } else {
            const error = await response.json();
            showError('Failed to create integration: ' + JSON.stringify(error));
        }
    } catch (error) {
        console.error('Error creating integration:', error);
        showError('Error creating integration');
    }
}

// Save new template
async function saveTemplate() {
    const form = document.getElementById('addTemplateForm');
    const formData = new FormData(form);
    
    const templateData = {
        name: formData.get('templateName'),
        description: formData.get('templateDescription'),
        category: formData.get('templateCategory'),
        configuration_schema: JSON.parse(formData.get('templateConfig') || '{}'),
        default_configuration: {},
        ui_schema: {}
    };
    
    try {
        const response = await fetch('/admin-config/api/templates/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(templateData)
        });
        
        if (response.ok) {
            const template = await response.json();
            showSuccess(`Template "${template.name}" created successfully!`);
            
            // Close modal and reload templates
            const modal = bootstrap.Modal.getInstance(document.getElementById('addTemplateModal'));
            modal.hide();
            form.reset();
            loadTemplates();
        } else {
            const error = await response.json();
            showError('Failed to create template: ' + JSON.stringify(error));
        }
    } catch (error) {
        console.error('Error creating template:', error);
        showError('Error creating template');
    }
}

// Import template
function importTemplate() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const templateData = JSON.parse(e.target.result);
                    importTemplateData(templateData);
                } catch (error) {
                    showError('Invalid JSON file');
                }
            };
            reader.readAsText(file);
        }
    };
    input.click();
}

// Import template data
async function importTemplateData(templateData) {
    try {
        const response = await fetch('/admin-config/api/templates/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(templateData)
        });
        
        if (response.ok) {
            const template = await response.json();
            showSuccess(`Template "${template.name}" imported successfully!`);
            loadTemplates();
        } else {
            const error = await response.json();
            showError('Failed to import template: ' + JSON.stringify(error));
        }
    } catch (error) {
        console.error('Error importing template:', error);
        showError('Error importing template');
    }
}

// Utility functions
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function showSuccess(message) {
    // You can implement a toast notification system here
    alert('Success: ' + message);
}

function showError(message) {
    // You can implement a toast notification system here
    alert('Error: ' + message);
}

// Export functions for global access
window.filterTemplates = filterTemplates;
window.previewTemplate = previewTemplate;
window.useTemplate = useTemplate;
window.saveTemplate = saveTemplate;
window.importTemplate = importTemplate;