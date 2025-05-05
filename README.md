<div align="center">
  <h1>🤖 Follower Bot</h1>
  <p><em><b>An automated bot for following and reciprocating follows with GitHub users.</b></em></p>
  <img src="https://api.visitorbadge.io/api/combined?path=https://github.com/ftnfurina/follower-bot&label=VISITORS&style=flat-square&countColor=%23f3722c" alt="visitors"/>
  <div>
    <a href="./README_ZH.md">中文</a> |
    <a href="./README.md">English</a>
  </div>
</div>

## 🌟 Features

1. **Full Automation** - No manual intervention required.
2. **State Management** - Uses persistent storage to ensure operations resume after restarts.
3. **Multiple Deployment Options** - Supports Windows service, Docker container, and more.

## 🎯 Function

1. Sync all followers/following.
2. Auto follow user who follow you.
3. Auto unfollow user who unfollow you.
4. Condition based auto unfollow/follow.
5. Email notifications for statistics and exception information.

## 🚀 Usage

### 🔧 Prerequisites

> [!Warning]
> **♻ Do not set the request frequency too high when modifying configurations. Excessive requests may trigger GitHub restrictions (⛔ including potential IP blocking, rate limiting, or account suspension. Proceed with caution!!!).**

1. Clone the repository.
2. Generate a GitHub personal access token with at least the `user:follow` scope. See: [Managing Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
3. Save the token to the `GITHUB_TOKEN` variable in the `.env.local` file.
4. Modify other configurations in the `.env` file as needed.
5. Modify the bot configurations in the `bots.yaml` file as needed.

### 📦 Data Storage

Modify the `DATABASE.URL` configuration item in the `.env` file to support the following databases:

#### 🐬 MySQL (Recommended)

```shell
# Install dependencies
rye add pymysql
```

```ini
DATABASE.URL = mysql+pymysql://username:password@localhost/follower_bot
```

#### 🪶 SQLite (Default)


```ini
DATABASE.URL = sqlite:///data/store.db
```

### 📬 Email Notifications (Optional)

Configure the relevant settings in the `.env.local` file to enable the email notification feature.

```ini
# Email configuration
# SMTP server
EMAIL.SMTP_SERVER = smtp.gmail.com
# SMTP port
EMAIL.SMTP_PORT = 587
# SMTP username
EMAIL.SMTP_USERNAME = "username"
# SMTP password
EMAIL.SMTP_PASSWORD = "password"
# Sender email address
EMAIL.SENDER_EMAIL = "sender@example.com"
# List of recipient email addresses
EMAIL.RECIPIENT_EMAILS = ["recipient@example.com"]
```

### 🏃‍♂️ Run the Bot

#### 🪟 Run on Windows

> [!Note]
> If using a custom Python environment, update the &lt;executable/&gt; path in [follower-bot-service.xml](./follower-bot-service.xml).

```shell
# Create a virtual environment and install dependencies
rye sync
# WinSW config reference: https://github.com/winsw/winsw/blob/v3/docs/xml-config-file.md
# Register as a Windows service
follower-bot-service.exe install
# Start the service
follower-bot-service.exe start
# Stop the service
follower-bot-service.exe stop
# Uninstall the service
follower-bot-service.exe uninstall
```

#### 🐋 Run with Docker

```shell
# Build the Docker image
docker build -t follower-bot .
# Run the Docker container
docker run -d --name follower-bot -v "logs:/app/logs" -v "data:/app/data" follower-bot
# Stop the container
docker stop follower-bot
```

## 🧪 Development and Debugging

Debugging in a virtual environment (recommended):

```shell
# Install dependencies
rye sync
# Run/Debug the bot
rye run start [-h]
```

Debugging in a local environment:

```shell
# Install dependencies
pip install --no-cache -r requirements.lock
# Run/Debug the bot
python -m follower_bot.bot [-h]
```

## 📦 Related Tools

+ [Rye](https://github.com/astral-sh/rye): Python environment manager
+ [WinSW](https://github.com/winsw/winsw): Windows service manager
+ [Github API](https://docs.github.com/en/rest): GitHub API reference
+ [pydantic](https://docs.pydantic.dev/latest/): Python data validation
+ [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#settings-management): Settings management for Pydantic
+ [loguru](https://github.com/Delgan/loguru): Python logging library
+ [loguru-config](https://github.com/erezinman/loguru-config): Configuration for loguru
+ [requests](https://requests.readthedocs.io/en/latest/): HTTP library for Python
+ [rate-keeper](https://github.com/ftnfurina/rate-keeper): API Rate Keeper Decorator
+ [apscheduler](https://github.com/agronholm/apscheduler): Task scheduling library for Python
+ [sqlmodel](https://sqlmodel.tiangolo.com/): SQL and ORM library for Python
+ [pyyaml](https://github.com/yaml/pyyaml): YAML parser and emitter for Python

## 🔗 References

[OfficialCodeVoyage/Github_Automation_Follower_Bot](https://github.com/OfficialCodeVoyage/Github_Automation_Follower_Bot)
