<div align="center">
  <h1>🤖 Follower Bot</h1>
  <p><em><b>An automated bot for following GitHub users.</b></em></p>
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

## 🚀 Usage

### 🔧 Prerequisites

> [!Warning]
> **♻ Do not set the request frequency too high when modifying configurations. Excessive requests may trigger GitHub restrictions (⛔ including potential IP blocking, rate limiting, or account suspension. Proceed with caution!!!).**

1. Clone the repository.
2. Generate a GitHub personal access token with at least the `user:follow` scope. See: [Managing Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
3. Save the token to the `GITHUB_TOKEN` variable in the `.env.local` file.
4. Modify other configurations in the `.env` file as needed.

### 🪟 Run on Windows

> [!Note]
> If using a custom Python environment, update the `<executable/>` path in [follower-bot-service.xml](./follower-bot-service.xml).

Required tools: [Rye](https://github.com/astral-sh/rye) (Python environment manager) + [WinSW](https://github.com/winsw/winsw) (Windows service manager).

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

### 🐋 Run with Docker

```shell
# Build the Docker image
docker build -t follower-bot .
# Run the Docker container
docker run -d --name follower-bot -v "logs:/app/logs" -v "data:/app/data" follower-bot
# Stop the container
docker stop follower-bot
```

## 🔗 References

[OfficialCodeVoyage/Github_Automation_Follower_Bot](https://github.com/OfficialCodeVoyage/Github_Automation_Follower_Bot)