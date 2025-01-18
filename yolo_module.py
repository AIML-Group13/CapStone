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
