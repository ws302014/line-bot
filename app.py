from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, ImageMessage
import requests
import pytesseract
from PIL import Image
import io
import os

app = Flask(__name__)

# 環境變數（Render 會自動幫你設置）
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

score_map = {
    '1': 1, '2': 1, '3': 1, '4': 1, '5': 1,
    '6': 0, '7': 0, '8': 0, '9': 0,
    '10': -1, 'J': -1, 'Q': -1, 'K': -1
}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # 下載圖片
    message_content = line_bot_api.get_message_content(event.message.id)
    img = Image.open(io.BytesIO(message_content.content))

    # OCR
    text = pytesseract.image_to_string(img, lang='eng').upper().replace(" ", "")
    print("偵測到文字：", text)

    # 計算分數
    total = 0
    for key, val in score_map.items():
        total += text.count(key) * val

    # 分析結果
    if total > 0:
        banker_prob = 60 + total * 2
        player_prob = 100 - banker_prob
        result = f"莊機率約 {banker_prob}%（總分 +{total}）"
    elif total < 0:
        player_prob = 60 + abs(total) * 2
        banker_prob = 100 - player_prob
        result = f"閒機率約 {player_prob}%（總分 {total}）"
    else:
        result = "莊機率約 55%（總分 0）"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

@app.route('/')
def home():
    return 'LINE OCR Bot is running!'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
