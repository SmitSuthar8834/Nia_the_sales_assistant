// Lead-specific meeting action handlers for admin interface

function scheduleMeeting(leadId) {
    // Create a modal dialog for meeting scheduling
    const modal = createMeetingModal(leadId);
    document.body.appendChild(modal);
    
    // Show the modal
    modal.style.display = 'block';
    
    // Populate form with lead data
    populateMeetingForm(leadId);
}

function createMeetingModal(leadId) {
    const modal = document.createElement('div');
    modal.className = 'meeting-modal';
    modal.style.cssText = `
        display: none;
        position: fixed;
        z-index: 10000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
    `;
    
    modal.innerHTML = `
        <div class="meeting-modal-content" style="
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: none;
            border-radius: 8px;
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #dee2e6; padding-bottom: 15px;">
                <h2 style="margin: 0; color: #007cba;">📅 Schedule New Meeting</h2>
                <span class="close-modal" style="
                    color: #aaa;
                    float: right;
                    font-size: 28px;
                    font-weight: bold;
                    cursor: pointer;
                    line-height: 1;
                ">&times;</span>
            </div>
            
            <form id="meeting-form" style="display: grid; gap: 15px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <label for="meeting-title" style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">Meeting Title *</label>
                        <input type="text" id="meeting-title" name="title" required style="
                            width: 100%;
                            padding: 8px 12px;
                            border: 1px solid #ced4da;
                            border-radius: 4px;
                            font-size: 14px;
                            box-sizing: border-box;
                        ">
                    </div>
                    
                    <div>
                        <label for="meeting-type" style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">Meeting Type *</label>
                        <select id="meeting-type" name="meeting_type" required style="
                            width: 100%;
                            padding: 8px 12px;
                            border: 1px solid #ced4da;
                            border-radius: 4px;
                            font-size: 14px;
                            box-sizing: border-box;
                        ">
                            <option value="discovery">Discovery Call</option>
                            <option value="demo">Product Demo</option>
                            <option value="proposal">Proposal Presentation</option>
                            <option value="negotiation">Negotiation</option>
                            <option value="closing">Closing Call</option>
                            <option value="follow_up">Follow-up</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <label for="meeting-date" style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">Date *</label>
                        <input type="date" id="meeting-date" name="date" required style="
                            width: 100%;
                            padding: 8px 12px;
                            border: 1px solid #ced4da;
                            border-radius: 4px;
                            font-size: 14px;
                            box-sizing: border-box;
                        ">
                    </div>
                    
                    <div>
                        <label for="meeting-time" style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">Time *</label>
                        <input type="time" id="meeting-time" name="time" required style="
                            width: 100%;
                            padding: 8px 12px;
                            border: 1px solid #ced4da;
                            border-radius: 4px;
                            font-size: 14px;
                            box-sizing: border-box;
                        ">
                    </div>
                </div>
                
                <div>
                    <label for="meeting-duration" style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">Duration (minutes)</label>
                    <select id="meeting-duration" name="duration_minutes" style="
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid #ced4da;
                        border-radius: 4px;
                        font-size: 14px;
                        box-sizing: border-box;
                    ">
                        <option value="30">30 minutes</option>
                        <option value="45">45 minutes</option>
                        <option value="60" selected>1 hour</option>
                        <option value="90">1.5 hours</option>
                        <option value="120">2 hours</option>
                    </select>
                </div>
                
                <div>
                    <label for="meeting-description" style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">Description</label>
                    <textarea id="meeting-description" name="description" rows="3" style="
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid #ced4da;
                        border-radius: 4px;
                        font-size: 14px;
                        resize: vertical;
                        box-sizing: border-box;
                    "></textarea>
                </div>
                
                <div>
                    <label for="meeting-agenda" style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">Agenda</label>
                    <textarea id="meeting-agenda" name="agenda" rows="4" style="
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid #ced4da;
                        border-radius: 4px;
                        font-size: 14px;
                        resize: vertical;
                        box-sizing: border-box;
                    "></textarea>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                    <button type="button" class="cancel-meeting" style="
                        background: #6c757d;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                    ">Cancel</button>
                    <button type="submit" style="
                        background: #007cba;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                    ">📅 Schedule Meeting</button>
                </div>
            </form>
        </div>
    `;
    
    // Add event listeners
    const closeBtn = modal.querySelector('.close-modal');
    const cancelBtn = modal.querySelector('.cancel-meeting');
    const form = modal.querySelector('#meeting-form');
    
    closeBtn.onclick = () => {
        document.body.removeChild(modal);
    };
    
    cancelBtn.onclick = () => {
        document.body.removeChild(modal);
    };
    
    // Close modal when clicking outside
    modal.onclick = (event) => {
        if (event.target === modal) {
            document.body.removeChild(modal);
        }
    };
    
    // Handle form submission
    form.onsubmit = (event) => {
        event.preventDefault();
        submitMeetingForm(leadId, modal);
    };
    
    return modal;
}

