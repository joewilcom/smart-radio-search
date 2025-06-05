FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy everything from the repo into the container's /app folder
COPY . .

# Install dependencies from the root-level requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Flask
ENV FLASK_APP=backend/app.py
ENV FLASK_RUN_PORT=8080
ENV OPENAI_API_KEY=""

# Expose port for Fly.io
EXPOSE 8080

# Run the app
CMD ["flask", "run", "--host=0.0.0.0"]
