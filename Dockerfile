FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for SQLite database
RUN mkdir -p /data

# Expose Streamlit port
EXPOSE 8000

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0", "--server.headless=true"]
