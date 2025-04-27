FROM python:3.10-slim

# Install necessary build dependencies
RUN apt-get update && apt-get install -y build-essential gcc

WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the command to run your app
CMD ["python", "app.py"]
