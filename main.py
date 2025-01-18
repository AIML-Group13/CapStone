from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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

import logging
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

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

class SignalUpdate(BaseModel):
    timings: List[SignalTiming]
    total_time: int

# Store signal data in memory (in production, use a database)
signals = {
    1: {"name": "North Signal", "vehicle_count": 0, "timing": 0, "image_path": None},
    2: {"name": "South Signal", "vehicle_count": 0, "timing": 0, "image_path": None},
    3: {"name": "East Signal", "vehicle_count": 0, "timing": 0, "image_path": None},
    4: {"name": "West Signal", "vehicle_count": 0, "timing": 0, "image_path": None},
}

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

def count_vehicles(image_path):
    """
    Simulate vehicle detection (in production, use real computer vision)
    Returns a random number for demonstration
    """
    return np.random.randint(5, 20)

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # user = request.session.get('user')
    # if not user:
    #     return RedirectResponse(url="/login")
    logger.info("Invoked home page")
    return templates.TemplateResponse("index.html", {"request": request, "title": "Traffic Control System"})


@app.get("/signals")
async def get_signals():
    return signals

@app.post("/upload/{signal_id}")
async def upload_image(signal_id: int, file: UploadFile = File(...)):
    if signal_id not in signals:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Save the uploaded image
    file_path = f"uploads/signal_{signal_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Count vehicles in the image
    vehicle_count = count_vehicles(file_path)
    
    # Update signal data
    signals[signal_id]["image_path"] = file_path
    signals[signal_id]["vehicle_count"] = vehicle_count
    
    return {
        "signal_id": signal_id,
        "vehicle_count": vehicle_count,
        "message": "Image uploaded successfully"
    }

@app.post("/update-timings")
async def update_timings(update: SignalUpdate):
    total_vehicles = sum(timing.vehicle_count for timing in update.timings)
    
    if total_vehicles > 0:
        for timing in update.timings:
            signal_id = timing.signal_id
            if signal_id in signals:
                signals[signal_id]["timing"] = timing.timing
    
    return {"message": "Timings updated successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8051, reload=True)
