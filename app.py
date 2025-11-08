from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage,
    TemplateSendMessage, ButtonsTemplate, MessageTemplateAction
)
import pytesseract
from PIL import Image
import io
import os
import random

app = Flask(__name__)

# LINE 環境變數
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 牌面分數設定
score_map = {
    '1': 1, '2': 1, '3': 1, '4': 1, '5': 1,
    '6': 0, '7': 0, '8': 0, '9': 0,
    '10': -1, 'J': -1, 'Q': -1, 'K': -1
}

# 使用者暫存圖片預測結果
user_results = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 使用者文字互動
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.strip()

    # Step 1：輸入「預測」時顯示按鈕
    if text in ["預測", "開始", "測試"]:
        buttons_template = TemplateSendMessage(
            alt_text='預測選項',
            template=ButtonsTemplate(
                title="請選擇動作👇",
                text="請上傳牌勢圖片或直接選擇狀況：",
                actions=[
                    MessageTemplateAction(label="大牌多", text="大牌多"),
                    MessageTemplateAction(label="小牌多", text="小牌多"),
                    MessageTemplateAction(label="一樣多", text="一樣多"),
                    MessageTemplateAction(label="公天牌", text="公天牌"),
                    MessageTemplateAction(label="點天牌", text="點天牌"),
                    MessageTemplateAction(label="和大牌", text="和大牌"),
                    MessageTemplateAction(label="和小牌", text="和小牌")
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return

    # Step 2：按鈕回傳後進行預測
    if event.source.user_id in user_results:
        banker_prob, player_prob = user_results[event.source.user_id]

        adjustment = {
            "大牌多": ("player", random.randint(3, 10)),
            "小牌多": ("banker", random.randint(3, 10)),
            "一樣多": ("banker", random.randint(1, 5)),
            "和大牌": ("player", random.randint(3, 10)),
            "和小牌": ("banker", random.randint(3, 10)),
            "公天牌": ("player", random.randint(8, 15)),
            "點天牌": ("banker", random.randint(8, 15))
        }

        if text in adjustment:
            side, value = adjustment[text]
            if side == "banker":
                banker_prob += value
            else:
                player_prob += value

            # 限制上限
            if banker_prob > 95: banker_prob = 95
            if player_prob > 95: player_prob = 95

            # 依據最終機率決定結果
            result_side = "莊" if banker_prob >= player_prob else "閒"
            result = f"📊 最終預測結果：{result_side}\n莊：{banker_prob}%　閒：{player_prob}%"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
            del user_results[event.source.user_id]
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請使用按鈕選擇牌勢狀況"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先輸入『預測』開始流程。"))

# 使用者上傳圖片
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    img = Image.open(io.BytesIO(message_content.content))

    # OCR 偵測文字
    text = pytesseract.image_to_string(img, lang='eng').upper().replace(" ", "")
    print("偵測到文字：", text)

    # 隨機預測（模擬初步分析）
    banker_prob = random.randint(45, 70)
    player_prob = 100 - banker_prob

    # 暫存初步預測結果
    user_results[event.source.user_id] = (banker_prob, player_prob)

    # 回覆結果 + 按鈕
    buttons_template = TemplateSendMessage(
        alt_text='初步預測結果',
        template=ButtonsTemplate(
            title="初步預測結果 👇",
            text=f"莊 {banker_prob}%　閒 {player_prob}%\n請選擇牌勢狀況以修正預測：",
            actions=[
                MessageTemplateAction(label="大牌多", text="大牌多"),
                MessageTemplateAction(label="小牌多", text="小牌多"),
                MessageTemplateAction(label="一樣多", text="一樣多"),
                MessageTemplateAction(label="公天牌", text="公天牌"),
                MessageTemplateAction(label="點天牌", text="點天牌"),
                MessageTemplateAction(label="和大牌", text="和大牌"),
                MessageTemplateAction(label="和小牌", text="和小牌")
            ]
        )
    )

    line_bot_api.reply_message(event.reply_token, buttons_template)

@app.route('/')
def home():
    return 'LINE 百家樂預測 Bot 正在運行！'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
