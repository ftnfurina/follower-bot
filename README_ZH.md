<div align="center">
  <h1>🤖 Follower Bot</h1>
  <p><em><b>一个自动关注/回关 GitHub 用户的机器人。</b></em></p>
  <img src="https://api.visitorbadge.io/api/combined?path=https://github.com/ftnfurina/follower-bot&label=VISITORS&style=flat-square&countColor=%23f3722c" alt="visitors"/>
  <div>
    <a href="./README_ZH.md">中文</a> |
    <a href="./README.md">English</a>
  </div>
</div>

## 🌟 特点

1. **全自动化** - 无需人工干预。
2. **状态管理** - 使用持久化存储保证程序重启后可以继续运行。
3. **多种运行方式** - 包括 Windows 服务和 Docker 容器等。

## 🎯 功能

1. 同步全部关注/追随的用户。
2. 自动回关那些关注你的用户。
3. 自动取关那些取关你的用户。
4. 按条件自动取关/关注用户。
5. 邮件通知统计/异常信息。

## 🚀 使用方法

### 🔧 前置条件

> [!Warning]
> **♻ 当你修改配置时，请不要将请求频率设置得过高，否则可能会被 GitHub 限制（⛔ 账号封禁也是有可能的，请谨慎操作！！！）。**

1. 克隆代码库。
2. 获取 GitHub 个人访问令牌，至少包含 `user:follow` 作用域，参考：[管理个人访问令牌](https://docs.github.com/zh/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)。
3. 保存令牌到 `.env.local` 文件的 `GITHUB_TOKEN` 环境变量中。
4. 按需求修改 `.env` 文件中的其他配置项。
5. 按需求修改 `bots.yaml` 文件中的机器人配置。

### 📦 数据存储

修改 `.env` 文件中的 `DATABASE.URL` 配置项，支持以下数据库：

#### 🐬 MySQL（推荐）

```shell
# 安装依赖
rye add pymysql
```


```ini
DATABASE.URL = mysql+pymysql://username:password@localhost/follower_bot
```

#### 🪶 SQLite（默认）

```ini
DATABASE.URL = sqlite:///data/store.db
```

### 📬 邮件通知（可选）

在 `.env.local` 文件中配置邮件通知相关配置项，即可开启邮件通知功能。

```ini
# 邮件配置
# SMTP 服务器地址
EMAIL.SMTP_SERVER = smtp.gmail.com
# SMTP 服务器端口
EMAIL.SMTP_PORT = 587
# SMTP 用户名
EMAIL.SMTP_USERNAME = "username"
# SMTP 密码
EMAIL.SMTP_PASSWORD = "password"
# 发件人邮箱地址
EMAIL.SENDER_EMAIL = "sender@example.com"
# 收件人邮箱地址列表
EMAIL.RECIPIENT_EMAILS = ["recipient@example.com"]
```

### 🏃 运行方式

#### 🪟 Windows 上运行

> [!Note]
> 若是使用其他 Python 环境，请自行修改 [follower-bot-service.xml](./follower-bot-service.xml) 文件中 &lt;executable/&gt; 配置项的 Python 路径。

```shell
# 生成虚拟环境并安装依赖
rye sync
# WinSW 配置文件参考: https://github.com/winsw/winsw/blob/v3/docs/xml-config-file.md
# 注册服务到 Windows
follower-bot-service.exe install
# 启动服务
follower-bot-service.exe start
# 停止服务
follower-bot-service.exe stop
# 卸载服务
follower-bot-service.exe uninstall
```

#### 🐋 Docker 上运行

```shell
# 构建 Docker 镜像
docker build -t follower-bot .
# 运行 Docker 容器
docker run -d --name follower-bot -v "logs:/app/logs" -v "data:/app/data" follower-bot
# 停止 Docker 容器
docker stop follower-bot
```

## 🧪 开发调试

虚拟环境调试（推荐）：

```shell
# 安装依赖
rye sync
# 运行/调试程序
rye run start [-h]
```

本机环境调试：

```shell
# 安装依赖
pip install --no-cache -r requirements.lock
# 运行/调试程序
python -m follower_bot.bot [-h]
```

## 📦 相关工具

+ [Rye](https://github.com/astral-sh/rye)：Python 环境管理工具
+ [WinSW](https://github.com/winsw/winsw)：Windows 服务管理工具
+ [Github API](https://docs.github.com/zh/rest)：GitHub API 文档
+ [pydantic](https://docs.pydantic.dev/latest/)：Python 数据校验
+ [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#settings-management)：配置管理
+ [loguru](https://github.com/Delgan/loguru)：Python 日志库
+ [loguru-config](https://github.com/erezinman/loguru-config)：loguru 日志配置
+ [requests](https://requests.readthedocs.io/en/latest/)：Python HTTP 客户端库
+ [rate-keeper](https://github.com/ftnfurina/rate-keeper)：API 速率维持装饰器
+ [apscheduler](https://github.com/agronholm/apscheduler)：Python 任务调度库
+ [sqlmodel](https://sqlmodel.tiangolo.com/)：Python SQL ORM 库
+ [pyyaml](https://github.com/yaml/pyyaml): Python YAML 解析库

## 🔗 参考链接

[OfficialCodeVoyage/Github_Automation_Follower_Bot](https://github.com/OfficialCodeVoyage/Github_Automation_Follower_Bot)
