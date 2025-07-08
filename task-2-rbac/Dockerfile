# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /code

# Copy the dependency file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
# This single command should copy everything, including the new alembic/versions dir
COPY . .

# Expose the port the app will run on
EXPOSE 8000