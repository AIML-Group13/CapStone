// Configuration
const API_URL = 'http://localhost:8051';
const SIGNALS = [
    { id: 1, name: 'North Signal' },
    { id: 2, name: 'South Signal' },
    { id: 3, name: 'East Signal' },
    { id: 4, name: 'West Signal' }
];

// State management
let isSimulationRunning = false;
let currentSignalIndex = 0;
let simulationInterval;
let currentTimer;

class SignalController {
    constructor() {
        this.signals = new Map();
        this.totalTime = 120; // Default total cycle time
        this.isRunning = false;
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

    getTotalVehicles() {
        let total = 0;
        this.signals.forEach(signal => {
            total += signal.vehicleCount || 0;
        });
        return total;
    }
}

const controller = new SignalController();

// DOM Element References
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

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
            status: 'Waiting'
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

async function handleImageUpload(event, signalId) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/upload/${signalId}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        updateSignalUI(signalId, {
            vehicleCount: data.vehicle_count,
            image: URL.createObjectURL(file)
        });
        
        controller.updateSignal(signalId, {
            vehicleCount: data.vehicle_count
        });
        
        await updateTimings();
    } catch (error) {
        console.error('Error uploading image:', error);
        showError('Failed to upload image');
    }
}

async function updateTimings() {
    const timings = Array.from(controller.signals.entries()).map(([id, data]) => ({
        signal_id: id,
        vehicle_count: data.vehicleCount,
        timing: calculateTiming(data.vehicleCount, controller.getTotalVehicles(), controller.totalTime)
    }));

    try {
        await fetch(`${API_URL}/update-timings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timings,
                total_time: controller.totalTime
            })
        });
        
        timings.forEach(timing => {
            controller.updateSignal(timing.signal_id, {
                timing: timing.timing
            });
        });
        
        updateSignalDisplays();
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

    updateTrafficLights(card, data.status);
}

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

function startSimulation() {
    currentSignalIndex = 0;
    runSignalCycle();
}

function stopSimulation() {
    clearInterval(simulationInterval);
    clearTimeout(currentTimer);
    
    controller.signals.forEach((_, id) => {
        controller.updateSignal(id, { status: 'Waiting' });
    });
    
    updateSignalDisplays();
}

function runSignalCycle() {
    const signalIds = Array.from(controller.signals.keys());
    
    function updateCycle() {
        const currentId = signalIds[currentSignalIndex];
        const currentSignal = controller.getSignal(currentId);
        
        // Reset all signals to red
        signalIds.forEach(id => {
            controller.updateSignal(id, { status: 'Red' });
        });
        
        // Set current signal to green
        controller.updateSignal(currentId, { status: 'Green' });
        updateSignalDisplays();
        
        // Schedule yellow light
        currentTimer = setTimeout(() => {
            controller.updateSignal(currentId, { status: 'Yellow' });
            updateSignalDisplays();
            
            // Schedule next signal
            currentTimer = setTimeout(() => {
                currentSignalIndex = (currentSignalIndex + 1) % signalIds.length;
                if (isSimulationRunning) {
                    updateCycle();
                }
            }, 3000); // Yellow light duration
        }, (currentSignal.timing * 1000) - 3000);
    }
    
    updateCycle();
}

// Utility Functions
function calculateTiming(vehicleCount, totalVehicles, totalTime) {
    if (totalVehicles === 0) return Math.round(totalTime / 4);
    const minTime = 15; // Minimum green light time
    const calculatedTime = Math.round((vehicleCount / totalVehicles) * totalTime);
    return Math.max(minTime, calculatedTime);
}

function showError(message) {
    // You can implement your preferred error display method here
    alert(message);
}
