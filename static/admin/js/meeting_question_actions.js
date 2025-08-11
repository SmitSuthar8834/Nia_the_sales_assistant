/**
 * JavaScript for Meeting Question Admin Actions
 */

// Question management functions
function markQuestionAsked(questionId) {
    const response = prompt('Enter the response received (optional):');
    if (response !== null) { // User didn't cancel
        showLoading(questionId);
        
        fetch(`/admin/meeting_service/meetingquestion/${questionId}/mark_asked/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            },
            body: `response=${encodeURIComponent(response)}`
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(questionId);
            if (data.success) {
                showMessage('Question marked as asked successfully', 'success');
                location.reload();
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading(questionId);
            showMessage('Network error: ' + error.message, 'error');
        });
    }
}

function toggleManualOverride(questionId) {
    if (confirm('Toggle manual override for this question? This will mark it as manually customized.')) {
        showLoading(questionId);
        
        fetch(`/admin/meeting_service/meetingquestion/${questionId}/toggle_override/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(questionId);
            if (data.success) {
                showMessage(data.message, 'success');
                location.reload();
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading(questionId);
            showMessage('Network error: ' + error.message, 'error');
        });
    }
}

function updateQuestionEffectiveness(questionId) {
    const score = prompt('Enter effectiveness score (0-100):');
    if (score !== null && !isNaN(score) && score >= 0 && score <= 100) {
        showLoading(questionId);
        
        fetch(`/admin/meeting_service/meetingquestion/${questionId}/update_effectiveness/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            },
            body: `effectiveness_score=${score}`
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(questionId);
            if (data.success) {
                showMessage('Question effectiveness updated successfully', 'success');
                location.reload();
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading(questionId);
            showMessage('Network error: ' + error.message, 'error');
        });
    } else if (score !== null) {
        showMessage('Please enter a valid number between 0 and 100.', 'warning');
    }
}

function createQuestionVariation(questionId) {
    if (confirm('Create a variation of this question for A/B testing?')) {
        showLoading(questionId);
        
        fetch(`/admin/meeting_service/meetingquestion/${questionId}/create_variation/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(questionId);
            if (data.success) {
                showMessage('Question variation created successfully', 'success');
                if (data.variation_id) {
                    const editUrl = `/admin/meeting_service/meetingquestion/${data.variation_id}/change/`;
                    if (confirm('Question variation created. Would you like to edit it now?')) {
                        window.open(editUrl, '_blank');
                    }
                }
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading(questionId);
            showMessage('Network error: ' + error.message, 'error');
        });
    }
}

// Meeting management functions
function generateQuestionsForMeeting(meetingId) {
    if (confirm('Generate AI questions for this meeting based on lead data?')) {
        showLoading(meetingId);
        
        fetch(`/admin/meeting_service/meeting/${meetingId}/generate_questions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(meetingId);
            if (data.success) {
                showMessage(`Generated ${data.questions_count} questions for meeting`, 'success');
                location.reload();
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading(meetingId);
            showMessage('Network error: ' + error.message, 'error');
        });
    }
}

function regenerateQuestionsForMeeting(meetingId) {
    if (confirm('Regenerate all AI questions for this meeting? This will replace existing questions.')) {
        showLoading(meetingId);
        
        fetch(`/admin/meeting_service/meeting/${meetingId}/regenerate_questions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(meetingId);
            if (data.success) {
                showMessage(`Regenerated questions: deleted ${data.deleted_count}, created ${data.created_count}`, 'success');
                location.reload();
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading(meetingId);
            showMessage('Network error: ' + error.message, 'error');
        });
    }
}

// Bulk operations
function bulkMarkQuestionsAsked() {
    const selectedQuestions = getSelectedItems();
    if (selectedQuestions.length === 0) {
        showMessage('Please select questions to mark as asked.', 'warning');
        return;
    }
    
    if (confirm(`Mark ${selectedQuestions.length} selected question(s) as asked?`)) {
        showBulkLoading();
        
        fetch('/admin/meeting_service/meetingquestion/bulk_mark_asked/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            },
            body: `question_ids=${selectedQuestions.join('&question_ids=')}`
        })
        .then(response => response.json())
        .then(data => {
            hideBulkLoading();
            if (data.success) {
                showMessage(`Successfully marked ${data.updated_count} question(s) as asked`, 'success');
                location.reload();
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideBulkLoading();
            showMessage('Network error: ' + error.message, 'error');
        });
    }
}

