import json
import os
import random
import requests
from gemini import get_gemini_text

# トピックリストの保存ファイル
TOPICS_FILE = "topics.json"

# 初回実行時のデフォルトトピック
DEFAULT_TOPICS = [
    "AIと未来の働き方",
    "最新のテクノロジートレンド",
    "日本の伝統文化とデジタル技術",
    "ロボットと社会の関係",
    "持続可能な開発目標（SDGs）"
]

# LINE API設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")

def load_topics():
    """トピックリストをJSONファイルから読み込む（なければ作成）"""
    if not os.path.exists(TOPICS_FILE):
        print(f"{TOPICS_FILE} が存在しないため、新しく作成します。")
        save_topics(DEFAULT_TOPICS)
        return DEFAULT_TOPICS
    with open(TOPICS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_topics(topics):
    """トピックリストをJSONファイルに保存"""
    with open(TOPICS_FILE, "w", encoding="utf-8") as file:
        json.dump(topics, file, ensure_ascii=False, indent=4)
    print(f"{TOPICS_FILE} を更新しました。")

def send_message(text):
    """LINEにメッセージを送信"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_GROUP_ID,
        "messages": [{"type": "text", "text": text}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("メッセージ送信成功")
    else:
        print(f"メッセージ送信失敗: {response.status_code}, {response.text}")

if __name__ == "__main__":
    topics = load_topics()  # トピックリストの読み込み
    topic = random.choice(topics)  # ランダムにトピックを選択
    print(f"選択されたトピック: {topic}")

    tweet = get_gemini_text(topic)  # Gemini API でツイート生成
    print(f"生成されたメッセージ: {tweet}")

    send_message(tweet)  # LINE にメッセージを送信
