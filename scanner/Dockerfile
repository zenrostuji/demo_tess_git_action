FROM python:3.10-slim

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		ca-certificates \
		fonts-unifont \
		fonts-liberation \
		libasound2 \
		libatk1.0-0 \
		libatk-bridge2.0-0 \
		libatspi2.0-0 \
		libdrm2 \
		libgbm1 \
		libglib2.0-0 \
		libgtk-3-0 \
		libnss3 \
		libnspr4 \
		libx11-6 \
		libx11-xcb1 \
		libxcb-dri3-0 \
		libxcomposite1 \
		libxcursor1 \
		libxdamage1 \
		libxfixes3 \
		libxi6 \
		libxrandr2 \
		libxshmfence1 \
		libxss1 \
		libxtst6 \
		wget \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
COPY . .
CMD ["python", "scanner.py", "serve"]