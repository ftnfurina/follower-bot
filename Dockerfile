FROM python:slim

WORKDIR /app
COPY . .
RUN pip install --no-cache -r requirements.lock

CMD ["python", "-m", "follower_bot.bot"]
