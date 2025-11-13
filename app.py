# app.py
import os
import io
import random
import requests
import numpy as np
from PIL import Image
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage
)

app = Flask(__name__)

# 從環境變數讀取 Line token
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise Exception("請先設定 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE BOT 正常運作中"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
print("收到 LINE webhook!")  
    print("Body:", body) 
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 使用者輸入「開始」或「預測」時觸發
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_text = event.message.text.strip()

    if user_text in ["開始", "預測"]:
        reply_text = "請輸入路線趨勢圖"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    else:
        reply_text = "請輸入「開始」或「預測」來開始分析"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

# 使用者上傳圖片時觸發
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # 取得圖片內容
    message_content = line_bot_api.get_message_content(event.message.id)
    image_bytes = io.BytesIO(message_content.content)
    image = Image.open(image_bytes).convert("RGB")

    # 將圖片轉成 numpy 陣列分析顏色
    img_np = np.array(image)
    red = img_np[:, :, 0].astype(int)
    green = img_np[:, :, 1].astype(int)
    blue = img_np[:, :, 2].astype(int)

    # 簡單判斷紅與藍比例（排除灰色區）
    red_strength = np.sum((red > blue) & (red > green))
    blue_strength = np.sum((blue > red) & (blue > green))

    # 判斷結果
    if red_strength > blue_strength * 1.1:
        result = "紅色較多 → 預測莊"
    elif blue_strength > red_strength * 1.1:
        result = "藍色較多 → 預測閒"
    else:
        result = "紅藍接近 → 隨機預測：" + random.choice(["莊", "閒"])

    # 回覆分析結果
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"分析結果：{result}")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
