
import os
import pandas as pd
from pathlib import Path


def vehicle_count(csv_path, input_type):
  if input_type=='Image':
    df = pd.read_csv(csv_path, header=None)
    print(df.columns.values)

    df.columns=['File','Vehicle_Type', 'Confidence', 'Frame']
    return df.shape[0]

  elif input_type=='Video':
    df = pd.read_csv(csv_path, header=None)
    #get columns of df
    print(df.columns)
    df.columns=['File','Vehicle_Type', 'Confidence', 'Frame']
    df = df.groupby(['Frame','Vehicle_Type']).size().reset_index(name='Count')
    df = df.groupby('Vehicle_Type')['Count'].mean().reset_index()
    df['Count'] = df['Count'].astype(int)
    return df

def num_vehicles(img_path):
  os.system(f"python ../yolov5/detect.py --weights ../best.pt --img 640 --conf 0.4 --save-csv --source {img_path}")
  latest_exp = sorted(Path('../yolov5/runs/detect').glob('exp*'), key=os.path.getmtime)[-1]
  filenames = [f for f in os.listdir(latest_exp) if f.endswith('.csv')]
  count = vehicle_count(f"{latest_exp}/{filenames[0]}", 'Image')
  return count
  
  def ambulance_detection(img_path):
      os.system(f"python ../yolov5/detect.py --weights ../er_best.pt --img 640 --conf 0.4 --save-csv --source {img_path}")
      latest_exp = sorted(Path('../yolov5/runs/detect').glob('exp*'), key=os.path.getmtime)[-1]
      filenames = [f for f in os.listdir(latest_exp) if f.endswith(('.jpeg', '.jpg'))][0]
      print(filenames)
      return f"{latest_exp}/{filenames}"


def detect_vehicles_and_ambulance(image_path):
    """
    Simulate vehicle and ambulance detection
    In production, replace with actual computer vision model
    Returns tuple of (vehicle_count, ambulance_detected)
    """
    vehicle_count = num_vehicles(image_path)
    ambulance_detected = ambulance_detection(image_path)
    return vehicle_count, ambulance_detected

if __name__ == "__main__":
    print(detect_vehicles_and_ambulance("./uploads/signal_1_20250118_040041.jpg"))
#     print(detect_vehicles_and_ambulance("test2.jpg"))
#     print(detect_vehicles_and_ambulance("test3.jpg"))
#     print(detect_vehicles_and_ambulance("test4.jpg"))

