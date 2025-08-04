/**
 * Smart Chat Interface with Voice Fallback
 * Handles real-time chat, voice transitions, file sharing, and bot commands
 */

class ChatManager {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.typingTimeout = null;
        this.messageQueue = [];
        this.availableForVoice = false;
        this.botCommands = [];
        
        this.initializeEventListeners();
        this.loadBotCommands();
    }
    
    /**
     * Initialize event listeners for chat interface
     */
    initializeEventListeners() {
        // Chat input handling
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => this.handleChatInput(e));
            chatInput.addEventListener('input', () => this.handleTyping());
        }
        
        // Send button
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        // Voice transition button
        const voiceButton = document.getElementById('voice-transition-btn');
        if (voiceButton) {
            voiceButton.addEventListener('click', () => this.requestVoiceTransition());
        }
        
        // File upload
        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }
        
        // Availability toggle
        const availabilityToggle = document.getElementById('availability-toggle');
        if (availabilityToggle) {
            availabilityToggle.addEventListener('change', (e) => this.updateAvailability(e.target.checked));
        }
        
        // Search functionality
        const searchInput = document.getElementById('chat-search');
        if (searchInput) {
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.searchChatHistory(e.target.value);
                }
            });
        }
    }
    
    /**
     * Create a new chat session
     */
    async createChatSession(initialMessage = '') {
        try {
            const response = await fetch('/voice_service/chat/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    priority: 'medium',
                    initial_message: initialMessage
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            // Connect to WebSocket
            await this.connectWebSocket();
            
            this.showAlert('Chat session created successfully', 'success');
            return data;
            
        } catch (error) {
            console.error('Error creating chat session:', error);
            this.showAlert('Failed to create chat session', 'error');
            throw error;
        }
    }
    
    /**
     * Connect to WebSocket for real-time chat
     */
    async connectWebSocket() {
        if (!this.sessionId) {
            throw new Error('No session ID available');
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.sessionId}/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = (event) => {
            console.log('Chat WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            
            // Send queued messages
            this.processMessageQueue();
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.socket.onclose = (event) => {
            console.log('Chat WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            // Attempt to reconnect after delay
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connectWebSocket();
                }
            }, 5000);
        };
        
        this.socket.onerror = (error) => {
            console.error('Chat WebSocket error:', error);
            this.showAlert('Connection error occurred', 'error');
        };
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'connection_established':
                this.handleConnectionEstablished(data);
                break;
            case 'chat_message':
                this.displayMessage(data.message);
                break;
            case 'typing_indicator':
                this.handleTypingIndicator(data);
                break;
            case 'read_receipt':
                this.handleReadReceipt(data);
                break;
            case 'voice_transition_ready':
                this.handleVoiceTransitionReady(data);
                break;
            case 'voice_transition_notification':
                this.handleVoiceTransitionNotification(data);
                break;
            case 'availability_update':
                this.handleAvailabilityUpdate(data);
                break;
            case 'bot_commands':
                this.botCommands = data.commands;
                this.updateCommandSuggestions();
                break;
            case 'message_history':
                this.displayMessageHistory(data.messages);
                break;
            case 'search_results':
                this.displaySearchResults(data);
                break;
            case 'error':
                this.showAlert(data.message, 'error');
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    /**
     * Handle connection established
     */
    handleConnectionEstablished(data) {
        console.log('Chat connection established:', data);
        this.availableForVoice = data.voice_available;
        this.updateAvailabilityUI();
    }
    
    /**
     * Send a chat message
     */
    sendMessage(content = null) {
        const chatInput = document.getElementById('chat-input');
        const messageContent = content || (chatInput ? chatInput.value.trim() : '');
        
        if (!messageContent) return;
        
        const message = {
            type: 'chat_message',
            content: messageContent,
            message_type: 'text',
            timestamp: new Date().toISOString()
        };
        
        if (this.isConnected) {
            this.socket.send(JSON.stringify(message));
            if (chatInput) chatInput.value = '';
        } else {
            this.messageQueue.push(message);
            this.showAlert('Message queued - reconnecting...', 'warning');
        }
    }
    
    /**
     * Handle chat input keydown events
     */
    handleChatInput(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        } else if (event.key === '/' && event.target.value === '') {
            // Show command suggestions
            this.showCommandSuggestions();
        }
    }
    
    /**
     * Handle typing indicators
     */
    handleTyping() {
        if (!this.isConnected) return;
        
        // Send typing start
        this.socket.send(JSON.stringify({
            type: 'typing_start'
        }));
        
        // Clear existing timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        
        // Set timeout to stop typing
        this.typingTimeout = setTimeout(() => {
            if (this.isConnected) {
                this.socket.send(JSON.stringify({
                    type: 'typing_stop'
                }));
            }
        }, 2000);
    }
    
    /**
     * Handle typing indicator from other users
     */
    handleTypingIndicator(data) {
        const typingIndicator = document.getElementById('typing-indicator');
        if (!typingIndicator) return;
        
        if (data.typing) {
            typingIndicator.textContent = `${data.username} is typing...`;
            typingIndicator.style.display = 'block';
        } else {
            typingIndicator.style.display = 'none';
        }
    }
    
    /**
     * Display a chat message in the UI
     */
    displayMessage(message) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;
        
        const messageElement = this.createMessageElement(message);
        messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Mark message as read if it's from NIA
        if (message.sender === 'nia') {
            this.markMessageAsRead(message.id);
        }
        
        // Play notification sound for incoming messages
        if (message.sender === 'nia') {
            this.playNotificationSound();
        }
    }
    
    /**
     * Create a message element for display
     */
    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${message.sender}`;
        messageDiv.dataset.messageId = message.id;
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        
        let attachmentsHtml = '';
        if (message.attachments && message.attachments.length > 0) {
            attachmentsHtml = message.attachments.map(attachment => 
                `<div class="message-attachment">
                    <span class="attachment-icon">📎</span>
                    <span class="attachment-name">${attachment.filename || 'File'}</span>
                </div>`
            ).join('');
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-sender">${message.sender === 'user' ? 'You' : 'NIA'}</span>
                <span class="message-time">${timestamp}</span>
                <span class="message-status" data-status="${message.status}">
                    ${this.getStatusIcon(message.status)}
                </span>
            </div>
            <div class="message-content">
                ${this.formatMessageContent(message.content)}
                ${attachmentsHtml}
            </div>
        `;
        
        return messageDiv;
    }
    
    /**
     * Format message content (handle bot commands, links, etc.)
     */
    formatMessageContent(content) {
        // Handle bot commands
        if (content.startsWith('/')) {
            return `<code class="bot-command">${content}</code>`;
        }
        
        // Handle URLs
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        content = content.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        
        // Handle line breaks
        return content.replace(/\n/g, '<br>');
    }
    
    /**
     * Get status icon for message
     */
    getStatusIcon(status) {
        switch (status) {
            case 'sent': return '✓';
            case 'delivered': return '✓✓';
            case 'read': return '✓✓';
            case 'failed': return '❌';
            default: return '';
        }
    }
    
    /**
     * Display message history
     */
    displayMessageHistory(messages) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;
        
        messagesContainer.innerHTML = '';
        
        messages.forEach(message => {
            this.displayMessage(message);
        });
    }
    
    /**
     * Mark message as read
     */
    markMessageAsRead(messageId) {
        if (!this.isConnected) return;
        
        this.socket.send(JSON.stringify({
            type: 'mark_read',
            message_ids: [messageId]
        }));
    }
    
    /**
     * Handle read receipts
     */
    handleReadReceipt(data) {
        data.message_ids.forEach(messageId => {
            const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
            if (messageElement) {
                const statusElement = messageElement.querySelector('.message-status');
                if (statusElement) {
                    statusElement.dataset.status = 'read';
                    statusElement.textContent = '✓✓';
                }
            }
        });
    }
    
    /**
     * Request voice transition
     */
    requestVoiceTransition() {
        if (!this.isConnected) {
            this.showAlert('Not connected to chat', 'error');
            return;
        }
        
        this.socket.send(JSON.stringify({
            type: 'request_voice_transition',
            reason: 'user_request'
        }));
        
        this.showAlert('Preparing voice call...', 'info');
    }
    
    /**
     * Handle voice transition ready
     */
    handleVoiceTransitionReady(data) {
        const voiceModal = document.getElementById('voice-transition-modal');
        if (voiceModal) {
            voiceModal.style.display = 'block';
            
            const joinButton = document.getElementById('join-voice-call');
            if (joinButton) {
                joinButton.onclick = () => {
                    window.open(data.webrtc_url, '_blank');
                    voiceModal.style.display = 'none';
                };
            }
        }
        
        this.showAlert(data.message, 'success');
    }
    
    /**
     * Handle voice transition notification
     */
    handleVoiceTransitionNotification(data) {
        this.showAlert('Voice call is being prepared...', 'info');
    }
    
    /**
     * Update availability for voice calls
     */
    updateAvailability(available) {
        this.availableForVoice = available;
        
        if (this.isConnected) {
            this.socket.send(JSON.stringify({
                type: 'update_availability',
                available_for_voice: available
            }));
        }
        
        this.updateAvailabilityUI();
    }
    
    /**
     * Update availability UI
     */
    updateAvailabilityUI() {
        const toggle = document.getElementById('availability-toggle');
        const status = document.getElementById('availability-status');
        
        if (toggle) {
            toggle.checked = this.availableForVoice;
        }
        
        if (status) {
            status.textContent = this.availableForVoice ? 'Available for voice calls' : 'Chat only';
            status.className = `availability-status ${this.availableForVoice ? 'available' : 'unavailable'}`;
        }
    }
    
    /**
     * Handle availability update from server
     */
    handleAvailabilityUpdate(data) {
        // This would handle updates from other users in group chats
        console.log('Availability update:', data);
    }
    
    /**
     * Handle file upload
     */
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Check file size (limit to 10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showAlert('File size must be less than 10MB', 'error');
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`/voice_service/chat/session/${this.sessionId}/upload/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.showAlert('File uploaded successfully', 'success');
            
            // Clear file input
            event.target.value = '';
            
        } catch (error) {
            console.error('Error uploading file:', error);
            this.showAlert('Failed to upload file', 'error');
        }
    }
    
    /**
     * Load available bot commands
     */
    async loadBotCommands() {
        try {
            const response = await fetch('/voice_service/chat/commands/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.botCommands = data.commands;
            this.updateCommandSuggestions();
            
        } catch (error) {
            console.error('Error loading bot commands:', error);
        }
    }
    
    /**
     * Show command suggestions
     */
    showCommandSuggestions() {
        const suggestionsContainer = document.getElementById('command-suggestions');
        if (!suggestionsContainer) return;
        
        suggestionsContainer.innerHTML = '';
        
        this.botCommands.forEach(command => {
            const suggestionElement = document.createElement('div');
            suggestionElement.className = 'command-suggestion';
            suggestionElement.innerHTML = `
                <div class="command-name">${command.command}</div>
                <div class="command-description">${command.description}</div>
                <div class="command-usage">${command.usage}</div>
            `;
            
            suggestionElement.addEventListener('click', () => {
                const chatInput = document.getElementById('chat-input');
                if (chatInput) {
                    chatInput.value = command.command + ' ';
                    chatInput.focus();
                }
                suggestionsContainer.style.display = 'none';
            });
            
            suggestionsContainer.appendChild(suggestionElement);
        });
        
        suggestionsContainer.style.display = 'block';
    }
    
    /**
     * Update command suggestions based on input
     */
    updateCommandSuggestions() {
        // This would be called when the user types to filter suggestions
        console.log('Bot commands loaded:', this.botCommands.length);
    }
    
    /**
     * Search chat history
     */
    async searchChatHistory(query) {
        if (!query.trim()) return;
        
        try {
            const response = await fetch(`/voice_service/chat/search/?query=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.displaySearchResults(data);
            
        } catch (error) {
            console.error('Error searching chat history:', error);
            this.showAlert('Failed to search chat history', 'error');
        }
    }
    
    /**
     * Display search results
     */
    displaySearchResults(data) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = '';
        
        if (data.results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }
        
        data.results.forEach(result => {
            const resultElement = document.createElement('div');
            resultElement.className = 'search-result';
            resultElement.innerHTML = `
                <div class="result-header">
                    <span class="result-sender">${result.sender}</span>
                    <span class="result-time">${new Date(result.timestamp).toLocaleString()}</span>
                </div>
                <div class="result-content">${this.highlightSearchTerm(result.content, data.query)}</div>
            `;
            
            resultElement.addEventListener('click', () => {
                // Navigate to the session containing this message
                this.loadChatSession(result.session_id);
            });
            
            resultsContainer.appendChild(resultElement);
        });
        
        resultsContainer.style.display = 'block';
    }
    
    /**
     * Highlight search terms in content
     */
    highlightSearchTerm(content, term) {
        const regex = new RegExp(`(${term})`, 'gi');
        return content.replace(regex, '<mark>$1</mark>');
    }
    
    /**
     * Load existing chat session
     */
    async loadChatSession(sessionId) {
        try {
            const response = await fetch(`/voice_service/chat/session/${sessionId}/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.sessionId = sessionId;
            
            // Connect to WebSocket for this session
            await this.connectWebSocket();
            
            // Display message history
            this.displayMessageHistory(data.messages);
            
            this.showAlert('Chat session loaded', 'success');
            
        } catch (error) {
            console.error('Error loading chat session:', error);
            this.showAlert('Failed to load chat session', 'error');
        }
    }
    
    /**
     * Process queued messages when connection is restored
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.socket.send(JSON.stringify(message));
        }
    }
    
    /**
     * Update connection status UI
     */
    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            statusIndicator.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }
    
    /**
     * Play notification sound
     */
    playNotificationSound() {
        // Create and play a subtle notification sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    }
    
    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) return;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type}`;
        alertElement.innerHTML = `
            <span>${message}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        alertContainer.appendChild(alertElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertElement.parentElement) {
                alertElement.remove();
            }
        }, 5000);
    }
    
    /**
     * Get CSRF token for API requests
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
    
    /**
     * End current chat session
     */
    async endChatSession() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/voice_service/chat/session/${this.sessionId}/end/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Close WebSocket connection
            if (this.socket) {
                this.socket.close();
            }
            
            this.sessionId = null;
            this.isConnected = false;
            
            this.showAlert('Chat session ended', 'success');
            
        } catch (error) {
            console.error('Error ending chat session:', error);
            this.showAlert('Failed to end chat session', 'error');
        }
    }
}

// Initialize chat manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatManager = new ChatManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatManager;
}