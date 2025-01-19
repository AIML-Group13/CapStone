// Configuration
const API_URL = 'http://localhost:8000';
const SIGNALS = [
    { id: 1, name: 'North Signal' },
    { id: 2, name: 'South Signal' },
    { id: 3, name: 'East Signal' },
    { id: 4, name: 'West Signal' }
];

function updateSignalDisplays() {
    controller.signals.forEach((data, id) => {
        updateSignalUI(id, data);
    });
}

function updateTrafficLights(card, status) {
    const lights = card.querySelectorAll('.light');
    lights.forEach(light => light.classList.remove('active'));

    if (status === 'Green') {
        card.querySelector('.light.green').classList.add('active');
    } else if (status === 'Yellow') {
        card.querySelector('.light.yellow').classList.add('active');
    } else if (status === 'Red') {
        card.querySelector('.light.red').classList.add('active');
    }
}


// Simulation Control
function toggleSimulation() {
    const startButton = document.getElementById('startSimulation');
    isSimulationRunning = !isSimulationRunning;
    
    if (isSimulationRunning) {
        startButton.textContent = 'Stop Simulation';
        startSimulation();
    } else {
        startButton.textContent = 'Start Simulation';
        stopSimulation();
    }
}
// State management
class SignalController {
    constructor() {
        this.signals = new Map();
        this.totalTime = 120;
        this.isRunning = false;
        this.emergencyMode = false;
    }

    updateSignal(id, data) {
        this.signals.set(id, {
            ...this.signals.get(id),
            ...data
        });
    }

    getSignal(id) {
        return this.signals.get(id);
    }

    hasAmbulance() {
        let hasEmergency = false;
        this.signals.forEach(signal => {
            if (signal.ambulanceDetected) hasEmergency = true;
        });
        return hasEmergency;
    }
}

const controller = new SignalController();
let isSimulationRunning = false;
let currentSignalIndex = 0;
let simulationInterval;
let currentTimer;

// Initialize application
function initializeApp() {
    createSignalCards();
    setupEventListeners();
    fetchInitialData();
}

// Create signal cards
function createSignalCards() {
    const signalGrid = document.querySelector('.signal-grid');
    const template = document.getElementById('signal-template');

    SIGNALS.forEach(signal => {
        const card = template.content.cloneNode(true);
        const signalCard = card.querySelector('.signal-card');
        
        signalCard.dataset.signalId = signal.id;
        signalCard.querySelector('.signal-name').textContent = signal.name;
        
        const fileInput = card.querySelector('.file-input');
        fileInput.addEventListener('change', (e) => handleImageUpload(e, signal.id));
        
        controller.updateSignal(signal.id, {
            vehicleCount: 0,
            timing: 0,
            status: 'Waiting',
            ambulanceDetected: false
        });
        
        signalGrid.appendChild(card);
    });
}

// Event Listeners
function setupEventListeners() {
    const startButton = document.getElementById('startSimulation');
    const totalTimeInput = document.getElementById('totalTime');

    startButton.addEventListener('click', toggleSimulation);
    totalTimeInput.addEventListener('change', (e) => {
        controller.totalTime = parseInt(e.target.value);
        updateTimings();
    });
}
// API Calls
async function fetchInitialData() {
    try {
        const response = await fetch(`${API_URL}/signals`);
        const data = await response.json();
        
        Object.entries(data).forEach(([id, signalData]) => {
            controller.updateSignal(parseInt(id), signalData);
        });
        
        updateSignalDisplays();
    } catch (error) {
        console.error('Error fetching initial data:', error);
        showError('Failed to fetch signal data');
    }
}
// API Calls
async function handleImageUpload(event, signalId) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/upload-image/${signalId}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        updateSignalUI(signalId, {
            vehicleCount: data.vehicle_count,
            ambulanceDetected: data.ambulance_detected,
            // image: URL.createObjectURL(file)
            image: data.image_url
        });
        
        controller.updateSignal(signalId, {
            vehicleCount: data.vehicle_count,
            ambulanceDetected: data.ambulance_detected
        });
        
        await updateTimings();
        
        // If ambulance detected, show alert
        if (data.ambulance_detected) {
            showEmergencyAlert(signalId);
        }
    } catch (error) {
        console.error('Error uploading image:', error);
        showError('Failed to upload image');
    }
}

