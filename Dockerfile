# Use a base Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for OpenCV and git
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .
COPY ./yolov5/requirements.txt ./yolov5/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r ./yolov5/requirements.txt

# Copy app files into the container
COPY . .

# Set the environment variable (Cloud Run uses this to configure the service)
ENV PORT=8000

# Expose the port that FastAPI runs on
EXPOSE 8000

# Run the FastAPI app
CMD ["sh", "-c", "cd TrafficSystem && python main.py"]
