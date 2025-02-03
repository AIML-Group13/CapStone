import os
import pandas as pd
from pathlib import Path
import platform

def vehicle_count(csv_path, input_type):
    if input_type == 'Image':
        df = pd.read_csv(csv_path, header=None)
        df.columns = ['File', 'Vehicle_Type', 'Confidence']
        return df.shape[0]
    elif input_type == 'Video':
        df = pd.read_csv(csv_path, header=None)
        # Get columns of df
        print(df.columns)
        df.columns = ['File', 'Vehicle_Type', 'Confidence', 'Frame']
        df = df.groupby(['Frame', 'Vehicle_Type']).size().reset_index(name='Count')
        df = df.groupby('Vehicle_Type')['Count'].mean().reset_index()
        df['Count'] = df['Count'].astype(int)
        return df

def run_command(command):
    if platform.system() == "Windows":
        os.system(command.replace("/", "\\"))
    else:
        os.system(command)

def num_vehicles(img_path):
    run_command(f"python ../yolov5/detect.py --weights ../best.pt --img 640 --conf 0.4 --save-csv --source {img_path}")
    latest_exp = sorted(Path('../yolov5/runs/detect').glob('exp*'), key=os.path.getmtime)[-1]
    # For counting vehicles in image
    filenames = [f for f in os.listdir(latest_exp) if f.endswith('.csv')]
    count = vehicle_count(f"{latest_exp}/{filenames[0]}", 'Image')

    # For detecting vehicles in Image
    detect_vehicle_file = [f for f in os.listdir(latest_exp) if f.endswith(('.jpeg', '.jpg'))][0]
    print("detect_vehicle_count", detect_vehicle_file, count)
    return count, f"{latest_exp}/{detect_vehicle_file}"

def ambulance_detection(img_path):
    run_command(f"python ../yolov5/detect.py --weights ../er_best.pt --img 640 --conf 0.4 --save-csv --source {img_path}")
    latest_exp = sorted(Path('../yolov5/runs/detect').glob('exp*'), key=os.path.getmtime)[-1]
    filenames = [f for f in os.listdir(latest_exp) if f.endswith('.csv')]
    if len(filenames) == 0:
        print("No Ambulance Detected")
        return 0, None
    
    count = vehicle_count(f"{latest_exp}/{filenames[0]}", 'Image')
    ambulance_detect_vehicle_file = [f for f in os.listdir(latest_exp) if f.endswith(('.jpeg', '.jpg'))][0]
    print("Ambulance detect_vehicle_count", ambulance_detect_vehicle_file, count)
    return count, f"{latest_exp}/{ambulance_detect_vehicle_file}"

# Example usage
if __name__ == "__main__":
    img_path = "./uploads/signal_1_20250118_040041.jpg"
    vehicle_count, vehicle_image = num_vehicles(img_path)
    print(f"Vehicle count: {vehicle_count}, Vehicle image: {vehicle_image}")

    ambulance_count, ambulance_image = ambulance_detection(img_path)
    print(f"Ambulance count: {ambulance_count}, Ambulance image: {ambulance_image}")
