# CareFlow Nexus AI Agents - Hugging Face Deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/config /app/logs

# Create a startup script that handles secrets
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "=== CareFlow Nexus Agent Server - Hugging Face Deployment ==="\n\
\n\
# Write Firebase service account from secret to file\n\
if [ -n "$FIREBASE_SERVICE_ACCOUNT_JSON" ]; then\n\
  echo "✓ Writing Firebase service account to file..."\n\
  echo "$FIREBASE_SERVICE_ACCOUNT_JSON" > /app/config/serviceAccountKey.json\n\
  export FIREBASE_SERVICE_ACCOUNT_PATH="/app/config/serviceAccountKey.json"\n\
else\n\
  echo "⚠ Warning: FIREBASE_SERVICE_ACCOUNT_JSON not set"\n\
fi\n\
\n\
# Set default values for optional env vars\n\
export GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.0-flash-exp}"\n\
export RULE_WEIGHT="${RULE_WEIGHT:-0.5}"\n\
export AI_WEIGHT="${AI_WEIGHT:-0.5}"\n\
export AGENT_SERVER_PORT="${PORT:-7860}"\n\
export ENVIRONMENT="${ENVIRONMENT:-production}"\n\
export LOG_LEVEL="${LOG_LEVEL:-INFO}"\n\
\n\
echo "✓ Configuration loaded"\n\
echo "  Port: $AGENT_SERVER_PORT"\n\
echo "  Model: $GEMINI_MODEL"\n\
echo "  Weights: Rule=$RULE_WEIGHT, AI=$AI_WEIGHT"\n\
echo ""\n\
echo "Starting Agent Server..."\n\
echo ""\n\
\n\
# Start the agent server\n\
exec uvicorn agent_server:app --host 0.0.0.0 --port $AGENT_SERVER_PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set environment variables with defaults
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=7860

# Expose port (Hugging Face uses 7860 by default)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

# Run startup script
CMD ["/app/start.sh"]
