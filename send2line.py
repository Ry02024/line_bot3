import json
import os
import random
import requests
import datetime
from gemini import get_gemini_text

# トピックリストの保存ファイル
TOPICS_FILE = "topics.json"
BOT_MESSAGE_LOG_FILE = "bot_message_log.txt"

# 初回実行時のデフォルトトピック（10個）
DEFAULT_TOPICS = [
    "AIと未来の働き方",
    "最新のテクノロジートレンド",
    "日本の伝統文化とデジタル技術",
    "ロボットと社会の関係",
    "持続可能な開発目標（SDGs）",
    "未来のモビリティと交通システム",
    "メタバースとその可能性",
    "宇宙開発の最新動向",
    "再生可能エネルギーの革新",
    "量子コンピュータの未来"
]

# LINE API設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")

def save_bot_message(text):
    """メッセージをログファイルに保存"""
    with open(BOT_MESSAGE_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text + "\n")

# 初回実行時に空のログファイルを作成（なければ）
if not os.path.exists(BOT_MESSAGE_LOG_FILE):
    with open(BOT_MESSAGE_LOG_FILE, "w", encoding="utf-8") as file:
        file.write("Bot Message Log Initialized\n")

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

def update_topics(topics):
    """日本時間21時の回だけ、ランダムに5つのトピックを入れ替える"""
    new_topics = random.sample(DEFAULT_TOPICS, 5)  # デフォルトリストからランダムに5つ選択
    remaining_topics = random.sample(topics, 5)   # 既存のリストからランダムに5つ選択
    updated_topics = new_topics + remaining_topics  # 10個のリストにする
    save_topics(updated_topics)
    print("🔄 日本時間21時のため、トピックリストを更新しました。")
    return updated_topics

def send_message(text):
    """LINEにメッセージを送信し、ログにも記録"""
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
        print("✅ メッセージ送信成功")
        save_bot_message(text)  # 送信後にログへ記録
    else:
        print(f"❌ メッセージ送信失敗: {response.status_code}, {response.text}")

if __name__ == "__main__":
    topics = load_topics()  # トピックリストの読み込み

    # 現在のUTC時刻を取得し、日本時間21時かどうかを判定
    now_utc = datetime.datetime.utcnow()
    jst_hour = (now_utc.hour + 9) % 24  # UTCからJSTに変換

    if jst_hour == 21:
        topics = update_topics(topics)  # 21時の回のみトピックを更新
    else:
        print(f"⏰ 日本時間{jst_hour}時のため、トピックは変更しません。")

    topic = random.choice(topics)  # ランダムにトピックを選択
    print(f"🎯 選択されたトピック: {topic}")

    tweet = get_gemini_text(topic)  # Gemini API でツイート生成
    print(f"📝 生成されたメッセージ: {tweet}")

    send_message(tweet)  # LINE にメッセージを送信
