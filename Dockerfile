
# Use a Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY src .

# Expose the port that the application will run on (adjust if your app uses a different port)
EXPOSE 8000

# Define the command to run the application
CMD ["python", "-m", "backend.main"] # Assuming your main entry point is in src/backend/main.py
