# Use the official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose default Chainlit port
EXPOSE 8000

# Run the Chainlit app
CMD ["chainlit", "run", "app.py", "--port", "8000", "--host", "0.0.0.0"]
