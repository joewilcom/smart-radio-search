# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Flask knows which app to run
ENV FLASK_APP=app.py

# Optional: prevent bytecode .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Optional: unbuffered logs (helpful for Koyeb logging)
ENV PYTHONUNBUFFERED=1

# Expose the port Koyeb will use
EXPOSE 8080

# Start the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
