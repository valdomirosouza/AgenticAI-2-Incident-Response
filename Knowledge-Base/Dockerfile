FROM python:3.12-slim
RUN groupadd -r app && useradd -r -g app -m app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
# Download model to a fixed path so the app user can read it at runtime
ENV HF_HOME=/app/.hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    && chown -R app:app /app/.hf_cache
# Disable hub network access at runtime — model is fully cached above
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
COPY --chown=app:app app ./app
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
