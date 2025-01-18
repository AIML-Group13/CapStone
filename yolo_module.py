import os
import pandas as pd
from pathlib import Path



def num_vehicles(img_path):
  os.system(f"python ../yolov5/detect.py --weights ../best.pt --img 640 --conf 0.4 --save-csv --source {img_path}")
  latest_exp = sorted(Path('../yolov5/runs/detect').glob('exp*'), key=os.path.getmtime)[-1]
  filenames = [f for f in os.listdir(latest_exp) if f.endswith('.csv')]
  count = vehicle_count(f"{latest_exp}/{filenames[0]}", 'Image')
  return count

def vehicle_count(csv_path, input_type):
  if input_type=='Image':
    df = pd.read_csv(csv_path, header=None)
    df.columns=['File','Vehicle_Type', 'Confidence', 'Frame']
    return df.shape[0]
  elif input_type=='Video':
    df = pd.read_csv(csv_path, header=None)
    df.columns=['File','Vehicle_Type', 'Confidence', 'Frame']
    df = df.groupby(['Frame','Vehicle_Type']).size().reset_index(name='Count')
    df = df.groupby('Vehicle_Type')['Count'].mean().reset_index()
    df['Count'] = df['Count'].astype(int)
    return df

  def ambulance_detection(img_path):
    os.system(f"python ../yolov5/detect.py --weights ../er_best.pt --img 640 --conf 0.4 --save-csv --source {img_path}")
    latest_exp = sorted(Path('../yolov5/runs/detect').glob('exp*'), key=os.path.getmtime)[-1]
    filenames = [f for f in os.listdir(latest_exp) if f.endswith(('.jpeg', '.jpg'))][0]
    print(filenames)
    return f"{latest_exp}/{filenames}"
