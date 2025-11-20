FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=2

# 필요한 라이브러리 직접 설치
RUN pip install --no-cache-dir \
        flask \
        gunicorn \
        gevent \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# 앱 복사
COPY . .

# 비루트 사용자 실행
RUN useradd appuser
USER appuser

EXPOSE 8080

# Gunicorn workers = CPU * 2 + 1
CMD ["sh", "-c", "gunicorn -w $(expr $(nproc) \\* 2 + 1) -k gevent -b 0.0.0.0:8080 app:app"]