function bulkUpdateQuestionPriority() {
    const selectedQuestions = getSelectedItems();
    if (selectedQuestions.length === 0) {
        showMessage('Please select questions to update.', 'warning');
        return;
    }
    
    const newPriority = prompt('Enter new priority level (1-10):');
    if (newPriority !== null && !isNaN(newPriority) && newPriority >= 1 && newPriority <= 10) {
        showBulkLoading();
        
        fetch('/admin/meeting_service/meetingquestion/bulk_update_priority/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            },
            body: `question_ids=${selectedQuestions.join('&question_ids=')}&new_priority=${newPriority}`
        })
        .then(response => response.json())
        .then(data => {
            hideBulkLoading();
            if (data.success) {
                showMessage(`Updated priority for ${data.updated_count} question(s)`, 'success');
                location.reload();
            } else {
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideBulkLoading();
            showMessage('Network error: ' + error.message, 'error');
        });
    } else if (newPriority !== null) {
        showMessage('Please enter a valid number between 1 and 10.', 'warning');
    }
}

function exportQuestionAnalytics() {
    const selectedQuestions = getSelectedItems();
    
    showBulkLoading();
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/admin/meeting_service/meetingquestion/export_analytics/';
    
    // Add CSRF token
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = getCsrfToken();
    form.appendChild(csrfInput);
    
    // Add selected question IDs if any
    selectedQuestions.forEach(id => {
        const idInput = document.createElement('input');
        idInput.type = 'hidden';
        idInput.name = 'question_ids';
        idInput.value = id;
        form.appendChild(idInput);
    });
    
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    
    setTimeout(hideBulkLoading, 2000);
}

// Analytics functions
function analyzeQuestionPerformance() {
    const selectedQuestions = getSelectedItems();
    if (selectedQuestions.length === 0) {
        showMessage('Please select questions to analyze.', 'warning');
        return;
    }
    
    const analysisUrl = `/admin/meeting_service/meetingquestion/analyze_performance/?ids=${selectedQuestions.join(',')}`;
    window.open(analysisUrl, '_blank', 'width=1000,height=700');
}

function showQuestionTrends() {
    const trendsUrl = '/admin/meeting_service/analytics/question_trends/';
    window.open(trendsUrl, '_blank', 'width=1200,height=800');
}

function compareQuestionTypes() {
    const comparisonUrl = '/admin/meeting_service/analytics/question_type_comparison/';
    window.open(comparisonUrl, '_blank', 'width=1200,height=800');
}

// Utility functions
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function getSelectedItems() {
    const checkboxes = document.querySelectorAll('input[name="_selected_action"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function showLoading(itemId) {
    const button = document.querySelector(`[onclick*="${itemId}"]`);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="question-loading"></span> Loading...';
    }
}

function hideLoading(itemId) {
    // This would restore the original button state
    // For now, we'll just reload the page
}

function showBulkLoading() {
    const bulkActions = document.querySelector('.bulk-actions');
    if (bulkActions) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'bulk-loading';
        loadingDiv.innerHTML = '<span class="question-loading"></span> Processing bulk action...';
        loadingDiv.style.cssText = 'text-align: center; padding: 10px; background: #fff3cd; border-radius: 5px; margin: 10px 0;';
        bulkActions.appendChild(loadingDiv);
    }
}