function populateMeetingForm(leadId) {
    // Get lead data from the current page
    const leadNameElement = document.querySelector('#id_company_name');
    const companyName = leadNameElement ? leadNameElement.value : 'Unknown Company';
    
    // Set default values
    document.getElementById('meeting-title').value = `Meeting with ${companyName}`;
    
    // Set default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('meeting-date').value = tomorrow.toISOString().split('T')[0];
    
    // Set default time to 10:00 AM
    document.getElementById('meeting-time').value = '10:00';
    
    // Auto-populate description and agenda based on lead data
    const industryElement = document.querySelector('#id_industry');
    const industry = industryElement ? industryElement.value : '';
    
    let description = `Discussion with contact from ${companyName}`;
    if (industry) {
        description += ` (${industry} industry)`;
    }
    
    document.getElementById('meeting-description').value = description;
    
    // Generate basic agenda
    const agenda = `1. Introduction and rapport building
2. Understand current challenges and pain points
3. Discuss requirements and objectives
4. Present relevant solutions
5. Next steps and follow-up actions`;
    
    document.getElementById('meeting-agenda').value = agenda;
    
    // Set meeting type based on lead status if available
    const statusElement = document.querySelector('#id_status');
    if (statusElement) {
        const status = statusElement.value;
        const meetingTypeSelect = document.getElementById('meeting-type');
        
        switch (status) {
            case 'new':
                meetingTypeSelect.value = 'discovery';
                break;
            case 'contacted':
                meetingTypeSelect.value = 'discovery';
                break;
            case 'qualified':
                meetingTypeSelect.value = 'demo';
                break;
            case 'converted':
                meetingTypeSelect.value = 'proposal';
                break;
            default:
                meetingTypeSelect.value = 'discovery';
        }
    }
}

