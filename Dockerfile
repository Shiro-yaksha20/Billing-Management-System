# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We install xvfb if we ever want to run GUI tests inside docker,
# but mostly just deps here.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the working directory contents into the container at /app
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV QT_QPA_PLATFORM=offscreen

# Command to run tests by default, or the app
CMD ["python", "main.py"]
