# Use Python 3.10.12
FROM python:3.10.12-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Expose port for Flask (health check)
EXPOSE 8080

# Run bot
CMD ["python", "bot.py"]