function submitMeetingForm(leadId, modal) {
    const form = document.getElementById('meeting-form');
    const formData = new FormData(form);
    
    // Combine date and time
    const date = formData.get('date');
    const time = formData.get('time');
    const scheduledAt = `${date}T${time}:00`;
    
    const meetingData = {
        lead: leadId,
        title: formData.get('title'),
        meeting_type: formData.get('meeting_type'),
        scheduled_at: scheduledAt,
        duration_minutes: parseInt(formData.get('duration_minutes')),
        description: formData.get('description'),
        agenda: formData.get('agenda'),
        status: 'scheduled'
    };
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Scheduling...';
    submitBtn.disabled = true;
    
    fetch('/admin/meeting_service/meeting/add/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(meetingData)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            // If direct API fails, redirect to admin add form with pre-filled data
            const params = new URLSearchParams();
            Object.keys(meetingData).forEach(key => {
                if (meetingData[key] !== null && meetingData[key] !== undefined) {
                    params.append(key, meetingData[key]);
                }
            });
            
            window.open(`/admin/meeting_service/meeting/add/?${params.toString()}`, '_blank');
            document.body.removeChild(modal);
            return null;
        }
    })
    .then(data => {
        if (data) {
            if (data.success) {
                alert('Meeting scheduled successfully!');
                location.reload();
            } else {
                alert('Error scheduling meeting: ' + (data.error || 'Unknown error'));
            }
            document.body.removeChild(modal);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Fallback: redirect to admin add form
        const params = new URLSearchParams();
        Object.keys(meetingData).forEach(key => {
            if (meetingData[key] !== null && meetingData[key] !== undefined) {
                params.append(key, meetingData[key]);
            }
        });
        
        window.open(`/admin/meeting_service/meeting/add/?${params.toString()}`, '_blank');
        document.body.removeChild(modal);
    })
    .finally(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
}

function generateMeetingAgenda(leadId) {
    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '🤖 Generating...';
    button.disabled = true;
    
    fetch(`/admin-config/ai/generate-meeting-agenda/?lead_id=${leadId}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show the generated agenda in a modal
            showAgendaModal(data.agenda, leadId);
        } else {
            alert('Error generating agenda: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error generating agenda. Please try again.');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
}

function showAgendaModal(agenda, leadId) {
    const modal = document.createElement('div');
    modal.className = 'agenda-modal';
    modal.style.cssText = `
        display: block;
        position: fixed;
        z-index: 10001;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
    `;
    
    modal.innerHTML = `
        <div class="agenda-modal-content" style="
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: none;
            border-radius: 8px;
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #dee2e6; padding-bottom: 15px;">
                <h2 style="margin: 0; color: #007cba;">🤖 AI-Generated Meeting Agenda</h2>
                <span class="close-agenda-modal" style="
                    color: #aaa;
                    float: right;
                    font-size: 28px;
                    font-weight: bold;
                    cursor: pointer;
                    line-height: 1;
                ">&times;</span>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0; line-height: 1.5;">${agenda}</pre>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button class="close-agenda-modal" style="
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                ">Close</button>
                <button onclick="useAgendaAndSchedule('${leadId}', \`${agenda.replace(/`/g, '\\`')}\`)" style="
                    background: #007cba;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                ">📅 Use This Agenda</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    const closeBtns = modal.querySelectorAll('.close-agenda-modal');
    closeBtns.forEach(btn => {
        btn.onclick = () => {
            document.body.removeChild(modal);
        };
    });
    
    // Close modal when clicking outside
    modal.onclick = (event) => {
        if (event.target === modal) {
            document.body.removeChild(modal);
        }
    };
}

function useAgendaAndSchedule(leadId, agenda) {
    // Close the agenda modal
    const agendaModal = document.querySelector('.agenda-modal');
    if (agendaModal) {
        document.body.removeChild(agendaModal);
    }
    
    // Open the scheduling modal
    scheduleMeeting(leadId);
    
    // Wait a bit for the modal to render, then populate the agenda
    setTimeout(() => {
        const agendaField = document.getElementById('meeting-agenda');
        if (agendaField) {
            agendaField.value = agenda;
        }
    }, 100);
}

// Quick meeting actions for lead list view
function quickScheduleMeeting(leadId, leadName) {
    if (confirm(`Schedule a meeting with ${leadName}?`)) {
        // Quick schedule with default values
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const scheduledAt = `${tomorrow.toISOString().split('T')[0]}T10:00:00`;
        
        const meetingData = {
            lead: leadId,
            title: `Meeting with ${leadName}`,
            meeting_type: 'discovery',
            scheduled_at: scheduledAt,
            duration_minutes: 60,
            description: `Discovery call with ${leadName}`,
            status: 'scheduled'
        };
        
        fetch('/admin/meeting_service/meeting/add/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(meetingData)
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Failed to schedule meeting');
            }
        })
        .then(data => {
            if (data.success) {
                alert('Meeting scheduled successfully!');
                location.reload();
            } else {
                alert('Error scheduling meeting: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Fallback: open detailed scheduling modal
            scheduleMeeting(leadId);
        });
    }
}

// Helper function to get CSRF token (if not already defined)
if (typeof getCookie === 'undefined') {
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
}