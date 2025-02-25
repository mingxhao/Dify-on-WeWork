import time
import traceback

import aiohttp
import redis
import uvicorn
import xmltodict
from fastapi import FastAPI, HTTPException, Request
from fastapi.logger import logger
from fastapi.responses import Response
from pydantic import BaseModel

from WxCrypt.WXBizMsgCrypt3 import WXBizMsgCrypt
from tasks import process_ai_request

app = FastAPI()

# Redis 连接
redis_client = redis.Redis(host='localhost', port=6379, db=0)
redis_client.flushdb()
# Dify API 的 URL（替换为你的实际 URL）
DIFY_API_URL = 'http://xxx/v1/chat-messages'
DIFY_API_KEY = 'app-xxxx'

# 企业微信被动消息解密配置
wx_Token = 'xxxx'
wx_EncodingAESKey = 'xxxx'
# 企业id
corp_id = 'xxxx'
# 企业应用secret
corp_secret = 'xxx-xxx'
# 企业微信应用请求的token
wx_token_key = 'wechat_access_token'

try:
    wxcpt = WXBizMsgCrypt(wx_Token, wx_EncodingAESKey, corp_id)
except Exception as e:
    logger.error(f"初始化WXBizMsgCrypt失败: {str(e)}")
    raise


class UserMessage(BaseModel):
    to_user_name: str
    from_user_name: str
    create_time: str
    msg_type: str
    content: str
    msg_id: str
    agent_id: str


async def get_access_token():
    """
    获取企业微信的 access_token
    """
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={corp_secret}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get("errcode") != 0:
                raise HTTPException(status_code=500, detail="Failed to get access_token")
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 7200)
            # 缓存 access_token，设置过期时间（提前 5 分钟过期）
            redis_client.set(wx_token_key, access_token, ex=expires_in - 300)
            return access_token


async def refresh_access_token():
    """
    刷新 access_token
    """
    return await get_access_token()


async def ensure_access_token():
    """
    确保 access_token 有效
    """
    access_token = redis_client.get(wx_token_key)
    if not access_token:
        access_token = await refresh_access_token()
    else:
        access_token = access_token.decode('utf-8')
    return access_token


def DecryptMsg(body, msg_signature, timestamp, nonce):
    ret, sMsg = wxcpt.DecryptMsg(body, msg_signature, timestamp, nonce)
    if ret != 0:
        logger.error(f"消息解密失败，错误码: {ret}")
        return None

    logger.info(f"解密后的原始 XML 内容: {sMsg}")
    xml_dict = xmltodict.parse(sMsg)
    logger.info(f"解析后的 XML 字典: {xml_dict}")

    xml_content = xml_dict['xml']
    decrypt_msg = UserMessage(
        to_user_name=xml_content.get('ToUserName'),
        from_user_name=xml_content.get('FromUserName'),
        create_time=xml_content.get('CreateTime'),
        msg_type=xml_content.get('MsgType'),
        content=xml_content.get('Content'),
        msg_id=xml_content.get('MsgId'),
        agent_id=xml_content.get('AgentID')
    )

    return decrypt_msg


def EncryptMsg(userMessage: UserMessage, nonce):
    # 加密消息
    reply_msg = f"""
                <xml>
                    <ToUserName><![CDATA[{userMessage.from_user_name}]]></ToUserName>
                    <FromUserName><![CDATA[{userMessage.to_user_name}]]></FromUserName>
                    <CreateTime>{userMessage.create_time}</CreateTime>
                    <MsgType><![CDATA[text]]></MsgType>
                    <Content><![CDATA[{userMessage.content}]]></Content>
                    <MsgId>{userMessage.msg_id}</MsgId>
                    <AgentID>{userMessage.agent_id}</AgentID>
                </xml>
                """
    ret, encrypted_msg = wxcpt.EncryptMsg(reply_msg, nonce, userMessage.create_time)
    if ret != 0:
        logger.error(f"消息加密失败，错误码: {ret}")
        raise HTTPException(status_code=500, detail="消息加密失败")
    return encrypted_msg


@app.post("/callback")
async def receive_message(request: Request):
    try:
        if not await ensure_access_token():
            raise HTTPException(status_code=500, detail="Failed to get access_token")

        # 获取请求参数
        body = await request.body()
        msg_signature = request.query_params.get("msg_signature")
        timestamp = request.query_params.get("timestamp")
        nonce = request.query_params.get("nonce")

        if not all([msg_signature, timestamp, nonce]):
            raise HTTPException(status_code=400, detail="缺少必要的参数")
        res_message: UserMessage = DecryptMsg(body, msg_signature, timestamp, nonce)

        access_token = redis_client.get(wx_token_key).decode('utf-8')

        # 将 AI 请求放入后台处理
        process_ai_request.delay(
            res_message.from_user_name,
            res_message.content,
            res_message.msg_id,
            res_message.agent_id,
            res_message.to_user_name
        )

        req_message = UserMessage(
            to_user_name=res_message.from_user_name,
            from_user_name=res_message.to_user_name,
            create_time=str(int(time.time())),
            msg_type='text',
            content='正在搜索中。。。',
            msg_id=res_message.msg_id,
            agent_id=res_message.agent_id
        )
        return Response(content=EncryptMsg(req_message, nonce), media_type="application/xml")

    except Exception as e:
        logger.error(f"处理消息时发生错误: {str(e)}")
        logger.error("详细错误信息如下：")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="服务器内部错误")


@app.get("/callback")
async def verify_url(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    try:
        logger.info(f"收到验证请求: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}")
        ret, DecryptEchoStr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
        if ret == 0:
            logger.info("URL验证成功")
            return Response(content=DecryptEchoStr)
        else:
            logger.error(f"URL验证失败，错误码: {ret}")
            raise HTTPException(status_code=400, detail="验证失败")
    except Exception as e:
        logger.error(f"验证过程发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/callback")
async def verify_callback_url(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    try:
        verification_result, decrypted_echo_str = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
        if verification_result == 0:
            return Response(content=decrypted_echo_str)
        else:
            logger.error(f"URL验证失败，错误码: {verification_result}")
            raise HTTPException(status_code=400, detail="URL验证失败")
    except Exception as e:
        logger.error(f"验证过程发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
