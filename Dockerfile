# Use the official Python image as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app to the container
COPY app.py .

# Expose the port on which Flask app will run
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
