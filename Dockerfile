FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts/write_build_info.py ./scripts/write_build_info.py

ARG APP_GIT_SHA=unknown

ENV EXPENSAS_DATA_DIR=/expensas-data
ENV PYTHONPATH=/app

VOLUME ["/expensas-data"]

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--browser.gatherUsageStats=false"]
