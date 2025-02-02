import os
import requests
from gemini import get_gemini_text  # `gemini.py` から関数をインポート
import random  # random モジュールをインポート

# 環境変数からLINEのアクセストークンとグループIDを取得
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
group_id = os.getenv("LINE_GROUP_ID")

def send_message(text):
    """LINEメッセージを送信する"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {channel_access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "to": group_id,
        "messages": [{"type": "text", "text": text}]
    }

    response = requests.post(url, json=data, headers=headers)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

if __name__ == "__main__":
    topics = [
        "最新のAI技術",
        "環境問題とテクノロジー",
        "宇宙探査の未来",
        "健康寿命を延ばす方法",
        "食料問題の解決策",
        "エネルギー問題の現状と対策",
        "教育の未来",
        "都市のスマート化",
        "リモートワークの進化",
        "サステナブルな社会"
    ] # トピックリストを定義

    topic = random.choice(topics) # ランダムにトピックを選択
    print(f"📢 今日のトピック: {topic}") # 選択されたトピックを出力

    message = get_gemini_text(topic)

    if message:
        print(f"📨 送信するメッセージ: {message}")
        send_message(message)
    else:
        print("⚠️ 生成されたメッセージが空です。")
