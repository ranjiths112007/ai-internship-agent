FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install chromium || true

COPY . .

EXPOSE 8000

ENV APP_ENV=production
ENV DATABASE_URL=sqlite:///./data/internships.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
