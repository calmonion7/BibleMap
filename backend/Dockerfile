# 빌드 컨텍스트 = 레포 루트(compose) — data/ 를 이미지에 굽는다(롤백 때 데이터도 함께 되돌아간다).
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app/ ./app/
COPY data/ ./data/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
