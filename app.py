from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return 'Bot OK', 200

@app.route('/callback', methods=['POST'])
def callback():
    print("收到 LINE webhook！")
    return 'OK', 200  # ✅ 一定要回傳 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
