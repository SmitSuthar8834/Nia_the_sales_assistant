// Main application initialization for NIA Sales Assistant

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the UI Manager
    window.uiManager = new UIManager();
    
    // Initialize application
    initializeApp();
});

async function initializeApp() {
    try {
        // Test API connection
        await testAPIConnection();
        
        // Load initial data
        await loadInitialData();
        
        console.log('NIA Sales Assistant initialized successfully');
    } catch (error) {
        console.error('Failed to initialize application:', error);
        showInitializationError(error);
    }
}

async function testAPIConnection() {
    try {
        await window.apiService.testConnection();
        console.log('API connection successful');
    } catch (error) {
        console.warn('API connection test failed:', error.message);
        // Don't throw error here as the app can still work with cached data
    }
}

async function loadInitialData() {
    // Load leads if we're on the leads view
    if (window.uiManager.currentView === 'leads') {
        await window.uiManager.loadLeads();
    }
}

function showInitializationError(error) {
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        alertContainer.innerHTML = `
            <div class="alert alert-error">
                <strong>Initialization Error:</strong> ${error.message}
                <br>
                <small>Some features may not work properly. Please refresh the page or contact support.</small>
            </div>
        `;
    }
}

// Global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Show user-friendly error message
    if (window.uiManager) {
        window.uiManager.showAlert(
            'An unexpected error occurred. Please try again or refresh the page.',
            'error'
        );
    }
    
    // Prevent the default browser error handling
    event.preventDefault();
});

// Global error handler for JavaScript errors
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    
    // Show user-friendly error message for critical errors
    if (window.uiManager && event.error && event.error.message) {
        window.uiManager.showAlert(
            'A technical error occurred. Please refresh the page.',
            'error'
        );
    }
});

// Utility functions for debugging and development
window.debugNIA = {
    // Get current application state
    getState: function() {
        return {
            currentView: window.uiManager?.currentView,
            currentLead: window.uiManager?.currentLead,
            analysisResults: window.uiManager?.analysisResults
        };
    },
    
    // Test API endpoints
    testAPI: async function() {
        const tests = [
            { name: 'Test Connection', fn: () => window.apiService.testConnection() },
            { name: 'Get Leads', fn: () => window.apiService.getLeads() },
            { name: 'Get Analytics', fn: () => window.apiService.getLeadAnalytics() },
            { name: 'Get Quota Status', fn: () => window.apiService.getQuotaStatus() }
        ];
        
        const results = {};
        
        for (const test of tests) {
            try {
                const result = await test.fn();
                results[test.name] = { success: true, data: result };
                console.log(`✅ ${test.name}:`, result);
            } catch (error) {
                results[test.name] = { success: false, error: error.message };
                console.error(`❌ ${test.name}:`, error.message);
            }
        }
        
        return results;
    },
    
    // Simulate lead creation for testing
    createTestLead: async function() {
        const testConversation = `
            I spoke with John Smith from Acme Corp today. They're a mid-size manufacturing company 
            with about 200 employees. John mentioned they're struggling with their current CRM system - 
            it's outdated and doesn't integrate well with their sales process. They're looking for a 
            modern solution that can handle lead tracking, opportunity management, and sales analytics. 
            Their budget is around $50,000 and they want to implement something within the next 3 months. 
            John is the VP of Sales and seems very interested. His email is john.smith@acmecorp.com 
            and phone is 555-123-4567.
        `;
        
        try {
            const analysis = await window.apiService.analyzeConversation(testConversation);
            console.log('Test analysis result:', analysis);
            return analysis;
        } catch (error) {
            console.error('Test lead creation failed:', error);
            throw error;
        }
    },
    
    // Clear all alerts
    clearAlerts: function() {
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            alertContainer.innerHTML = '';
        }
    }
};

// Performance monitoring
if (window.performance && window.performance.mark) {
    window.performance.mark('nia-app-start');
    
    window.addEventListener('load', function() {
        window.performance.mark('nia-app-loaded');
        window.performance.measure('nia-app-load-time', 'nia-app-start', 'nia-app-loaded');
        
        const loadTime = window.performance.getEntriesByName('nia-app-load-time')[0];
        if (loadTime) {
            console.log(`NIA app loaded in ${Math.round(loadTime.duration)}ms`);
        }
    });
}