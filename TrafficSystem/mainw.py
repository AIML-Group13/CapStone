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
import os,subprocess
import time
import platform

import logging
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from yolo_module import *

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.mount("/TrafficMonitor", StaticFiles(directory="../TrafficMonitor"), name="TrafficMonitor")


logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="../TrafficMonitor/templates/")

# Assuming signals is a dictionary to store signal data
signals = {
    1: {"name": "North Signal", "vehicle_count": 0, "timing": 0, "image_path": None, "ambulance_count": 0},
    2: {"name": "South Signal", "vehicle_count": 0, "timing": 0, "image_path": None, "ambulance_count": 0},
    3: {"name": "East Signal", "vehicle_count": 0, "timing": 0, "image_path": None, "ambulance_count": 0},
    4: {"name": "West Signal", "vehicle_count": 0, "timing": 0, "image_path": None, "ambulance_count": 0},
}

class SignalTiming(BaseModel):
    signal_id: int
    timing: int
    vehicle_count: int

class SignalUpdate(BaseModel):
    timings: List[SignalTiming]
    total_time: int
    signal_duration: int  # Add signal_duration here

def calculate_priority_timing(signal_data, total_time):
    """
    Calculate signal timing with ambulance priority
    """
    base_timing = total_time // len(signals)
    
    # If ambulance detected, allocate minimum 45 seconds
    if signal_data["ambulance_count"] > 0:
        return max(45, base_timing)
    
    return base_timing

@app.get("/home", response_class=HTMLResponse)
async def get_index(request: Request):
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
    ambulance_count, ambulance_detect_vehicle_file = ambulance_detection(file_location)
    
    signals[signal_id].update({
        "vehicle_count": vehicle_count,
        "ambulance_count": ambulance_count,
        "image_path": ambulance_detect_vehicle_file if ambulance_count > 0 else detect_vehicle_file
    })
    
    return {
        "signal_id": signal_id,
        "vehicle_count": vehicle_count,
        "ambulance_count": ambulance_count,
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
    try:
        signal_duration = update.signal_duration  # Get signal_duration from the request body

        # Check for ambulances first
        ambulance_signals = []
        for timing in update.timings:
            signal_id = timing.signal_id
            if signal_id in signals:
                if signals[signal_id]["ambulance_count"] > 0:
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
        
        # Allocate remaining time based on vehicle count
        remaining_signals = [t for t in update.timings if t.signal_id not in processed_signals]
        total_vehicle_count = sum(t.vehicle_count for t in remaining_signals)
        
        if total_vehicle_count > 0:
            for timing in remaining_signals:
                signal_id = timing.signal_id
                vehicle_count = timing.vehicle_count
                allocated_time = int(vehicle_count * remaining_time / total_vehicle_count)
                signals[signal_id]["timing"] = allocated_time
        
        return {
            "message": "Timings updated successfully",
            "ambulance_priority": len(ambulance_signals) > 0
        }
    except Exception as e:
        logger.error(f"Error updating timings: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while updating timings")

def clone_and_setup_yolov5():
    try:
        # Clone the repository
        subprocess.run(["git", "clone", "https://github.com/ultralytics/yolov5"], check=True)
        
        # Change directory to yolov5
        os.chdir("yolov5")
        
        # Install requirements
        subprocess.run(["pip", "install", "-qr", "requirements.txt"], check=True)
        subprocess.run(["pip", "install", "comet_ml"], check=True)
        
        print("YOLOv5 setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while setting up YOLOv5: {e}")
    finally:
        # Change back to the original directory
        os.chdir("..")

if __name__ == "__main__":
    os.chdir("..")
    
    # Remove existing yolov5 directory
    if platform.system() == "Windows":
        os.system("rmdir /S /Q yolov5")
    else:
        os.system("rm -rf yolov5")
    
    clone_and_setup_yolov5()
    
    # Copy detect.py file from TrafficSystem to yolov5
    if platform.system() == "Windows":
        os.system("copy TrafficSystem\\detect.py yolov5")
    else:
        os.system("cp TrafficSystem/detect.py yolov5")
    
    #know the current directory
    print("Current Directory",os.getcwd())
    
    # # Ensure the TrafficMonitor directory exists
    # traffic_monitor_dir = os.path.join("..", "TrafficMonitor")
    # if not os.path.exists(traffic_monitor_dir):
    #     os.makedirs(traffic_monitor_dir)
    
    # app.mount("/TrafficMonitor", StaticFiles(directory=traffic_monitor_dir), name="TrafficMonitor")
    
    os.chdir("TrafficSystem")
    
    # Start the FastAPI app
    uvicorn.run("mainw:app", host="0.0.0.0", port=8000, reload=True)
