# Build from the repo root: docker compose -f deploy/teams-bot/compose.yaml build
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 bot
WORKDIR /app
COPY deploy/teams-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY plugins /opt/ai-team-plugins/plugins
COPY deploy/teams-bot/app.py deploy/teams-bot/botlogic.py ./
# A new named volume copies this dir's owner; without it /data is root-owned and the bot can't write.
RUN mkdir /data && chown bot:bot /data
USER bot
ENV DATA_DIR=/data CLAUDE_CONFIG_DIR=/data/claude CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
EXPOSE 3978
CMD ["python", "app.py"]
