FROM python:3.9-slim

# Install system dependencies required by PyAV and FFmpeg
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswresample-dev \
    libswscale-dev \
    libavfilter-dev

# Set the working directory
WORKDIR /app

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Command to run the bot
CMD ["python", "main.py"]
