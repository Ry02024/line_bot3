import sys, os, json, random, requests, datetime,

# src/ ディレクトリを sys.path に追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Gemini モジュールのインポート
from gemini import get_gemini_text, summarize_text, generate_topics_from_summary

# ファイルの定義
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # `src/` のディレクトリを取得
CONFIG_DIR = os.path.join(BASE_DIR, "../config")  # `config/` のパスを取得

TOPICS_FILE = os.path.join(CONFIG_DIR, "topics.json")  # 新しいパス
BOT_MESSAGE_LOG_FILE = os.path.join("../logs", "bot_message_log.txt")  # ログの修正

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

def update_topics(summary_text):
    """既存のトピックから5つを維持し、要約から5つの新トピックを生成して更新"""
    if not summary_text or summary_text.strip() == "投稿が少ないため、要約できませんでした。":
        print("⚠️ 要約が十分に生成されなかったため、トピックを更新しません。")
        return load_topics()  # トピック更新せず、既存のまま

    old_topics = load_topics()
    new_topics = generate_topics_from_summary(summary_text)  # Gemini APIで新トピックス生成

    if len(new_topics) < 5:
        print("⚠️ 新しいトピックスが5つ生成されなかったため、更新をスキップします。")
        return old_topics
    
    remaining_topics = random.sample(old_topics, 5)  # 既存の5つを維持
    updated_topics = new_topics + remaining_topics  # 10個のリストにする
    save_topics(updated_topics)
    print("🔄 トピックリストを更新しました。")
    
    return updated_topics

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

def update_topics(summary_text):
    """既存のトピックから5つを維持し、要約から5つの新トピックを生成して更新"""
    if not summary_text or summary_text.strip() == "投稿が少ないため、要約できませんでした。":
        print("⚠️ 要約が十分に生成されなかったため、トピックを更新しません。")
        return load_topics()  # トピック更新せず、既存のまま

    old_topics = load_topics()
    new_topics = generate_topics_from_summary(summary_text)  # Gemini APIで新トピックス生成

    if len(new_topics) < 5:
        print("⚠️ 新しいトピックスが5つ生成されなかったため、更新をスキップします。")
        return old_topics
    
    remaining_topics = random.sample(old_topics, 5)  # 既存の5つを維持
    updated_topics = new_topics + remaining_topics  # 10個のリストにする
    save_topics(updated_topics)
    print("🔄 トピックリストを更新しました。")
    
    return updated_topics

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
        print("✅ メッセージ送信成功")
        save_bot_message(text)  # 送信後にログへ記録
    else:
        print(f"❌ メッセージ送信失敗: {response.status_code}, {response.text}")

def read_bot_messages():
    """bot_message_log.txt から本日の投稿を取得"""
    if not os.path.exists(BOT_MESSAGE_LOG_FILE):
        return []

    with open(BOT_MESSAGE_LOG_FILE, "r", encoding="utf-8") as file:
        messages = file.readlines()
    
    return messages

if __name__ == "__main__":
    now_utc = datetime.datetime.utcnow()
    jst_hour = (now_utc.hour + 9) % 24  # UTCからJSTに変換
    jst_minute = now_utc.minute

    # **テストモード (手動実行)**
    if "--test-summary" in sys.argv:
        print("🚀 **手動テストモード: 1日の要約とトピック更新を実行** 🚀")
        messages = read_bot_messages()
        summary_text = summarize_text(messages)
        send_message(f"📅 **テスト要約**:\n{summary_text}")
        update_topics(summary_text)  # **修正: ここで summary_text を引数に渡す**
        sys.exit(0)  # テスト完了
        
    # 📌 **日本時間21:15 → 1日の要約を投稿 & トピック更新**
    if jst_hour == 21 and jst_minute >= 15:
        print("📢 日本時間21:15 要約メッセージを投稿し、トピックを更新します。")
        messages = read_bot_messages()
        summary_text = summarize_text(messages)
        
        send_message(f"📅 本日の要約:\n{summary_text}")
        update_topics()  # トピックを更新

    # 📌 **それ以外の時間帯は通常のランダム投稿**
    else:
        topics = load_topics()
        topic = random.choice(topics)  # ランダムにトピックを選択
        print(f"🎯 選択されたトピック: {topic}")

        tweet = get_gemini_text(topic)  # Gemini API でツイート生成
        print(f"📝 生成されたメッセージ: {tweet}")

        send_message(tweet)  # LINE にメッセージを送信
