# Use a clean Python base image
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory to the absolute project root folder
WORKDIR /app
ENV PYTHONPATH="/app:/app/src:${PYTHONPATH}"

# Install curl, gnupg, and core system dependencies for headless browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unzip \
    git \
    chromium \
    chromium-driver \
    firefox-esr \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libasound2 \
    libx11-xcb1 \
    libgbm1 \
    libnss3 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver explicitly (firefox-esr has no matching apt driver package,
# so it must be downloaded and pinned manually — unlike chromium-driver above)
ARG GECKODRIVER_VERSION=0.37.1
RUN curl -sSL "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    | tar xz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver

# Find the exact installed path for WebDrivers and add them to the system PATH environment
ENV PATH="/usr/bin:/usr/local/bin:${PATH}"

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt

# Copy the entire repository into /app
COPY . .

# Expose your Uvicorn web server port
EXPOSE 8000

# Launch Uvicorn using the explicit src.main:app dot-notation path
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]