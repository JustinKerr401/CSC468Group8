# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app and other necessary files
COPY . .

# Expose the Flask API port
EXPOSE 5000

# Run the Flask app
CMD ["python", "stock_monitor.py"]