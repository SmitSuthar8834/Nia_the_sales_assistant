// Visual Workflow Builder JavaScript

class WorkflowBuilder {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.draggedNode = null;
        this.isConnecting = false;
        this.connectionStart = null;
        
        this.initializeCanvas();
        this.setupEventListeners();
    }
    
    initializeCanvas() {
        this.canvas.style.position = 'relative';
        this.canvas.style.overflow = 'auto';
        this.canvas.innerHTML = '';
        
        // Add grid background
        this.canvas.style.backgroundImage = `
            radial-gradient(circle, #ccc 1px, transparent 1px)
        `;
        this.canvas.style.backgroundSize = '20px 20px';
    }
    
    setupEventListeners() {
        this.canvas.addEventListener('click', this.onCanvasClick.bind(this));
        this.canvas.addEventListener('dragover', this.onDragOver.bind(this));
        this.canvas.addEventListener('drop', this.onDrop.bind(this));
        
        // Prevent default drag behavior
        this.canvas.addEventListener('dragenter', e => e.preventDefault());
    }
    
    onCanvasClick(e) {
        if (e.target === this.canvas) {
            this.deselectAllNodes();
        }
    }
    
    onDragOver(e) {
        e.preventDefault();
    }
    
    onDrop(e) {
        e.preventDefault();
        const nodeType = e.dataTransfer.getData('text/plain');
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.addNode(nodeType, x, y);
    }
    
    addNode(type, x, y) {
        const nodeId = `node_${Date.now()}`;
        const node = {
            id: nodeId,
            type: type,
            x: x,
            y: y,
            config: this.getDefaultNodeConfig(type)
        };
        
        this.nodes.push(node);
        this.renderNode(node);
        this.selectNode(node);
    }
    
    getDefaultNodeConfig(type) {
        const configs = {
            'trigger': {
                name: 'Trigger',
                icon: 'fas fa-play',
                color: '#28a745',
                inputs: [],
                outputs: ['output']
            },
            'action': {
                name: 'Action',
                icon: 'fas fa-cog',
                color: '#007bff',
                inputs: ['input'],
                outputs: ['output']
            },
            'condition': {
                name: 'Condition',
                icon: 'fas fa-question',
                color: '#ffc107',
                inputs: ['input'],
                outputs: ['true', 'false']
            },
            'integration': {
                name: 'Integration',
                icon: 'fas fa-plug',
                color: '#6f42c1',
                inputs: ['input'],
                outputs: ['success', 'error']
            },
            'end': {
                name: 'End',
                icon: 'fas fa-stop',
                color: '#dc3545',
                inputs: ['input'],
                outputs: []
            }
        };
        
        return configs[type] || configs['action'];
    }
    
    renderNode(node) {
        const nodeElement = document.createElement('div');
        nodeElement.className = 'workflow-node';
        nodeElement.id = node.id;
        nodeElement.style.left = `${node.x}px`;
        nodeElement.style.top = `${node.y}px`;
        nodeElement.draggable = true;
        
        nodeElement.innerHTML = `
            <div class="node-header" style="background-color: ${node.config.color}; color: white; padding: 8px; border-radius: 4px 4px 0 0;">
                <i class="${node.config.icon} me-2"></i>
                <span class="node-title">${node.config.name}</span>
                <button class="btn btn-sm btn-outline-light float-end node-delete" onclick="workflowBuilder.deleteNode('${node.id}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="node-body" style="padding: 12px; background: white; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 4px 4px;">
                <div class="node-config">
                    <small class="text-muted">Click to configure</small>
                </div>
                <div class="node-ports">
                    ${this.renderNodePorts(node)}
                </div>
            </div>
        `;
        
        // Add event listeners
        nodeElement.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectNode(node);
        });
        
        nodeElement.addEventListener('dragstart', (e) => {
            this.draggedNode = node;
            e.dataTransfer.effectAllowed = 'move';
        });
        
        nodeElement.addEventListener('dragend', () => {
            this.draggedNode = null;
        });
        
        this.canvas.appendChild(nodeElement);
    }
    
    renderNodePorts(node) {
        let portsHtml = '';
        
        // Input ports
        node.config.inputs.forEach((input, index) => {
            portsHtml += `
                <div class="input-port" data-port="${input}" style="position: absolute; left: -8px; top: ${30 + index * 20}px; width: 16px; height: 16px; background: #007bff; border-radius: 50%; cursor: pointer;" 
                     onclick="workflowBuilder.startConnection('${node.id}', '${input}', 'input')"></div>
            `;
        });
        
        // Output ports
        node.config.outputs.forEach((output, index) => {
            portsHtml += `
                <div class="output-port" data-port="${output}" style="position: absolute; right: -8px; top: ${30 + index * 20}px; width: 16px; height: 16px; background: #28a745; border-radius: 50%; cursor: pointer;"
                     onclick="workflowBuilder.startConnection('${node.id}', '${output}', 'output')"></div>
            `;
        });
        
        return portsHtml;
    }
    
    selectNode(node) {
        this.deselectAllNodes();
        this.selectedNode = node;
        
        const nodeElement = document.getElementById(node.id);
        nodeElement.classList.add('selected');
        
        // Show node configuration panel
        this.showNodeConfig(node);
    }
    
    deselectAllNodes() {
        this.selectedNode = null;
        this.canvas.querySelectorAll('.workflow-node').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Hide configuration panel
        this.hideNodeConfig();
    }
    
    showNodeConfig(node) {
        const configPanel = document.getElementById('nodeConfigPanel');
        if (!configPanel) return;
        
        configPanel.style.display = 'block';
        configPanel.innerHTML = `
            <h6><i class="${node.config.icon} me-2"></i>${node.config.name} Configuration</h6>
            <form id="nodeConfigForm">
                <div class="mb-3">
                    <label class="form-label">Node Name</label>
                    <input type="text" class="form-control" value="${node.config.name}" onchange="workflowBuilder.updateNodeName('${node.id}', this.value)">
                </div>
                ${this.getNodeSpecificConfig(node)}
                <button type="button" class="btn btn-primary btn-sm" onclick="workflowBuilder.saveNodeConfig('${node.id}')">
                    Save Configuration
                </button>
            </form>
        `;
    }
    
    getNodeSpecificConfig(node) {
        switch (node.type) {
            case 'trigger':
                return `
                    <div class="mb-3">
                        <label class="form-label">Trigger Type</label>
                        <select class="form-select" name="trigger_type">
                            <option value="manual">Manual</option>
                            <option value="schedule">Scheduled</option>
                            <option value="webhook">Webhook</option>
                            <option value="event">Event</option>
                        </select>
                    </div>
                `;
            case 'integration':
                return `
                    <div class="mb-3">
                        <label class="form-label">Integration</label>
                        <select class="form-select" name="integration_id">
                            <option value="">Select Integration</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Action</label>
                        <select class="form-select" name="action">
                            <option value="create">Create Record</option>
                            <option value="update">Update Record</option>
                            <option value="delete">Delete Record</option>
                            <option value="query">Query Records</option>
                        </select>
                    </div>
                `;
            case 'condition':
                return `
                    <div class="mb-3">
                        <label class="form-label">Condition</label>
                        <textarea class="form-control" name="condition" rows="3" placeholder="Enter condition logic"></textarea>
                    </div>
                `;
            default:
                return `
                    <div class="mb-3">
                        <label class="form-label">Configuration</label>
                        <textarea class="form-control" name="config" rows="3" placeholder="Enter configuration JSON"></textarea>
                    </div>
                `;
        }
    }
    
    hideNodeConfig() {
        const configPanel = document.getElementById('nodeConfigPanel');
        if (configPanel) {
            configPanel.style.display = 'none';
        }
    }
    
    updateNodeName(nodeId, newName) {
        const node = this.nodes.find(n => n.id === nodeId);
        if (node) {
            node.config.name = newName;
            const titleElement = document.querySelector(`#${nodeId} .node-title`);
            if (titleElement) {
                titleElement.textContent = newName;
            }
        }
    }
    
    saveNodeConfig(nodeId) {
        const form = document.getElementById('nodeConfigForm');
        const formData = new FormData(form);
        const config = Object.fromEntries(formData.entries());
        
        const node = this.nodes.find(n => n.id === nodeId);
        if (node) {
            node.config = { ...node.config, ...config };
            AdminConfig.showAlert('Node configuration saved', 'success', 2000);
        }
    }
    
    deleteNode(nodeId) {
        if (!confirm('Are you sure you want to delete this node?')) {
            return;
        }
        
        // Remove node from array
        this.nodes = this.nodes.filter(n => n.id !== nodeId);
        
        // Remove connections involving this node
        this.connections = this.connections.filter(c => 
            c.fromNode !== nodeId && c.toNode !== nodeId
        );
        
        // Remove node element
        const nodeElement = document.getElementById(nodeId);
        if (nodeElement) {
            nodeElement.remove();
        }
        
        // Redraw connections
        this.redrawConnections();
        
        // Hide config panel if this node was selected
        if (this.selectedNode && this.selectedNode.id === nodeId) {
            this.hideNodeConfig();
        }
    }
    
    startConnection(nodeId, port, type) {
        if (this.isConnecting) {
            // Complete connection
            this.completeConnection(nodeId, port, type);
        } else {
            // Start connection
            this.isConnecting = true;
            this.connectionStart = { nodeId, port, type };
            this.canvas.style.cursor = 'crosshair';
        }
    }
    
    completeConnection(toNodeId, toPort, toType) {
        if (!this.connectionStart || this.connectionStart.nodeId === toNodeId) {
            this.cancelConnection();
            return;
        }
        
        // Validate connection (output to input only)
        if (this.connectionStart.type === toType) {
            AdminConfig.showAlert('Cannot connect same port types', 'warning', 2000);
            this.cancelConnection();
            return;
        }
        
        const connection = {
            id: `conn_${Date.now()}`,
            fromNode: this.connectionStart.type === 'output' ? this.connectionStart.nodeId : toNodeId,
            fromPort: this.connectionStart.type === 'output' ? this.connectionStart.port : toPort,
            toNode: this.connectionStart.type === 'input' ? this.connectionStart.nodeId : toNodeId,
            toPort: this.connectionStart.type === 'input' ? this.connectionStart.port : toPort
        };
        
        this.connections.push(connection);
        this.redrawConnections();
        this.cancelConnection();
    }
    
    cancelConnection() {
        this.isConnecting = false;
        this.connectionStart = null;
        this.canvas.style.cursor = 'default';
    }
    
    redrawConnections() {
        // Remove existing connection elements
        this.canvas.querySelectorAll('.workflow-connection').forEach(el => el.remove());
        
        // Draw all connections
        this.connections.forEach(connection => {
            this.drawConnection(connection);
        });
    }
    
    drawConnection(connection) {
        const fromNode = document.getElementById(connection.fromNode);
        const toNode = document.getElementById(connection.toNode);
        
        if (!fromNode || !toNode) return;
        
        const fromRect = fromNode.getBoundingClientRect();
        const toRect = toNode.getBoundingClientRect();
        const canvasRect = this.canvas.getBoundingClientRect();
        
        const fromX = fromRect.right - canvasRect.left;
        const fromY = fromRect.top + fromRect.height / 2 - canvasRect.top;
        const toX = toRect.left - canvasRect.left;
        const toY = toRect.top + toRect.height / 2 - canvasRect.top;
        
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.className = 'workflow-connection';
        svg.style.position = 'absolute';
        svg.style.left = '0';
        svg.style.top = '0';
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.pointerEvents = 'none';
        svg.style.zIndex = '1';
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const midX = (fromX + toX) / 2;
        const d = `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`;
        
        path.setAttribute('d', d);
        path.setAttribute('stroke', '#007bff');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('fill', 'none');
        path.setAttribute('marker-end', 'url(#arrowhead)');
        
        // Add arrowhead marker
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrowhead');
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '7');
        marker.setAttribute('refX', '9');
        marker.setAttribute('refY', '3.5');
        marker.setAttribute('orient', 'auto');
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
        polygon.setAttribute('fill', '#007bff');
        
        marker.appendChild(polygon);
        defs.appendChild(marker);
        svg.appendChild(defs);
        svg.appendChild(path);
        
        this.canvas.appendChild(svg);
    }
    
    exportWorkflow() {
        return {
            nodes: this.nodes,
            connections: this.connections,
            metadata: {
                created: new Date().toISOString(),
                version: '1.0'
            }
        };
    }
    
    importWorkflow(workflowData) {
        this.clear();
        
        if (workflowData.nodes) {
            workflowData.nodes.forEach(node => {
                this.nodes.push(node);
                this.renderNode(node);
            });
        }
        
        if (workflowData.connections) {
            this.connections = workflowData.connections;
            this.redrawConnections();
        }
    }
    
    clear() {
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.canvas.innerHTML = '';
        this.hideNodeConfig();
    }
}

// Global workflow builder instance
let workflowBuilder = null;

// Initialize workflow builder when DOM is ready
$(document).ready(function() {
    if (document.getElementById('workflowCanvas')) {
        workflowBuilder = new WorkflowBuilder('workflowCanvas');
    }
});

// Drag and drop from toolbox
function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.dataset.nodeType);
}