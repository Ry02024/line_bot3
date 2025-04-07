import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "")
MODE = os.getenv("MODE", "main")  # 'main' or 'detail'
MESSAGE_FILE = "exhibition_message.txt"

def send_to_line(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {"to": LINE_GROUP_ID, "messages": [{"type": "text", "text": text}]}
    r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
    print("✅ LINE送信成功" if r.status_code == 200 else f"❌ 送信失敗: {r.text}")

def save_to_file(text):
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print("✅ 保存完了")

def read_from_file():
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        return f.read()

def get_gemini_summary():
    # ダミー実装。Gemini APIで取得して整形する部分を入れる
    today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y年%-m月%-d日")
    return f"🗓️{today}時点、東京の展示情報です。\n\n🎨展示1：館1\n🎭展示2：館2\n🎨展示3：館3"

def get_one_detail():
    # 1つを抜き出して概要取得（ここもGemini検索の実装を想定）
    lines = read_from_file().splitlines()
    candidates = [line for line in lines if "：" in line]
    if not candidates:
        return "📭 詳細対象が見つかりませんでした。"
    return f"🔍 詳細紹介\n{candidates[0]} はとても興味深い展示です！"

if __name__ == "__main__":
    if MODE == "main":
        summary = get_gemini_summary()
        send_to_line(summary)
        save_to_file(summary)
    elif MODE == "detail":
        detail = get_one_detail()
        send_to_line(detail)