function hideBulkLoading() {
    const loadingDiv = document.querySelector('.bulk-loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `admin-message ${type}`;
    messageDiv.textContent = message;
    
    // Insert at the top of the content
    const content = document.querySelector('.content');
    if (content) {
        content.insertBefore(messageDiv, content.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }
}

// Advanced filtering
function initializeAdvancedFilters() {
    const filterContainer = document.createElement('div');
    filterContainer.className = 'question-filters';
    filterContainer.innerHTML = `
        <h4>Advanced Filters</h4>
        <div class="filter-group">
            <label>Question Type:</label>
            <select id="filter-question-type">
                <option value="">All Types</option>
                <option value="discovery">Discovery</option>
                <option value="budget">Budget</option>
                <option value="timeline">Timeline</option>
                <option value="decision_makers">Decision Makers</option>
                <option value="pain_points">Pain Points</option>
                <option value="requirements">Requirements</option>
                <option value="competition">Competition</option>
                <option value="closing">Closing</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Priority:</label>
            <select id="filter-priority">
                <option value="">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Status:</label>
            <select id="filter-status">
                <option value="">All Statuses</option>
                <option value="asked">Asked</option>
                <option value="not-asked">Not Asked</option>
            </select>
        </div>
        <div class="filter-group">
            <label>AI Generated:</label>
            <select id="filter-ai-generated">
                <option value="">All</option>
                <option value="true">AI Generated</option>
                <option value="false">Manual</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Effectiveness:</label>
            <select id="filter-effectiveness">
                <option value="">All</option>
                <option value="high">High (70%+)</option>
                <option value="medium">Medium (50-69%)</option>
                <option value="low">Low (<50%)</option>
            </select>
        </div>
        <button onclick="applyFilters()" class="button" style="background: #007cba; color: white;">Apply Filters</button>
        <button onclick="clearFilters()" class="button" style="background: #6c757d; color: white;">Clear</button>
    `;
    
    const changeList = document.querySelector('#changelist');
    if (changeList) {
        changeList.insertBefore(filterContainer, changeList.firstChild);
    }
}

function applyFilters() {
    const filters = {
        questionType: document.getElementById('filter-question-type').value,
        priority: document.getElementById('filter-priority').value,
        status: document.getElementById('filter-status').value,
        aiGenerated: document.getElementById('filter-ai-generated').value,
        effectiveness: document.getElementById('filter-effectiveness').value
    };
    
    const rows = document.querySelectorAll('#result_list tbody tr');
    rows.forEach(row => {
        let show = true;
        
        // Apply each filter
        if (filters.questionType && !row.textContent.toLowerCase().includes(filters.questionType)) {
            show = false;
        }
        
        if (filters.priority) {
            const priorityCell = row.querySelector('.field-priority_display');
            if (priorityCell && !priorityCell.textContent.toLowerCase().includes(filters.priority)) {
                show = false;
            }
        }
        
        if (filters.status) {
            const statusCell = row.querySelector('.field-asked_status');
            if (statusCell) {
                const isAsked = statusCell.textContent.includes('Asked');
                if ((filters.status === 'asked' && !isAsked) || (filters.status === 'not-asked' && isAsked)) {
                    show = false;
                }
            }
        }
        
        if (filters.aiGenerated) {
            const aiCell = row.querySelector('.field-ai_generated');
            if (aiCell) {
                const isAI = aiCell.textContent.includes('True') || aiCell.textContent.includes('✓');
                if ((filters.aiGenerated === 'true' && !isAI) || (filters.aiGenerated === 'false' && isAI)) {
                    show = false;
                }
            }
        }
        
        row.style.display = show ? '' : 'none';
    });
    
    showMessage('Filters applied successfully', 'success');
}

function clearFilters() {
    document.getElementById('filter-question-type').value = '';
    document.getElementById('filter-priority').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-ai-generated').value = '';
    document.getElementById('filter-effectiveness').value = '';
    
    const rows = document.querySelectorAll('#result_list tbody tr');
    rows.forEach(row => {
        row.style.display = '';
    });
    
    showMessage('Filters cleared', 'info');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add performance indicators
    addQuestionPerformanceIndicators();
    
    // Initialize advanced filters
    initializeAdvancedFilters();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+Shift+A to mark selected questions as asked
        if (e.ctrlKey && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            bulkMarkQuestionsAsked();
        }
        
        // Ctrl+Shift+P to bulk update priority
        if (e.ctrlKey && e.shiftKey && e.key === 'P') {
            e.preventDefault();
            bulkUpdateQuestionPriority();
        }
        
        // Ctrl+Shift+E to export analytics
        if (e.ctrlKey && e.shiftKey && e.key === 'E') {
            e.preventDefault();
            exportQuestionAnalytics();
        }
    });
    
    // Add tooltips to action buttons
    const actionButtons = document.querySelectorAll('.question-actions button');
    actionButtons.forEach(button => {
        button.title = button.textContent.trim();
    });
    
    // Auto-refresh effectiveness scores every 30 seconds
    setInterval(refreshEffectivenessScores, 30000);
});

function addQuestionPerformanceIndicators() {
    const effectivenessColumns = document.querySelectorAll('.field-effectiveness_score');
    effectivenessColumns.forEach(cell => {
        const text = cell.textContent.trim();
        const score = parseFloat(text);
        
        if (!isNaN(score)) {
            let indicator = '';
            let className = '';
            
            if (score >= 70) {
                indicator = '🟢';
                className = 'effectiveness-high';
            } else if (score >= 50) {
                indicator = '🟡';
                className = 'effectiveness-medium';
            } else {
                indicator = '🔴';
                className = 'effectiveness-low';
            }
            
            cell.innerHTML = `<span class="performance-indicator ${className.replace('effectiveness-', '')}"></span> ${cell.innerHTML}`;
            cell.className += ' ' + className;
        }
    });
}

function refreshEffectivenessScores() {
    // This would refresh effectiveness scores in the background
    // For now, we'll just add a subtle indication that data is being refreshed
    const statusBar = document.querySelector('.paginator');
    if (statusBar) {
        const refreshIndicator = document.createElement('span');
        refreshIndicator.textContent = ' 🔄';
        refreshIndicator.style.opacity = '0.5';
        statusBar.appendChild(refreshIndicator);
        
        setTimeout(() => {
            if (refreshIndicator.parentNode) {
                refreshIndicator.parentNode.removeChild(refreshIndicator);
            }
        }, 2000);
    }
}