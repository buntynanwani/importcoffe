FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /Backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

COPY reqs.txt /Backend/reqs.txt
RUN pip install --no-cache-dir -r /Backend/reqs.txt

FROM python:3.13-slim

# Install netcat for wait loop and bash
RUN apt-get update && apt-get install -y --no-install-recommends \
	netcat-openbsd \
	bash \
	sqlite3 \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /Backend

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy project files from the build context (compose sets context to ./Backend)
COPY . /Backend/

RUN mkdir -p /Backend/code/static /Backend/code/staticfiles

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

RUN sed -i 's/\r$//' /Backend/script.sh && chmod +x /Backend/script.sh

ENTRYPOINT ["/bin/bash", "/Backend/script.sh"]