FROM python:3.11-slim

WORKDIR /app

# No credentials are baked into the image — MONID_API_KEY is supplied at runtime.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Directory checks (Glama etc.) only need the process to start and answer
# introspection requests, so no runtime dependency beyond fastmcp is required.
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio

CMD ["python", "server.py"]
