# Use the official Python image as the base image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install the application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the working directory
COPY . .

# Install Gunicorn
RUN pip install gunicorn

# Expose the port on which Gunicorn will run
EXPOSE 8000

# Define the entry point for the container to run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "manage:app"]
