FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face Spaces run as a non-root user; keep model/cache writable under /tmp.
ENV HF_HOME=/tmp/hf \
    FASTEMBED_CACHE_PATH=/tmp/fastembed_cache \
    LLM_ENGINE=gemini \
    GEMINI_MODEL=gemini-2.5-flash \
    QDRANT_URL=:memory: \
    TOP_K=6

# GEMINI_API_KEY is provided as a Space secret, not baked into the image.
EXPOSE 7860
CMD ["uvicorn", "rag.api:app", "--host", "0.0.0.0", "--port", "7860"]
