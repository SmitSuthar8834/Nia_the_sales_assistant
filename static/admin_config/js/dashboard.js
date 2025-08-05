// Dashboard specific JavaScript

$(document).ready(function() {
    loadDashboardData();
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

// Load dashboard data
function loadDashboardData() {
    AdminConfig.getDashboardData()
        .then(data => {
            updateStatistics(data.stats);
            updateHealthStatus(data.health_status);
            updateRecentActivity(data.recent_activity);
        })
        .catch(error => {
            console.error('Failed to load dashboard data:', error);
            AdminConfig.showAlert('Failed to load dashboard data', 'danger');
        });
}

// Update statistics cards
function updateStatistics(stats) {
    $('#totalIntegrations').text(stats.total_integrations || 0);
    $('#activeIntegrations').text(stats.active_integrations || 0);
    $('#totalWorkflows').text(stats.total_workflows || 0);
    $('#recentTests').text(stats.recent_tests || 0);
}

// Update health status
function updateHealthStatus(healthStatus) {
    const healthPercentage = Math.round(healthStatus.overall_health || 0);
    const healthyCount = healthStatus.healthy_configurations || 0;
    const unhealthyCount = healthStatus.unhealthy_configurations || 0;
    const totalCount = healthStatus.total_configurations || 0;
    
    // Update health badge and progress
    const healthBadge = $('#healthBadge');
    const healthProgress = $('#healthProgress');
    
    healthBadge.text(`${healthPercentage}%`);
    healthProgress.css('width', `${healthPercentage}%`);
    healthProgress.attr('aria-valuenow', healthPercentage);
    
    // Update badge color based on health
    healthBadge.removeClass('bg-success bg-warning bg-danger');
    healthProgress.removeClass('bg-success bg-warning bg-danger');
    
    if (healthPercentage >= 90) {
        healthBadge.addClass('bg-success');
        healthProgress.addClass('bg-success');
    } else if (healthPercentage >= 70) {
        healthBadge.addClass('bg-warning');
        healthProgress.addClass('bg-warning');
    } else {
        healthBadge.addClass('bg-danger');
        healthProgress.addClass('bg-danger');
    }
    
    // Update counts
    $('#healthyConfigs').text(healthyCount);
    $('#unhealthyConfigs').text(unhealthyCount);
    $('#totalConfigs').text(totalCount);
}

// Update recent activity table
function updateRecentActivity(activities) {
    const tbody = $('#recentActivityTable tbody');
    tbody.empty();
    
    if (!activities || activities.length === 0) {
        tbody.html(`
            <tr>
                <td colspan="5" class="text-center text-muted">
                    <i class="fas fa-info-circle me-2"></i>No recent activity
                </td>
            </tr>
        `);
        return;
    }
    
    activities.forEach(activity => {
        const row = `
            <tr>
                <td>${AdminConfig.formatRelativeTime(activity.timestamp)}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-user-circle me-2 text-muted"></i>
                        ${activity.user_name || activity.user}
                    </div>
                </td>
                <td>
                    <span class="badge bg-primary">${activity.action_display || activity.action}</span>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-${getResourceIcon(activity.content_type_name)} me-2 text-muted"></i>
                        ${activity.content_type_name || 'Unknown'}
                    </div>
                </td>
                <td>
                    ${activity.success ? 
                        '<i class="fas fa-check-circle text-success" title="Success"></i>' : 
                        '<i class="fas fa-times-circle text-danger" title="Failed"></i>'
                    }
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

// Get resource icon based on type
function getResourceIcon(resourceType) {
    const icons = {
        'integration configuration': 'plug',
        'workflow configuration': 'project-diagram',
        'configuration template': 'file-code',
        'configuration backup': 'database',
        'role permission': 'users-cog'
    };
    
    return icons[resourceType?.toLowerCase()] || 'cog';
}

// Refresh dashboard
function refreshDashboard() {
    AdminConfig.showLoading('Refreshing dashboard...');
    loadDashboardData();
    setTimeout(() => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Dashboard refreshed successfully', 'success', 3000);
    }, 1000);
}

// Create backup
function createBackup() {
    const backupName = `Dashboard Backup ${new Date().toISOString().slice(0, 19).replace('T', ' ')}`;
    
    AdminConfig.showLoading('Creating backup...');
    
    AdminConfig.apiRequest('/admin-config/api/backups/create_backup/', {
        method: 'POST',
        data: {
            name: backupName,
            description: 'Manual backup created from dashboard',
            backup_type: 'manual'
        }
    })
    .then(data => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Backup created successfully', 'success');
        loadDashboardData(); // Refresh stats
    })
    .catch(error => {
        AdminConfig.hideLoading();
        AdminConfig.showAlert('Failed to create backup: ' + error.message, 'danger');
    });
}

// Run health check
function runHealthCheck() {
    AdminConfig.showLoading('Running health check...');
    
    // Simulate health check (in real implementation, this would call an API)
    setTimeout(() => {
        AdminConfig.hideLoading();
        loadDashboardData(); // Refresh health status
        AdminConfig.showAlert('Health check completed', 'success');
    }, 2000);
}