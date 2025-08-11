/**
 * JavaScript functions for Meeting Admin actions
 * Handles meeting status changes and pre-meeting intelligence generation
 */

// Meeting status management functions
function startMeeting(meetingId) {
    if (confirm('Are you sure you want to start this meeting?')) {
        updateMeetingStatus(meetingId, 'start', 'Starting meeting...');
    }
}

function completeMeeting(meetingId) {
    if (confirm('Are you sure you want to mark this meeting as completed?')) {
        updateMeetingStatus(meetingId, 'complete', 'Completing meeting...');
    }
}

function cancelMeeting(meetingId) {
    if (confirm('Are you sure you want to cancel this meeting?')) {
        updateMeetingStatus(meetingId, 'cancel', 'Cancelling meeting...');
    }
}

function updateMeetingStatus(meetingId, action, loadingMessage) {
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ ' + loadingMessage;
    button.disabled = true;
    
    // Make AJAX request to update meeting status
    fetch(`/meeting_service/admin/meeting_service/meeting/${meetingId}/update_status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            action: action,
            meeting_id: meetingId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload the page to show updated status
            location.reload();
        } else {
            alert('Error: ' + (data.error || 'Unknown error occurred'));
            button.innerHTML = originalText;
            button.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating meeting status');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

// Pre-meeting intelligence generation functions
function generatePreparationMaterials(meetingId) {
    if (confirm('Generate comprehensive preparation materials for this meeting? This may take a few moments.')) {
        generateIntelligence(meetingId, 'preparation_materials', 'Generating preparation materials...');
    }
}

function generateMeetingAgenda(meetingId) {
    if (confirm('Generate AI-powered meeting agenda? This will replace any existing agenda.')) {
        generateIntelligence(meetingId, 'agenda', 'Generating meeting agenda...');
    }
}

function generateTalkingPoints(meetingId) {
    if (confirm('Generate AI-powered talking points for this meeting?')) {
        generateIntelligence(meetingId, 'talking_points', 'Generating talking points...');
    }
}

function generateCompetitiveAnalysis(meetingId) {
    if (confirm('Generate competitive analysis and positioning strategy?')) {
        generateIntelligence(meetingId, 'competitive_analysis', 'Generating competitive analysis...');
    }
}

function generateIntelligence(meetingId, type, loadingMessage) {
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ ' + loadingMessage;
    button.disabled = true;
    
    // Make AJAX request to generate intelligence
    fetch(`/meeting_service/admin/meeting_service/meeting/${meetingId}/generate_intelligence/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            type: type,
            meeting_id: meetingId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('Success: ' + data.message, 'success');
            
            // Optionally reload the page to show updated data
            if (data.reload) {
                setTimeout(() => location.reload(), 1500);
            }
        } else {
            showNotification('Error: ' + (data.error || 'Unknown error occurred'), 'error');
        }
        
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error generating intelligence materials', 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

// Question management functions
function markQuestionAsked(questionId) {
    const response = prompt('Enter the response received to this question (optional):');
    if (response !== null) { // User didn't cancel
        updateQuestionStatus(questionId, 'mark_asked', response);
    }
}

function toggleManualOverride(questionId) {
    if (confirm('Toggle manual override for this question? This will mark it as manually managed.')) {
        updateQuestionStatus(questionId, 'toggle_override');
    }
}

function updateQuestionEffectiveness(questionId) {
    const score = prompt('Enter effectiveness score (0-100):');
    if (score !== null && !isNaN(score) && score >= 0 && score <= 100) {
        updateQuestionStatus(questionId, 'update_effectiveness', score);
    } else if (score !== null) {
        alert('Please enter a valid score between 0 and 100');
    }
}

function updateQuestionStatus(questionId, action, data = null) {
    fetch(`/admin/meeting_service/meetingquestion/${questionId}/update_status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            action: action,
            data: data
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('Question updated successfully', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('Error: ' + (result.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating question', 'error');
    });
}

// Utility functions
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

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    
    // Set background color based on type
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
    
    // Allow manual close on click
    notification.addEventListener('click', () => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Meeting admin actions initialized');
});
//
 //Meeting Outcome Tracking Functions

function generateMeetingSummary(meetingId) {
    if (confirm('Generate post-meeting summary and key takeaways? This will analyze the meeting content and outcomes.')) {
        processOutcomeComponent(meetingId, 'summary', 'Generating meeting summary...');
    }
}

function extractActionItems(meetingId) {
    if (confirm('Extract action items and assignments from this meeting? This will identify tasks and responsibilities.')) {
        processOutcomeComponent(meetingId, 'action_items', 'Extracting action items...');
    }
}

function scheduleFollowUp(meetingId) {
    if (confirm('Schedule follow-up actions and next steps? This will create a comprehensive follow-up plan.')) {
        processOutcomeComponent(meetingId, 'follow_up', 'Scheduling follow-up actions...');
    }
}

function updateLeadScoring(meetingId) {
    if (confirm('Update lead scoring based on meeting outcomes? This will analyze the meeting impact on lead quality.')) {
        processOutcomeComponent(meetingId, 'scoring', 'Updating lead scoring...');
    }
}

function processCompleteOutcome(meetingId) {
    if (confirm('Process all meeting outcomes (summary, action items, follow-up, and lead scoring)? This comprehensive analysis may take a few minutes.')) {
        processOutcomeComponent(meetingId, 'complete', 'Processing all meeting outcomes...');
    }
}

function processOutcomeComponent(meetingId, component, loadingMessage) {
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ ' + loadingMessage;
    button.disabled = true;
    
    // Determine the endpoint based on component type
    let endpoint;
    switch (component) {
        case 'summary':
            endpoint = '/meeting_service/admin/meeting_service/meeting/generate_summary/';
            break;
        case 'action_items':
            endpoint = '/meeting_service/admin/meeting_service/meeting/extract_action_items/';
            break;
        case 'follow_up':
            endpoint = '/meeting_service/admin/meeting_service/meeting/schedule_follow_up/';
            break;
        case 'scoring':
            endpoint = '/meeting_service/admin/meeting_service/meeting/update_lead_scoring/';
            break;
        case 'complete':
            endpoint = '/meeting_service/admin/meeting_service/meeting/process_complete_outcome/';
            break;
        default:
            showNotification('Unknown outcome component type', 'error');
            button.innerHTML = originalText;
            button.disabled = false;
            return;
    }
    
    // Make AJAX request to process outcome component
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `meeting_id=${meetingId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message with details
            let message = 'Success: ';
            if (component === 'complete') {
                message += 'All meeting outcomes processed successfully';
                if (data.components) {
                    const successCount = Object.values(data.components).filter(c => c.success).length;
                    const totalCount = Object.keys(data.components).length;
                    message += ` (${successCount}/${totalCount} components completed)`;
                }
            } else {
                message += data.message || 'Component processed successfully';
            }
            
            showNotification(message, 'success');
            
            // Show additional details for specific components
            if (component === 'scoring' && data.score_changes) {
                const changes = Object.entries(data.score_changes)
                    .filter(([key, value]) => value !== 0)
                    .map(([key, value]) => `${key}: ${value > 0 ? '+' : ''}${value.toFixed(1)}`)
                    .join(', ');
                if (changes) {
                    showNotification(`Score changes: ${changes}`, 'info');
                }
            }
            
            // Reload page to show updated data
            setTimeout(() => location.reload(), 2000);
            
        } else {
            // Show error message
            const errorMessage = data.error || 'Unknown error occurred';
            showNotification(`Error: ${errorMessage}`, 'error');
            
            // Show component-specific errors for complete processing
            if (component === 'complete' && data.components) {
                const failedComponents = Object.entries(data.components)
                    .filter(([name, comp]) => !comp.success)
                    .map(([name, comp]) => `${name}: ${comp.error || 'Unknown error'}`);
                
                if (failedComponents.length > 0) {
                    showNotification(`Failed components: ${failedComponents.join('; ')}`, 'warning');
                }
            }
        }
        
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification(`Error processing ${component}: ${error.message}`, 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

// Enhanced notification function for outcome tracking
function showOutcomeNotification(title, message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `outcome-notification outcome-notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 20px;
        border-radius: 8px;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        z-index: 10000;
        max-width: 450px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        border-left: 4px solid rgba(255, 255, 255, 0.3);
    `;
    
    // Set background color based on type
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // Create notification content
    const titleElement = document.createElement('div');
    titleElement.style.cssText = 'font-weight: bold; font-size: 16px; margin-bottom: 8px;';
    titleElement.textContent = title;
    
    const messageElement = document.createElement('div');
    messageElement.style.cssText = 'font-size: 14px; line-height: 1.4;';
    messageElement.textContent = message;
    
    notification.appendChild(titleElement);
    notification.appendChild(messageElement);
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '×';
    closeButton.style.cssText = `
        position: absolute;
        top: 8px;
        right: 12px;
        background: none;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
        opacity: 0.7;
    `;
    closeButton.addEventListener('click', () => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    });
    notification.appendChild(closeButton);
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after specified duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, duration);
}

// Meeting outcome status checker
function checkMeetingOutcomeStatus(meetingId) {
    fetch(`/meeting_service/api/meetings/${meetingId}/outcomes/status/`)
    .then(response => response.json())
    .then(data => {
        if (data.overall_completion) {
            showOutcomeNotification(
                'Meeting Outcomes Complete',
                `All outcome components have been processed for this meeting (${data.completion_percentage}% complete).`,
                'success'
            );
        } else {
            const pendingComponents = Object.entries(data.components)
                .filter(([name, comp]) => !comp.completed)
                .map(([name, comp]) => name);
            
            showOutcomeNotification(
                'Pending Outcome Processing',
                `Some outcome components are pending: ${pendingComponents.join(', ')}`,
                'warning'
            );
        }
    })
    .catch(error => {
        console.error('Error checking outcome status:', error);
    });
}

// Auto-check outcome status for completed meetings
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a meeting detail page with a completed meeting
    const meetingIdElement = document.querySelector('[data-meeting-id]');
    const meetingStatusElement = document.querySelector('[data-meeting-status="completed"]');
    
    if (meetingIdElement && meetingStatusElement) {
        const meetingId = meetingIdElement.getAttribute('data-meeting-id');
        // Check outcome status after a short delay
        setTimeout(() => checkMeetingOutcomeStatus(meetingId), 1000);
    }
});