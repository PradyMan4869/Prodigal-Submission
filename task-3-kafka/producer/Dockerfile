# Use an official lightweight Python image.
FROM python:3.9-slim

# --- THIS IS THE NEW PART ---
# Update package lists and install curl
# apt-get clean removes unnecessary files to keep the image small
RUN apt-get update && apt-get install -y curl && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the dependency file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Expose the port the app will run on and run the application
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]