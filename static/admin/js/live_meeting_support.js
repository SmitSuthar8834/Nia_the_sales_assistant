/**
 * Live Meeting Support JavaScript for Django Admin
 * 
 * Provides real-time meeting support functionality including:
 * - Starting live meeting sessions
 * - Processing conversation turns
 * - Displaying real-time suggestions
 * - Sentiment analysis
 * - Key moment identification
 */

// Global variables for live meeting session
let liveMeetingSession = null;
let liveMeetingModal = null;
let conversationHistory = [];
let isRecording = false;

/**
 * Start a live meeting session
 */
function startLiveMeetingSession(meetingId) {
    // Create modal for live meeting interface
    createLiveMeetingModal(meetingId);
    
    // Initialize the live meeting session
    fetch('/meeting_service/api/live/start-session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            meeting_id: meetingId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            liveMeetingSession = data;
            updateLiveMeetingInterface(data);
            showMessage('Live meeting session started successfully!', 'success');
        } else {
            showMessage('Failed to start live meeting session: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error starting live meeting session:', error);
        showMessage('Error starting live meeting session', 'error');
    });
}

/**
 * Create the live meeting modal interface
 */
function createLiveMeetingModal(meetingId) {
    // Remove existing modal if present
    if (liveMeetingModal) {
        liveMeetingModal.remove();
    }
    
    // Create modal HTML
    const modalHTML = `
        <div id="live-meeting-modal" class="live-meeting-modal">
            <div class="live-meeting-content">
                <div class="live-meeting-header">
                    <h3>🎤 Live Meeting Support</h3>
                    <button class="close-button" onclick="closeLiveMeetingModal()">&times;</button>
                </div>
                
                <div class="live-meeting-body">
                    <!-- Meeting Info -->
                    <div class="meeting-info-section">
                        <div id="meeting-info">
                            <p>Initializing live meeting session...</p>
                        </div>
                    </div>
                    
                    <!-- Conversation Input -->
                    <div class="conversation-section">
                        <h4>Conversation Input</h4>
                        <div class="conversation-controls">
                            <select id="speaker-select">
                                <option value="user">You (Sales Rep)</option>
                                <option value="prospect">Prospect</option>
                            </select>
                            <button id="record-button" onclick="toggleRecording()" class="record-btn">
                                🎤 Start Recording
                            </button>
                        </div>
                        
                        <textarea id="conversation-input" 
                                  placeholder="Enter conversation text or use voice recording..."
                                  rows="3"></textarea>
                        
                        <button onclick="processConversationTurn()" class="process-btn">
                            Process Turn
                        </button>
                    </div>
                    
                    <!-- Real-time Analysis -->
                    <div class="analysis-section">
                        <div class="analysis-tabs">
                            <button class="tab-button active" onclick="showTab('suggestions')">
                                💡 Suggestions
                            </button>
                            <button class="tab-button" onclick="showTab('guidance')">
                                🎯 AI Guidance
                            </button>
                            <button class="tab-button" onclick="showTab('sentiment')">
                                😊 Sentiment
                            </button>
                            <button class="tab-button" onclick="showTab('moments')">
                                ⭐ Key Moments
                            </button>
                            <button class="tab-button" onclick="showTab('history')">
                                📝 History
                            </button>
                        </div>
                        
                        <div id="suggestions-tab" class="tab-content active">
                            <h4>Next Question Suggestions</h4>
                            <div id="question-suggestions">
                                <p>No suggestions yet. Start the conversation to get AI-powered recommendations.</p>
                            </div>
                        </div>
                        
                        <div id="guidance-tab" class="tab-content">
                            <h4>AI Meeting Guidance</h4>
                            <div class="guidance-sections">
                                <div class="guidance-section">
                                    <h5>🛡️ Objection Handling</h5>
                                    <div id="objection-handling">
                                        <p>No objections detected yet.</p>
                                    </div>
                                </div>
                                <div class="guidance-section">
                                    <h5>🎯 Closing Opportunities</h5>
                                    <div id="closing-opportunities">
                                        <p>No closing opportunities identified yet.</p>
                                    </div>
                                </div>
                                <div class="guidance-section">
                                    <h5>📋 Follow-up Actions</h5>
                                    <div id="follow-up-recommendations">
                                        <p>No follow-up recommendations yet.</p>
                                    </div>
                                </div>
                                <div class="guidance-section">
                                    <h5>⚠️ Intervention Alerts</h5>
                                    <div id="intervention-alerts">
                                        <p>No intervention alerts.</p>
                                    </div>
                                </div>
                                <div class="meeting-health">
                                    <h5>📊 Meeting Health</h5>
                                    <div id="meeting-health-indicator">
                                        <span class="health-status unknown">Unknown</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div id="sentiment-tab" class="tab-content">
                            <h4>Sentiment Analysis</h4>
                            <div id="sentiment-analysis">
                                <p>No sentiment data yet.</p>
                            </div>
                        </div>
                        
                        <div id="moments-tab" class="tab-content">
                            <h4>Key Moments</h4>
                            <div id="key-moments">
                                <p>No key moments identified yet.</p>
                            </div>
                        </div>
                        
                        <div id="history-tab" class="tab-content">
                            <h4>Conversation History</h4>
                            <div id="conversation-history">
                                <p>No conversation history yet.</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="live-meeting-footer">
                    <button onclick="endLiveMeetingSession()" class="end-session-btn">
                        🛑 End Session
                    </button>
                    <button onclick="refreshSuggestions()" class="refresh-btn">
                        🔄 Refresh
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    liveMeetingModal = document.getElementById('live-meeting-modal');
    
    // Add CSS styles
    addLiveMeetingStyles();
}

/**
 * Update the live meeting interface with session data
 */
function updateLiveMeetingInterface(sessionData) {
    const meetingInfo = document.getElementById('meeting-info');
    if (meetingInfo && sessionData) {
        meetingInfo.innerHTML = `
            <div class="meeting-details">
                <h4>${sessionData.meeting_title}</h4>
                <p><strong>Company:</strong> ${sessionData.lead_company}</p>
                <p><strong>Session ID:</strong> ${sessionData.session_id}</p>
                <p><strong>Status:</strong> <span class="status-active">Active</span></p>
            </div>
        `;
        
        // Display initial questions if available
        if (sessionData.initial_questions && sessionData.initial_questions.length > 0) {
            displayQuestionSuggestions(sessionData.initial_questions);
        }
    }
}

/**
 * Process a conversation turn
 */
function processConversationTurn() {
    const speakerSelect = document.getElementById('speaker-select');
    const conversationInput = document.getElementById('conversation-input');
    
    const speaker = speakerSelect.value;
    const content = conversationInput.value.trim();
    
    if (!content) {
        showMessage('Please enter conversation content', 'warning');
        return;
    }
    
    if (!liveMeetingSession) {
        showMessage('No active live meeting session', 'error');
        return;
    }
    
    // Show processing indicator
    const processBtn = document.querySelector('.process-btn');
    const originalText = processBtn.textContent;
    processBtn.textContent = 'Processing...';
    processBtn.disabled = true;
    
    // Send conversation turn to backend
    fetch('/meeting_service/api/live/conversation-turn/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            session_id: liveMeetingSession.session_id,
            speaker: speaker,
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add to conversation history
            conversationHistory.push({
                speaker: speaker,
                content: content,
                timestamp: new Date().toISOString()
            });
            
            // Update interface with analysis results
            if (data.analysis_performed) {
                if (data.sentiment_analysis) {
                    updateSentimentDisplay(data.sentiment_analysis);
                }
                if (data.key_moments) {
                    updateKeyMomentsDisplay(data.key_moments);
                }
                if (data.question_suggestions) {
                    displayQuestionSuggestions(data.question_suggestions);
                }
                
                // Refresh AI guidance after analysis
                setTimeout(() => {
                    refreshMeetingGuidance();
                }, 1000);
            }
            
            // Update conversation history display
            updateConversationHistoryDisplay();
            
            // Clear input
            conversationInput.value = '';
            
            showMessage('Conversation turn processed successfully', 'success');
        } else {
            showMessage('Failed to process conversation turn: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error processing conversation turn:', error);
        showMessage('Error processing conversation turn', 'error');
    })
    .finally(() => {
        // Reset button
        processBtn.textContent = originalText;
        processBtn.disabled = false;
    });
}

/**
 * Display question suggestions
 */
function displayQuestionSuggestions(suggestions) {
    const suggestionsDiv = document.getElementById('question-suggestions');
    
    if (!suggestions || suggestions.length === 0) {
        suggestionsDiv.innerHTML = '<p>No suggestions available.</p>';
        return;
    }
    
    let html = '';
    suggestions.forEach((suggestion, index) => {
        const priority = suggestion.priority_score || suggestion.priority || 50;
        const priorityClass = priority >= 80 ? 'high-priority' : priority >= 60 ? 'medium-priority' : 'low-priority';
        
        html += `
            <div class="suggestion-item ${priorityClass}">
                <div class="suggestion-header">
                    <span class="question-type">${suggestion.question_type || 'General'}</span>
                    <span class="priority-score">${Math.round(priority)}/100</span>
                </div>
                <div class="question-text">
                    ${suggestion.question_text || suggestion.question}
                </div>
                <div class="suggestion-details">
                    <p><strong>Rationale:</strong> ${suggestion.rationale || 'N/A'}</p>
                    ${suggestion.timing_suggestion ? `<p><strong>Timing:</strong> ${suggestion.timing_suggestion}</p>` : ''}
                    ${suggestion.expected_outcome ? `<p><strong>Expected Outcome:</strong> ${suggestion.expected_outcome}</p>` : ''}
                </div>
                <button onclick="useQuestion('${suggestion.question_text || suggestion.question}')" class="use-question-btn">
                    Use This Question
                </button>
            </div>
        `;
    });
    
    suggestionsDiv.innerHTML = html;
}

/**
 * Update sentiment display
 */
function updateSentimentDisplay(sentimentData) {
    const sentimentDiv = document.getElementById('sentiment-analysis');
    
    const sentimentEmoji = {
        'positive': '😊',
        'neutral': '😐',
        'negative': '😟'
    };
    
    const engagementEmoji = {
        'high': '🔥',
        'medium': '👍',
        'low': '😴'
    };
    
    sentimentDiv.innerHTML = `
        <div class="sentiment-display">
            <div class="sentiment-item">
                <h5>Overall Sentiment</h5>
                <div class="sentiment-value">
                    ${sentimentEmoji[sentimentData.overall_sentiment] || '😐'} 
                    ${sentimentData.overall_sentiment || 'neutral'}
                    <span class="score">(${(sentimentData.sentiment_score * 100).toFixed(0)}%)</span>
                </div>
            </div>
            
            <div class="sentiment-item">
                <h5>Engagement Level</h5>
                <div class="engagement-value">
                    ${engagementEmoji[sentimentData.engagement_level] || '👍'} 
                    ${sentimentData.engagement_level || 'medium'}
                    <span class="score">(${Math.round(sentimentData.engagement_score || 50)}/100)</span>
                </div>
            </div>
            
            ${sentimentData.emotional_indicators && sentimentData.emotional_indicators.length > 0 ? `
                <div class="sentiment-item">
                    <h5>Emotional Indicators</h5>
                    <ul class="indicators-list">
                        ${sentimentData.emotional_indicators.map(indicator => `<li>${indicator}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div class="confidence-bar">
                <label>Analysis Confidence: ${Math.round(sentimentData.confidence_level || 50)}%</label>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${sentimentData.confidence_level || 50}%"></div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Update key moments display
 */
function updateKeyMomentsDisplay(keyMoments) {
    const momentsDiv = document.getElementById('key-moments');
    
    if (!keyMoments || keyMoments.length === 0) {
        momentsDiv.innerHTML = '<p>No key moments identified yet.</p>';
        return;
    }
    
    const momentIcons = {
        'buying_signal': '💰',
        'objection': '⚠️',
        'pain_point': '😣',
        'decision_maker': '👔',
        'budget_mention': '💵',
        'timeline_mention': '⏰',
        'competitive_mention': '🏆',
        'requirement_clarification': '📋'
    };
    
    let html = '';
    keyMoments.forEach(moment => {
        const importance = Math.round(moment.importance_score || 50);
        const importanceClass = importance >= 80 ? 'high-importance' : importance >= 60 ? 'medium-importance' : 'low-importance';
        
        html += `
            <div class="moment-item ${importanceClass}">
                <div class="moment-header">
                    <span class="moment-icon">${momentIcons[moment.moment_type] || '📌'}</span>
                    <span class="moment-type">${moment.moment_type.replace('_', ' ').toUpperCase()}</span>
                    <span class="importance-score">${importance}/100</span>
                </div>
                <div class="moment-description">
                    ${moment.description}
                </div>
                ${moment.context ? `
                    <div class="moment-context">
                        <strong>Context:</strong> "${moment.context}"
                    </div>
                ` : ''}
                ${moment.suggested_response ? `
                    <div class="suggested-response">
                        <strong>Suggested Response:</strong> ${moment.suggested_response}
                    </div>
                ` : ''}
                ${moment.follow_up_actions && moment.follow_up_actions.length > 0 ? `
                    <div class="follow-up-actions">
                        <strong>Follow-up Actions:</strong>
                        <ul>
                            ${moment.follow_up_actions.map(action => `<li>${action}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    momentsDiv.innerHTML = html;
}

/**
 * Update conversation history display
 */
function updateConversationHistoryDisplay() {
    const historyDiv = document.getElementById('conversation-history');
    
    if (conversationHistory.length === 0) {
        historyDiv.innerHTML = '<p>No conversation history yet.</p>';
        return;
    }
    
    let html = '';
    conversationHistory.forEach((turn, index) => {
        const speakerClass = turn.speaker === 'user' ? 'user-turn' : 'prospect-turn';
        const speakerLabel = turn.speaker === 'user' ? 'You' : 'Prospect';
        
        html += `
            <div class="conversation-turn ${speakerClass}">
                <div class="turn-header">
                    <span class="speaker">${speakerLabel}</span>
                    <span class="timestamp">${new Date(turn.timestamp).toLocaleTimeString()}</span>
                </div>
                <div class="turn-content">
                    ${turn.content}
                </div>
            </div>
        `;
    });
    
    historyDiv.innerHTML = html;
    
    // Scroll to bottom
    historyDiv.scrollTop = historyDiv.scrollHeight;
}

/**
 * Use a suggested question
 */
function useQuestion(questionText) {
    const conversationInput = document.getElementById('conversation-input');
    const speakerSelect = document.getElementById('speaker-select');
    
    conversationInput.value = questionText;
    speakerSelect.value = 'user';
    
    showMessage('Question added to input. Click "Process Turn" to use it.', 'info');
}

/**
 * Refresh suggestions and guidance
 */
function refreshSuggestions() {
    if (!liveMeetingSession) {
        showMessage('No active live meeting session', 'error');
        return;
    }
    
    // Refresh regular suggestions
    fetch(`/meeting_service/api/live/suggestions/?session_id=${liveMeetingSession.session_id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.suggestions) {
                displayQuestionSuggestions(data.suggestions);
            }
            if (data.sentiment) {
                updateSentimentDisplay(data.sentiment);
            }
            if (data.key_moments) {
                updateKeyMomentsDisplay(data.key_moments);
            }
        }
    })
    .catch(error => {
        console.error('Error refreshing suggestions:', error);
    });
    
    // Refresh AI guidance
    refreshMeetingGuidance();
}

/**
 * Refresh AI meeting guidance
 */
function refreshMeetingGuidance() {
    if (!liveMeetingSession) {
        return;
    }
    
    fetch(`/meeting_service/api/live/guidance/?session_id=${liveMeetingSession.session_id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateGuidanceDisplay(data);
            showMessage('AI guidance refreshed', 'success');
        } else {
            showMessage('Failed to refresh guidance: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error refreshing guidance:', error);
        showMessage('Error refreshing guidance', 'error');
    });
}

/**
 * Update AI guidance display
 */
function updateGuidanceDisplay(guidanceData) {
    // Update objection handling
    updateObjectionHandlingDisplay(guidanceData.objection_handling || []);
    
    // Update closing opportunities
    updateClosingOpportunitiesDisplay(guidanceData.closing_opportunities || []);
    
    // Update follow-up recommendations
    updateFollowUpRecommendationsDisplay(guidanceData.follow_up_recommendations || []);
    
    // Update intervention alerts
    updateInterventionAlertsDisplay(guidanceData.intervention_alerts || []);
    
    // Update meeting health
    updateMeetingHealthDisplay(guidanceData.overall_meeting_health || 'unknown');
}

/**
 * Update objection handling display
 */
function updateObjectionHandlingDisplay(objectionHandling) {
    const objectionDiv = document.getElementById('objection-handling');
    
    if (!objectionHandling || objectionHandling.length === 0) {
        objectionDiv.innerHTML = '<p>No objections detected yet.</p>';
        return;
    }
    
    let html = '';
    objectionHandling.forEach(objection => {
        const urgencyClass = objection.urgency_level === 'critical' ? 'critical-urgency' : 
                           objection.urgency_level === 'high' ? 'high-urgency' : 'medium-urgency';
        
        html += `
            <div class="objection-item ${urgencyClass}">
                <div class="objection-header">
                    <span class="objection-type">${objection.objection_type.toUpperCase()}</span>
                    <span class="urgency-level">${objection.urgency_level}</span>
                    <span class="confidence-score">${Math.round(objection.confidence_score)}%</span>
                </div>
                <div class="objection-text">
                    <strong>Objection:</strong> "${objection.objection_text}"
                </div>
                <div class="recommended-response">
                    <strong>Recommended Response:</strong>
                    <p>${objection.recommended_response}</p>
                </div>
                ${objection.alternative_approaches && objection.alternative_approaches.length > 0 ? `
                    <div class="alternative-approaches">
                        <strong>Alternative Approaches:</strong>
                        <ul>
                            ${objection.alternative_approaches.map(approach => `<li>${approach}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${objection.follow_up_questions && objection.follow_up_questions.length > 0 ? `
                    <div class="follow-up-questions">
                        <strong>Follow-up Questions:</strong>
                        <ul>
                            ${objection.follow_up_questions.map(question => `<li>${question}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                <button onclick="useObjectionResponse('${objection.recommended_response}')" class="use-response-btn">
                    Use This Response
                </button>
            </div>
        `;
    });
    
    objectionDiv.innerHTML = html;
}

/**
 * Update closing opportunities display
 */
function updateClosingOpportunitiesDisplay(closingOpportunities) {
    const closingDiv = document.getElementById('closing-opportunities');
    
    if (!closingOpportunities || closingOpportunities.length === 0) {
        closingDiv.innerHTML = '<p>No closing opportunities identified yet.</p>';
        return;
    }
    
    let html = '';
    closingOpportunities.forEach(opportunity => {
        const timingClass = opportunity.timing_recommendation === 'immediate' ? 'immediate-timing' : 
                          opportunity.timing_recommendation === 'within_5_minutes' ? 'urgent-timing' : 'later-timing';
        
        html += `
            <div class="closing-opportunity ${timingClass}">
                <div class="opportunity-header">
                    <span class="opportunity-type">${opportunity.opportunity_type.replace('_', ' ').toUpperCase()}</span>
                    <span class="confidence-score">${Math.round(opportunity.confidence_score)}%</span>
                    <span class="timing">${opportunity.timing_recommendation.replace('_', ' ')}</span>
                </div>
                <div class="opportunity-description">
                    ${opportunity.description}
                </div>
                <div class="closing-technique">
                    <strong>Recommended Technique:</strong> ${opportunity.recommended_closing_technique}
                </div>
                ${opportunity.closing_questions && opportunity.closing_questions.length > 0 ? `
                    <div class="closing-questions">
                        <strong>Closing Questions:</strong>
                        <ul>
                            ${opportunity.closing_questions.map(question => `<li>${question}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${opportunity.risk_factors && opportunity.risk_factors.length > 0 ? `
                    <div class="risk-factors">
                        <strong>Risk Factors:</strong>
                        <ul>
                            ${opportunity.risk_factors.map(risk => `<li>${risk}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                <button onclick="useClosingQuestion('${opportunity.closing_questions ? opportunity.closing_questions[0] : ''}')" class="use-closing-btn">
                    Use Closing Question
                </button>
            </div>
        `;
    });
    
    closingDiv.innerHTML = html;
}

/**
 * Update follow-up recommendations display
 */
function updateFollowUpRecommendationsDisplay(followUpRecommendations) {
    const followUpDiv = document.getElementById('follow-up-recommendations');
    
    if (!followUpRecommendations || followUpRecommendations.length === 0) {
        followUpDiv.innerHTML = '<p>No follow-up recommendations yet.</p>';
        return;
    }
    
    let html = '';
    followUpRecommendations.forEach(recommendation => {
        const priorityClass = recommendation.priority === 'high' ? 'high-priority' : 
                            recommendation.priority === 'medium' ? 'medium-priority' : 'low-priority';
        
        html += `
            <div class="follow-up-item ${priorityClass}">
                <div class="follow-up-header">
                    <span class="action-type">${recommendation.action_type.toUpperCase()}</span>
                    <span class="priority">${recommendation.priority} priority</span>
                    <span class="timing">${recommendation.recommended_timing.replace('_', ' ')}</span>
                </div>
                <div class="action-description">
                    ${recommendation.action_description}
                </div>
                <div class="rationale">
                    <strong>Rationale:</strong> ${recommendation.rationale}
                </div>
                <div class="success-probability">
                    <strong>Success Probability:</strong> ${Math.round(recommendation.success_probability)}%
                </div>
                ${recommendation.required_resources && recommendation.required_resources.length > 0 ? `
                    <div class="required-resources">
                        <strong>Required Resources:</strong>
                        <ul>
                            ${recommendation.required_resources.map(resource => `<li>${resource}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    followUpDiv.innerHTML = html;
}

/**
 * Update intervention alerts display
 */
function updateInterventionAlertsDisplay(interventionAlerts) {
    const alertsDiv = document.getElementById('intervention-alerts');
    
    if (!interventionAlerts || interventionAlerts.length === 0) {
        alertsDiv.innerHTML = '<p>No intervention alerts.</p>';
        return;
    }
    
    let html = '';
    interventionAlerts.forEach(alert => {
        const severityClass = alert.severity === 'critical' ? 'critical-alert' : 
                            alert.severity === 'high' ? 'high-alert' : 
                            alert.severity === 'medium' ? 'medium-alert' : 'low-alert';
        
        html += `
            <div class="intervention-alert ${severityClass}">
                <div class="alert-header">
                    <span class="alert-type">${alert.alert_type.replace('_', ' ').toUpperCase()}</span>
                    <span class="severity">${alert.severity.toUpperCase()}</span>
                    <span class="confidence">${Math.round(alert.confidence_score)}%</span>
                </div>
                <div class="alert-description">
                    ${alert.description}
                </div>
                <div class="recommended-intervention">
                    <strong>Recommended Intervention:</strong>
                    <p>${alert.recommended_intervention}</p>
                </div>
                ${alert.immediate_actions && alert.immediate_actions.length > 0 ? `
                    <div class="immediate-actions">
                        <strong>Immediate Actions:</strong>
                        <ul>
                            ${alert.immediate_actions.map(action => `<li>${action}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    alertsDiv.innerHTML = html;
}

/**
 * Update meeting health display
 */
function updateMeetingHealthDisplay(meetingHealth) {
    const healthDiv = document.getElementById('meeting-health-indicator');
    
    const healthEmojis = {
        'excellent': '🟢',
        'good': '🟡',
        'concerning': '🟠',
        'critical': '🔴',
        'unknown': '⚪'
    };
    
    const healthClass = meetingHealth.toLowerCase();
    
    healthDiv.innerHTML = `
        <span class="health-status ${healthClass}">
            ${healthEmojis[meetingHealth] || '⚪'} ${meetingHealth.toUpperCase()}
        </span>
    `;
}

/**
 * Use objection response
 */
function useObjectionResponse(response) {
    const conversationInput = document.getElementById('conversation-input');
    const speakerSelect = document.getElementById('speaker-select');
    
    conversationInput.value = response;
    speakerSelect.value = 'user';
    
    showMessage('Objection response added to input. Click "Process Turn" to use it.', 'info');
}

/**
 * Use closing question
 */
function useClosingQuestion(question) {
    if (!question) return;
    
    const conversationInput = document.getElementById('conversation-input');
    const speakerSelect = document.getElementById('speaker-select');
    
    conversationInput.value = question;
    speakerSelect.value = 'user';
    
    showMessage('Closing question added to input. Click "Process Turn" to use it.', 'info');
}

/**
 * End live meeting session
 */
function endLiveMeetingSession() {
    if (!liveMeetingSession) {
        showMessage('No active live meeting session', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to end the live meeting session? This will generate a final summary.')) {
        return;
    }
    
    fetch('/meeting_service/api/live/end-session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            session_id: liveMeetingSession.session_id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Live meeting session ended successfully. Final summary generated.', 'success');
            closeLiveMeetingModal();
            
            // Refresh the page to show updated meeting data
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            showMessage('Failed to end live meeting session: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error ending live meeting session:', error);
        showMessage('Error ending live meeting session', 'error');
    });
}

/**
 * Close the live meeting modal
 */
function closeLiveMeetingModal() {
    if (liveMeetingModal) {
        liveMeetingModal.remove();
        liveMeetingModal = null;
        liveMeetingSession = null;
        conversationHistory = [];
    }
}

/**
 * Show/hide tabs
 */
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

/**
 * Toggle recording (placeholder for future voice integration)
 */
function toggleRecording() {
    const recordButton = document.getElementById('record-button');
    
    if (!isRecording) {
        isRecording = true;
        recordButton.textContent = '🛑 Stop Recording';
        recordButton.classList.add('recording');
        showMessage('Voice recording not yet implemented. Please type your conversation.', 'info');
    } else {
        isRecording = false;
        recordButton.textContent = '🎤 Start Recording';
        recordButton.classList.remove('recording');
    }
}

/**
 * Add CSS styles for live meeting interface
 */
function addLiveMeetingStyles() {
    if (document.getElementById('live-meeting-styles')) {
        return; // Styles already added
    }
    
    const styles = `
        <style id="live-meeting-styles">
            .live-meeting-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .live-meeting-content {
                background: white;
                border-radius: 8px;
                width: 90%;
                max-width: 1200px;
                height: 90%;
                max-height: 800px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .live-meeting-header {
                background: #007cba;
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .close-button {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .live-meeting-body {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            .meeting-info-section {
                grid-column: 1 / -1;
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 10px;
            }
            
            .conversation-section {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
            }
            
            .conversation-controls {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
                align-items: center;
            }
            
            .record-btn {
                background: #28a745;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .record-btn.recording {
                background: #dc3545;
                animation: pulse 1s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .process-btn {
                background: #007cba;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 10px;
            }
            
            .analysis-section {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
            }
            
            .analysis-tabs {
                display: flex;
                gap: 5px;
                margin-bottom: 15px;
            }
            
            .tab-button {
                background: #e9ecef;
                border: none;
                padding: 8px 12px;
                border-radius: 4px 4px 0 0;
                cursor: pointer;
                font-size: 12px;
            }
            
            .tab-button.active {
                background: white;
                border-bottom: 2px solid #007cba;
            }
            
            .tab-content {
                display: none;
                background: white;
                padding: 15px;
                border-radius: 0 5px 5px 5px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .suggestion-item {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            
            .suggestion-item.high-priority {
                border-left: 4px solid #dc3545;
            }
            
            .suggestion-item.medium-priority {
                border-left: 4px solid #ffc107;
            }
            
            .suggestion-item.low-priority {
                border-left: 4px solid #28a745;
            }
            
            .suggestion-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
                font-size: 12px;
            }
            
            .question-type {
                background: #007cba;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                text-transform: uppercase;
            }
            
            .priority-score {
                font-weight: bold;
            }
            
            .question-text {
                font-weight: bold;
                margin-bottom: 8px;
            }
            
            .suggestion-details {
                font-size: 12px;
                color: #666;
                margin-bottom: 8px;
            }
            
            .use-question-btn {
                background: #28a745;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                cursor: pointer;
                font-size: 11px;
            }
            
            .sentiment-display {
                display: grid;
                gap: 15px;
            }
            
            .sentiment-item h5 {
                margin: 0 0 5px 0;
                color: #333;
            }
            
            .sentiment-value, .engagement-value {
                font-size: 16px;
                font-weight: bold;
            }
            
            .score {
                font-size: 12px;
                color: #666;
                font-weight: normal;
            }
            
            .indicators-list {
                margin: 5px 0;
                padding-left: 20px;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
                overflow: hidden;
                margin-top: 5px;
            }
            
            .progress-fill {
                height: 100%;
                background: #007cba;
                transition: width 0.3s ease;
            }
            
            .guidance-sections {
                display: grid;
                gap: 15px;
            }
            
            .guidance-section {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
            
            .guidance-section h5 {
                margin: 0 0 10px 0;
                color: #007cba;
                border-bottom: 1px solid #e9ecef;
                padding-bottom: 5px;
            }
            
            .objection-item, .closing-opportunity, .follow-up-item, .intervention-alert {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            
            .objection-item.critical-urgency {
                border-left: 4px solid #dc3545;
                background: #fff5f5;
            }
            
            .objection-item.high-urgency {
                border-left: 4px solid #fd7e14;
                background: #fff8f0;
            }
            
            .objection-item.medium-urgency {
                border-left: 4px solid #ffc107;
                background: #fffbf0;
            }
            
            .closing-opportunity.immediate-timing {
                border-left: 4px solid #28a745;
                background: #f8fff9;
            }
            
            .closing-opportunity.urgent-timing {
                border-left: 4px solid #ffc107;
                background: #fffbf0;
            }
            
            .closing-opportunity.later-timing {
                border-left: 4px solid #6c757d;
                background: #f8f9fa;
            }
            
            .follow-up-item.high-priority {
                border-left: 4px solid #dc3545;
            }
            
            .follow-up-item.medium-priority {
                border-left: 4px solid #ffc107;
            }
            
            .follow-up-item.low-priority {
                border-left: 4px solid #28a745;
            }
            
            .intervention-alert.critical-alert {
                border-left: 4px solid #dc3545;
                background: #fff5f5;
            }
            
            .intervention-alert.high-alert {
                border-left: 4px solid #fd7e14;
                background: #fff8f0;
            }
            
            .intervention-alert.medium-alert {
                border-left: 4px solid #ffc107;
                background: #fffbf0;
            }
            
            .intervention-alert.low-alert {
                border-left: 4px solid #17a2b8;
                background: #f0f9ff;
            }
            
            .objection-header, .opportunity-header, .follow-up-header, .alert-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 12px;
            }
            
            .objection-type, .opportunity-type, .action-type, .alert-type {
                background: #007cba;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-weight: bold;
            }
            
            .urgency-level, .priority, .severity {
                background: #6c757d;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 11px;
            }
            
            .confidence-score, .timing {
                font-weight: bold;
                color: #495057;
            }
            
            .use-response-btn, .use-closing-btn {
                background: #28a745;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                cursor: pointer;
                font-size: 11px;
                margin-top: 8px;
            }
            
            .meeting-health {
                text-align: center;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }
            
            .health-status {
                font-size: 16px;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 15px;
                display: inline-block;
            }
            
            .health-status.excellent {
                background: #d4edda;
                color: #155724;
            }
            
            .health-status.good {
                background: #fff3cd;
                color: #856404;
            }
            
            .health-status.concerning {
                background: #f8d7da;
                color: #721c24;
            }
            
            .health-status.critical {
                background: #f5c6cb;
                color: #721c24;
            }
            
            .health-status.unknown {
                background: #e2e3e5;
                color: #383d41;
            }
            
            .moment-item {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            
            .moment-item.high-importance {
                border-left: 4px solid #dc3545;
            }
            
            .moment-item.medium-importance {
                border-left: 4px solid #ffc107;
            }
            
            .moment-item.low-importance {
                border-left: 4px solid #28a745;
            }
            
            .moment-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            
            .moment-icon {
                font-size: 16px;
            }
            
            .moment-type {
                font-weight: bold;
                font-size: 12px;
                color: #007cba;
            }
            
            .importance-score {
                margin-left: auto;
                font-size: 12px;
                font-weight: bold;
            }
            
            .moment-description {
                margin-bottom: 8px;
            }
            
            .moment-context, .suggested-response, .follow-up-actions {
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }
            
            .conversation-turn {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
                margin-bottom: 8px;
            }
            
            .conversation-turn.user-turn {
                border-left: 4px solid #007cba;
            }
            
            .conversation-turn.prospect-turn {
                border-left: 4px solid #28a745;
            }
            
            .turn-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .turn-content {
                font-size: 14px;
            }
            
            .live-meeting-footer {
                background: #f8f9fa;
                padding: 15px 20px;
                display: flex;
                gap: 10px;
                justify-content: flex-end;
                border-top: 1px solid #dee2e6;
            }
            
            .end-session-btn {
                background: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .refresh-btn {
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .status-active {
                color: #28a745;
                font-weight: bold;
            }
            
            #conversation-input {
                width: 100%;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-family: inherit;
                resize: vertical;
            }
            
            #speaker-select {
                padding: 6px 10px;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
        </style>
    `;
    
    document.head.insertAdjacentHTML('beforeend', styles);
}

/**
 * Utility function to get CSRF token
 */
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

/**
 * Show message to user
 */
function showMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `admin-message admin-message-${type}`;
    messageDiv.textContent = message;
    
    // Style the message
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-weight: bold;
        z-index: 10001;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    // Set background color based on type
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    messageDiv.style.backgroundColor = colors[type] || colors.info;
    
    // Add to page
    document.body.appendChild(messageDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Live Meeting Support JavaScript loaded');
});