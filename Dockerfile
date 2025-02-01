# Use a base Python image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy app files into the container
COPY best-model.torchscript requirements.txt app.py /app/ 

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable (Cloud Run uses this to configure the port)
ENV PORT=8080

# Expose the port that Gradio will run on
EXPOSE 8080

# Command to run the app
CMD ["python", "app.py"]
