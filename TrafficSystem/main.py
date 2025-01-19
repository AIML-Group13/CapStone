from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse,FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import cv2
import numpy as np
import base64
from datetime import datetime
import uvicorn
import os
import time

import logging
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from yolo_module import *
# app = APIRouter()


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.mount("/TrafficMonitor", StaticFiles(directory="../TrafficMonitor"), name="TrafficMonitor")


logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="../TrafficMonitor/templates/")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SignalTiming(BaseModel):
    signal_id: int
    timing: int
    vehicle_count: int
    ambulance_detected: bool

class SignalUpdate(BaseModel):
    timings: List[SignalTiming]
    total_time: int

# Store signal data in memory (in production, use a database)
signals = {
    1: {"name": "North Signal", "vehicle_count": 0, "timing": 0, "ambulance_detected": False, "image_path": None},
    2: {"name": "South Signal", "vehicle_count": 0, "timing": 0, "ambulance_detected": False, "image_path": None},
    3: {"name": "East Signal", "vehicle_count": 0, "timing": 0, "ambulance_detected": False, "image_path": None},
    4: {"name": "West Signal", "vehicle_count": 0, "timing": 0, "ambulance_detected": False, "image_path": None},
}

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# def detect_vehicles_and_ambulance(image_path):
#     """
#     Simulate vehicle and ambulance detection
#     In production, replace with actual computer vision model
#     Returns tuple of (vehicle_count, ambulance_detected)
#     """
#     # Simulate detection with random numbers for demonstration
#     vehicle_count = np.random.randint(5, 20)
#     ambulance_detected = np.random.random() < 0.2  # 20% chance of ambulance detection
#     return vehicle_count, ambulance_detected

def calculate_priority_timing(signal_data, total_time):
    """
    Calculate signal timing with ambulance priority
    """
    base_timing = total_time // len(signals)
    
    # If ambulance detected, allocate minimum 45 seconds
    if signal_data["ambulance_detected"]:
        return max(45, base_timing)
    
    return base_timing

@app.get("/home", response_class=HTMLResponse)
async def get_index(request: Request):
    # user = request.session.get('user')
    # if not user:
    #     return RedirectResponse(url="/login")
    logger.info("Invoked home page")
    return templates.TemplateResponse("index.html", {"request": request, "title": "Traffic Control System"})


@app.get("/signals")
async def get_signals():
    return signals

@app.post("/upload-image/{signal_id}")
async def upload_image(signal_id: int, file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    
    vehicle_count, detect_vehicle_file = num_vehicles(file_location)
    ambulance_detected = ambulance_detection(file_location)
    
    signals[signal_id].update({
        "vehicle_count": vehicle_count,
        "ambulance_detected": ambulance_detected,
        "image_path": detect_vehicle_file
    })
    
    return {
        "signal_id": signal_id,
        "vehicle_count": vehicle_count,
        "ambulance_detected": ambulance_detected,
        "message": "Image uploaded and processed successfully",
        "image_url": f"/get-image/{signal_id}?t={int(time.time())}"  # Add timestamp to force refresh
    }

@app.get("/get-image/{signal_id}")
async def get_image(signal_id: int):
    if signal_id in signals and signals[signal_id]["image_path"]:
        return FileResponse(signals[signal_id]["image_path"])
    return {"error": "Image not found"}


@app.post("/update-timings")
async def update_timings(update: SignalUpdate):
    # Check for ambulances first
    ambulance_signals = []
    for timing in update.timings:
        signal_id = timing.signal_id
        if signal_id in signals:
            if signals[signal_id]["ambulance_detected"]:
                ambulance_signals.append(signal_id)
    
    remaining_time = update.total_time
    processed_signals = set()
    
    # Handle ambulance signals first
    if ambulance_signals:
        priority_time = max(45, update.total_time // len(ambulance_signals))
        for signal_id in ambulance_signals:
            signals[signal_id]["timing"] = priority_time
            processed_signals.add(signal_id)
            remaining_time -= priority_time
    
    # Distribute remaining time among other signals
    remaining_signals = [t.signal_id for t in update.timings if t.signal_id not in processed_signals]
    if remaining_signals:
        time_per_signal = max(15, remaining_time // len(remaining_signals))
        for signal_id in remaining_signals:
            signals[signal_id]["timing"] = time_per_signal
    
    return {
        "message": "Timings updated successfully",
        "ambulance_priority": len(ambulance_signals) > 0
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