async function updateTimings() {
    const timings = Array.from(controller.signals.entries()).map(([id, data]) => ({
        signal_id: id,
        vehicle_count: data.vehicleCount,
        ambulance_detected: data.ambulanceDetected,
        timing: data.timing // Will be calculated on backend
    }));

    try {
        const response = await fetch(`${API_URL}/update-timings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timings,
                total_time: controller.totalTime
            })
        });
        
        const data = await response.json();
        controller.emergencyMode = data.ambulance_priority;
        
        // Refresh display
        await fetchInitialData();
    } catch (error) {
        console.error('Error updating timings:', error);
        showError('Failed to update signal timings');
    }
}

// UI Updates
function updateSignalUI(signalId, data) {
    const card = document.querySelector(`[data-signal-id="${signalId}"]`);
    if (!card) return;

    if (data.image) {
        const img = card.querySelector('.traffic-image');
        const uploadArea = card.querySelector('.upload-area');
        img.src = data.image;
        img.style.display = 'block';
        uploadArea.style.display = 'none';
    }

    if (data.vehicleCount !== undefined) {
        card.querySelector('.vehicle-count').textContent = data.vehicleCount;
    }

    if (data.timing !== undefined) {
        card.querySelector('.signal-timing').textContent = `${data.timing}s`;
    }

    if (data.status) {
        card.querySelector('.signal-status').textContent = data.status;
    }

    if (data.ambulanceDetected !== undefined) {
        card.classList.toggle('emergency', data.ambulanceDetected);
        const emergencyIndicator = card.querySelector('.emergency-indicator');
        if (emergencyIndicator) {
            emergencyIndicator.style.display = data.ambulanceDetected ? 'block' : 'none';
        }
    }

    updateTrafficLights(card, data.status);
}

function showEmergencyAlert(signalId) {
    const signal = SIGNALS.find(s => s.id === signalId);
    const alertDiv = document.createElement('div');
    alertDiv.className = 'emergency-alert';
    alertDiv.innerHTML = `
        <div class="alert-content">
            <strong>⚠️ Emergency Vehicle Detected!</strong>
            <p>Ambulance detected at ${signal.name}. Adjusting signal timing for priority passage.</p>
        </div>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

// Simulation Logic
function runSignalCycle() {
    const signalIds = Array.from(controller.signals.keys());
    
    function updateCycle() {
        const currentId = signalIds[currentSignalIndex];
        const currentSignal = controller.getSignal(currentId);
        
        // If ambulance detected, give priority
        if (currentSignal.ambulanceDetected) {
            controller.emergencyMode = true;
            currentSignal.timing = Math.max(45, currentSignal.timing);
        }
        
        // Reset all signals to red
        signalIds.forEach(id => {
            controller.updateSignal(id, { status: 'Red' });
        });
        
        // Set current signal to green
        controller.updateSignal(currentId, { status: 'Green' });
        updateSignalDisplays();
        
        const cycleTime = controller.emergencyMode ? 45000 : currentSignal.timing * 1000;
        
        // Schedule yellow light
        currentTimer = setTimeout(() => {
            controller.updateSignal(currentId, { status: 'Yellow' });
            updateSignalDisplays();
            
            // Schedule next signal
            currentTimer = setTimeout(() => {
                currentSignalIndex = (currentSignalIndex + 1) % signalIds.length;
                if (isSimulationRunning) {
                    // Check if next signal has ambulance
                    const nextSignal = controller.getSignal(signalIds[currentSignalIndex]);
                    if (nextSignal.ambulanceDetected) {
                        showEmergencyAlert(signalIds[currentSignalIndex]);
                    }
                    updateCycle();
                }
            }, 3000); // Yellow light duration
        }, cycleTime - 3000);
    }
    
    updateCycle();
}

// Add to your CSS (styles.css)
`.emergency-alert {
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #ff4444;
    color: white;
    padding: 15px;
    border-radius: 5px;
    z-index: 1000;
    animation: slideIn 0.5s ease-out;
}

.emergency-indicator {
    position: absolute;
    top: 10px;
    right: 10px;
    background-color: #ff4444;
    color: white;
    padding: 5px 10px;
    border-radius: 3px;
    font-size: 12px;
    display: none;
}

@keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}`

// Initialize the application
document.addEventListener('DOMContentLoaded', initializeApp);
