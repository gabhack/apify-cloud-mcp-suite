FROM python:3.12-slim
WORKDIR /app
COPY src/ ./src/
COPY data/ ./data/
ENV CLOUDCERT_DATA_DIR=/app/data
EXPOSE 8080
CMD ["python3", "src/server.py"]
