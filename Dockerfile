# Use an official Python runtime as a parent image
FROM python:3.12.4

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the app runs on
EXPOSE 8000

# Define the command to run the application
CMD ["fastapi", "dev", "main.py", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]

