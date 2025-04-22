FROM python:slim

RUN pip install uv

WORKDIR /app
COPY . .
RUN uv pip install --no-cache --system -r requirements.lock

CMD ["python", "-m", "follower_bot.bot"]
