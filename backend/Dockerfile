# Use Python as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend code to the container
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=stock_monitor.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

# Expose the port Flask will run on
EXPOSE 5000

# Start the Flask application
CMD ["flask", "run"]