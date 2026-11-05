# Build from the repo root: docker compose -f deploy/virtual-office/compose.yaml build
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 office
WORKDIR /app
COPY deploy/virtual-office/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY deploy/virtual-office/server.py ./
COPY deploy/virtual-office/office ./office
COPY deploy/virtual-office/static ./static
COPY deploy/virtual-office/data ./data
# A new named volume copies this dir's owner; without it /data is root-owned and the server can't write.
RUN mkdir /data && chown office:office /data
USER office
ENV DATA_DIR=/data PORT=8080
EXPOSE 8080
CMD ["python", "server.py"]
