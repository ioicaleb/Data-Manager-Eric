# Use an official, lightweight Python runtime image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /src

# Install system dependencies required for Flet's system backend
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker's build cache layers
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the default Flet web port
EXPOSE 8502

# Run the app as a web service bound to all network interfaces
CMD ["python", "main.py"]