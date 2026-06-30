FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default: run a quick smoke test
CMD ["python", "test_apis.py"]

# Usage:
#   docker build -t ai-freedom-island .
#   docker run --env-file .env ai-freedom-island python run_with_env.py --world docker_test --model qwen-turbo --days 1
#   docker run --env-file .env -p 8501:8501 ai-freedom-island streamlit run dashboard.py --server.address 0.0.0.0
