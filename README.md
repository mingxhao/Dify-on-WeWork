# Dify-On-WeWork

Dify-On-WeWork 是一个用于对接 Dify 和企业微信应用的中间件，实现自动化转发 AI 消息的功能。通过本地化部署 Python
服务，将企业微信接收到的消息转发给 Dify，并将 Dify 的回复发送回企业微信。

## 功能特性

- **企业微信消息接收与解密**：支持接收企业微信的加密消息，并解密处理。
- **Dify 消息转发**：将企业微信的消息转发给 Dify，并获取 AI 回复。
- **异步任务处理**：使用 Celery 异步处理消息，提高系统响应速度。
- **Redis 缓存**：缓存企业微信的 `access_token` 和用户会话 ID，提升性能。

## 文件目录结构

|-- WxCrypt
|   |-- WXBizMsgCrypt3.py
|   `-- ierror.py
|-- dify-on-wework-start.sh
|-- dify-on-wework-stop.sh
|-- main.py
|-- requirements.txt
|-- tasks.py

## 快速开始

### 环境要求

- Python 3.8+
- Redis
- Celery
- 企业微信应用（需配置 Token 和 EncodingAESKey）
- Dify API（需配置 API Key 和 URL）

### 安装步骤

1. **克隆仓库**

    ```bash
    git clone https://github.com/yourusername/dify-on-wework.git
    cd dify-on-wework
    ```

2. **安装依赖**

    ```bash
    pip install -r requirements.txt
    ```

3. **配置 Redis**

   确保 Redis 服务已启动，并监听默认端口 `6379`。

4. **下载 WxCrypt 库**

   从企业微信官网下载 WxCrypt 库，并解压到 `WxCrypt` 目录：

    ```bash
    wget https://dldir1.qq.com/wework/wwopen/file/weworkapi_python.tar.bzip2
    tar -xvjf weworkapi_python.tar.bzip2 -C WxCrypt
    ```

5. **修改配置文件**

    - **`main.py`**：修改以下配置：

        ```python
        wx_Token = 'your_wx_token'  # 企业微信应用的 Token
        wx_EncodingAESKey = 'your_encoding_aes_key'  # 企业微信应用的 EncodingAESKey
        corp_id = 'your_corp_id'  # 企业 ID
        corp_secret = 'your_corp_secret'  # 企业应用 Secret
        ```

    - **`tasks.py`**：修改以下配置：

        ```python
        DIFY_API_URL = 'http://your_dify_url/v1/chat-messages'  # Dify API URL
        DIFY_API_KEY = 'your_dify_api_key'  # Dify API Key
        ```

6. **启动服务**

   运行启动脚本：

    ```bash
    chmod +x dify-on-wework-start.sh
    ./dify-on-wework-start.sh
    ```

7. **停止服务**

   运行停止脚本：

    ```bash
    chmod +x dify-on-wework-stop.sh
    ./dify-on-wework-stop.sh
    ```

## 配置说明

### 企业微信配置

1. 登录企业微信管理后台，进入“应用管理”。
2. 创建或选择已有应用，获取以下信息：
    - **Token**：用于消息验证。
    - **EncodingAESKey**：用于消息加密解密。
    - **企业 ID**：企业微信的唯一标识。
    - **应用 Secret**：用于获取 `access_token`。

### Dify 配置

1. 登录 Dify 控制台，进入“API 设置”。
2. 获取以下信息：
    - **API URL**：Dify 的 API 地址。
    - **API Key**：用于调用 Dify API 的密钥。

## 使用说明

1. **部署服务**：按照安装步骤启动服务。
2. **配置企业微信回调**：
    - 在企业微信管理后台，设置回调 URL 为 `http://your_server_ip/callback`。
    - 配置 Token 和 EncodingAESKey 与 `main.py` 中的值一致。
3. **发送消息**：在企业微信中发送消息，服务会自动将消息转发给 Dify，并将 AI 回复返回。

## 日志查看

- **Uvicorn 日志**：`/var/log/dify_on_wework_main.log`
- **Uvicorn 错误日志**：`/var/log/dify_on_wework_main_error.log`
- **Celery 日志**：`/var/log/dify_on_wework_celery.log`
- **Celery 错误日志**：`/var/log/dify_on_wework_celery_error.log`

## 许可证

本项目采用 [GPL 3.0 许可证](LICENSE)。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系

如有问题，请联系：

- 邮箱：[zhaominghao@neusoft.edu.cn](mailto:zhaominghao@neusoft.edu.cn)
- GitHub: [mingxhao](https://github.com/mingxhao)

## 致谢

- 感谢 [企业微信](https://work.weixin.qq.com/) 提供的消息加解密库。
- 感谢 [Dify](https://dify.ai/) 提供的 AI 能力支持。

希望这个 `README.md` 能帮助你清晰地展示项目！如果有其他需求，可以随时补充或调整。
