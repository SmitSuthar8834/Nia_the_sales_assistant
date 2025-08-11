/**
 * JavaScript for Question Template Admin Actions
 */

// Function to test a question template
function testTemplate(templateId) {
    if (confirm('Test this question template with sample data?')) {
        // Create a modal or redirect to test the template
        const testUrl = `/admin/meeting_service/questiontemplate/${templateId}/test/`;
        window.open(testUrl, '_blank', 'width=800,height=600');
    }
}

// Function to duplicate a question template
function duplicateTemplate(templateId) {
    if (confirm('Create a duplicate of this question template?')) {
        // Submit a form to duplicate the template
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/questiontemplate/${templateId}/duplicate/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Function to view template analytics
function viewTemplateAnalytics(templateId) {
    const analyticsUrl = `/admin/meeting_service/questiontemplate/${templateId}/analytics/`;
    window.open(analyticsUrl, '_blank', 'width=1000,height=700');
}

// Function to mark a question as asked
function markQuestionAsked(questionId) {
    const response = prompt('Enter the response received (optional):');
    if (response !== null) { // User didn't cancel
        // Submit the update
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/meetingquestion/${questionId}/mark_asked/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add response
        const responseInput = document.createElement('input');
        responseInput.type = 'hidden';
        responseInput.name = 'response';
        responseInput.value = response;
        form.appendChild(responseInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Function to toggle manual override for a question
function toggleManualOverride(questionId) {
    if (confirm('Toggle manual override for this question? This will mark it as manually customized.')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/meetingquestion/${questionId}/toggle_override/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Function to update question effectiveness
function updateQuestionEffectiveness(questionId) {
    const score = prompt('Enter effectiveness score (0-100):');
    if (score !== null && !isNaN(score) && score >= 0 && score <= 100) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/meetingquestion/${questionId}/update_effectiveness/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add score
        const scoreInput = document.createElement('input');
        scoreInput.type = 'hidden';
        scoreInput.name = 'effectiveness_score';
        scoreInput.value = score;
        form.appendChild(scoreInput);
        
        document.body.appendChild(form);
        form.submit();
    } else if (score !== null) {
        alert('Please enter a valid number between 0 and 100.');
    }
}

// Function to generate questions for a meeting
function generateQuestionsForMeeting(meetingId) {
    if (confirm('Generate AI questions for this meeting based on lead data?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/meeting/${meetingId}/generate_questions/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Function to regenerate questions for a meeting
function regenerateQuestionsForMeeting(meetingId) {
    if (confirm('Regenerate all AI questions for this meeting? This will replace existing questions.')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/meeting/${meetingId}/regenerate_questions/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Function to export question analytics
function exportQuestionAnalytics() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/admin/meeting_service/meetingquestion/export_analytics/';
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);
    
    document.body.appendChild(form);
    form.submit();
}

// Function to bulk update question priorities
function bulkUpdatePriorities() {
    const newPriority = prompt('Enter new priority level (1-10):');
    if (newPriority !== null && !isNaN(newPriority) && newPriority >= 1 && newPriority <= 10) {
        // Get selected questions
        const selectedQuestions = document.querySelectorAll('input[name="_selected_action"]:checked');
        if (selectedQuestions.length === 0) {
            alert('Please select questions to update.');
            return;
        }
        
        if (confirm(`Update priority to ${newPriority} for ${selectedQuestions.length} selected question(s)?`)) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/admin/meeting_service/meetingquestion/bulk_update_priority/';
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
            
            // Add priority
            const priorityInput = document.createElement('input');
            priorityInput.type = 'hidden';
            priorityInput.name = 'new_priority';
            priorityInput.value = newPriority;
            form.appendChild(priorityInput);
            
            // Add selected question IDs
            selectedQuestions.forEach(checkbox => {
                const idInput = document.createElement('input');
                idInput.type = 'hidden';
                idInput.name = 'question_ids';
                idInput.value = checkbox.value;
                form.appendChild(idInput);
            });
            
            document.body.appendChild(form);
            form.submit();
        }
    } else if (newPriority !== null) {
        alert('Please enter a valid number between 1 and 10.');
    }
}

// Advanced question template management functions
function createQuestionFromTemplate(templateId) {
    const meetingId = prompt('Enter Meeting ID to create question for:');
    if (meetingId) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/questiontemplate/${templateId}/create_question/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add meeting ID
        const meetingInput = document.createElement('input');
        meetingInput.type = 'hidden';
        meetingInput.name = 'meeting_id';
        meetingInput.value = meetingId;
        form.appendChild(meetingInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

function bulkActivateTemplates() {
    const selectedTemplates = document.querySelectorAll('input[name="_selected_action"]:checked');
    if (selectedTemplates.length === 0) {
        alert('Please select templates to activate.');
        return;
    }
    
    if (confirm(`Activate ${selectedTemplates.length} selected template(s)?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/meeting_service/questiontemplate/bulk_activate/';
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add selected template IDs
        selectedTemplates.forEach(checkbox => {
            const idInput = document.createElement('input');
            idInput.type = 'hidden';
            idInput.name = 'template_ids';
            idInput.value = checkbox.value;
            form.appendChild(idInput);
        });
        
        document.body.appendChild(form);
        form.submit();
    }
}

function bulkDeactivateTemplates() {
    const selectedTemplates = document.querySelectorAll('input[name="_selected_action"]:checked');
    if (selectedTemplates.length === 0) {
        alert('Please select templates to deactivate.');
        return;
    }
    
    if (confirm(`Deactivate ${selectedTemplates.length} selected template(s)?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/meeting_service/questiontemplate/bulk_deactivate/';
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add selected template IDs
        selectedTemplates.forEach(checkbox => {
            const idInput = document.createElement('input');
            idInput.type = 'hidden';
            idInput.name = 'template_ids';
            idInput.value = checkbox.value;
            form.appendChild(idInput);
        });
        
        document.body.appendChild(form);
        form.submit();
    }
}

function exportTemplatePerformance() {
    const selectedTemplates = document.querySelectorAll('input[name="_selected_action"]:checked');
    const templateIds = Array.from(selectedTemplates).map(cb => cb.value);
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/admin/meeting_service/questiontemplate/export_performance/';
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);
    
    // Add template IDs
    templateIds.forEach(id => {
        const idInput = document.createElement('input');
        idInput.type = 'hidden';
        idInput.name = 'template_ids';
        idInput.value = id;
        form.appendChild(idInput);
    });
    
    document.body.appendChild(form);
    form.submit();
}

function optimizeTemplate(templateId) {
    if (confirm('Run AI optimization on this template? This will analyze performance data and suggest improvements.')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/questiontemplate/${templateId}/optimize/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Enhanced question management functions
function bulkMarkQuestionsAsked() {
    const selectedQuestions = document.querySelectorAll('input[name="_selected_action"]:checked');
    if (selectedQuestions.length === 0) {
        alert('Please select questions to mark as asked.');
        return;
    }
    
    if (confirm(`Mark ${selectedQuestions.length} selected question(s) as asked?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/meeting_service/meetingquestion/bulk_mark_asked/';
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add selected question IDs
        selectedQuestions.forEach(checkbox => {
            const idInput = document.createElement('input');
            idInput.type = 'hidden';
            idInput.name = 'question_ids';
            idInput.value = checkbox.value;
            form.appendChild(idInput);
        });
        
        document.body.appendChild(form);
        form.submit();
    }
}

function analyzeQuestionPerformance() {
    const selectedQuestions = document.querySelectorAll('input[name="_selected_action"]:checked');
    if (selectedQuestions.length === 0) {
        alert('Please select questions to analyze.');
        return;
    }
    
    const questionIds = Array.from(selectedQuestions).map(cb => cb.value);
    const analysisUrl = `/admin/meeting_service/meetingquestion/analyze_performance/?ids=${questionIds.join(',')}`;
    window.open(analysisUrl, '_blank', 'width=1000,height=700');
}

function createQuestionVariation(questionId) {
    if (confirm('Create a variation of this question for A/B testing?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/meeting_service/meetingquestion/${questionId}/create_variation/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Advanced analytics functions
function showQuestionTrends() {
    const trendsUrl = '/admin/meeting_service/analytics/question_trends/';
    window.open(trendsUrl, '_blank', 'width=1200,height=800');
}

function showTemplateComparison() {
    const comparisonUrl = '/admin/meeting_service/analytics/template_comparison/';
    window.open(comparisonUrl, '_blank', 'width=1200,height=800');
}

function showIndustryPerformance() {
    const industryUrl = '/admin/meeting_service/analytics/industry_performance/';
    window.open(industryUrl, '_blank', 'width=1200,height=800');
}

// Initialize admin interface enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Add tooltips to action buttons
    const actionButtons = document.querySelectorAll('.question-actions button, .template-actions button');
    actionButtons.forEach(button => {
        button.title = button.textContent.trim();
    });
    
    // Add confirmation to bulk actions
    const bulkActionSelect = document.querySelector('select[name="action"]');
    if (bulkActionSelect) {
        bulkActionSelect.addEventListener('change', function() {
            if (this.value === 'delete_selected') {
                const originalSubmit = document.querySelector('button[name="index"]');
                if (originalSubmit) {
                    originalSubmit.addEventListener('click', function(e) {
                        if (!confirm('Are you sure you want to delete the selected items? This action cannot be undone.')) {
                            e.preventDefault();
                        }
                    });
                }
            }
        });
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+G to generate questions (if on meeting page)
        if (e.ctrlKey && e.key === 'g' && window.location.pathname.includes('/meeting/')) {
            e.preventDefault();
            const meetingId = window.location.pathname.match(/\/meeting\/([^\/]+)\//);
            if (meetingId) {
                generateQuestionsForMeeting(meetingId[1]);
            }
        }
        
        // Ctrl+R to regenerate questions (if on meeting page)
        if (e.ctrlKey && e.key === 'r' && window.location.pathname.includes('/meeting/')) {
            e.preventDefault();
            const meetingId = window.location.pathname.match(/\/meeting\/([^\/]+)\//);
            if (meetingId) {
                regenerateQuestionsForMeeting(meetingId[1]);
            }
        }
        
        // Ctrl+T to test template (if on template page)
        if (e.ctrlKey && e.key === 't' && window.location.pathname.includes('/questiontemplate/')) {
            e.preventDefault();
            const templateId = window.location.pathname.match(/\/questiontemplate\/([^\/]+)\//);
            if (templateId) {
                testTemplate(templateId[1]);
            }
        }
        
        // Ctrl+A to view analytics (if on template page)
        if (e.ctrlKey && e.key === 'a' && window.location.pathname.includes('/questiontemplate/')) {
            e.preventDefault();
            const templateId = window.location.pathname.match(/\/questiontemplate\/([^\/]+)\//);
            if (templateId) {
                viewTemplateAnalytics(templateId[1]);
            }
        }
    });
    
    // Add real-time search for templates
    const searchInput = document.querySelector('#searchbar');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterTemplates(this.value);
            }, 300);
        });
    }
    
    // Add template performance indicators
    addPerformanceIndicators();
    
    // Initialize tooltips
    initializeTooltips();
});

function filterTemplates(searchTerm) {
    const rows = document.querySelectorAll('#result_list tbody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function addPerformanceIndicators() {
    // Add visual performance indicators to template rows
    const successRateCells = document.querySelectorAll('.field-success_rate_display');
    successRateCells.forEach(cell => {
        const text = cell.textContent.trim();
        const match = text.match(/(\d+\.?\d*)%/);
        if (match) {
            const rate = parseFloat(match[1]);
            let indicator = '';
            if (rate >= 70) {
                indicator = '🟢';
            } else if (rate >= 50) {
                indicator = '🟡';
            } else {
                indicator = '🔴';
            }
            cell.innerHTML = indicator + ' ' + cell.innerHTML;
        }
    });
}

function initializeTooltips() {
    // Add tooltips to various elements
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const tooltip = document.createElement('div');
    tooltip.className = 'admin-tooltip';
    tooltip.textContent = event.target.getAttribute('data-tooltip');
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 3px;
        font-size: 12px;
        z-index: 1000;
        pointer-events: none;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
    
    event.target._tooltip = tooltip;
}

function hideTooltip(event) {
    if (event.target._tooltip) {
        document.body.removeChild(event.target._tooltip);
        delete event.target._tooltip;
    }
}