# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt && \
	apt-get update && \
	apt-get install -y npm && \
	npm install -g prettier@3.4.2

# Copy application code
COPY main.py .
COPY functions.py .
COPY llm_parser.py .

RUN mkdir data/

# Expose port 8000
EXPOSE 8000

# Run the API when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]