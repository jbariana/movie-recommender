# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy all your project files
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port for Render
EXPOSE 10000

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=10000

# Start the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=10000"]
