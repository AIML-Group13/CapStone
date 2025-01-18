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

def Ambulance_Detection(img_path):
    !python /content/yolov5/detect.py --weights /content/drive/MyDrive/Results/ER/weights/best.pt --img 640 --conf 0.4 --save-csv --source "{img_path}"
    latest_exp = sorted(Path('/content/yolov5/runs/detect').glob('exp*'), key=os.path.getmtime)[-1]
    filenames = [f for f in os.listdir(latest_exp) if f.endswith(('.jpeg', '.jpg'))][0]
    print(filenames)
    return f"{latest_exp}/{filenames}"
