import os
import requests
from gemini import get_gemini_text  # `gemini.py` から関数をインポート
import random  # random モジュールをインポート
import json # JSON モジュールをインポート (トピックリストの保存・読み込みのため)
import datetime # datetime モジュールをインポート (save_bot_message で使用)

# 環境変数からLINEのアクセストークンとグループIDを取得
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
group_id = os.getenv("LINE_GROUP_ID")

BOT_MESSAGE_LOG_FILE = "bot_message_log.txt" # ボットのメッセージログファイル名
TOPICS_FILE = "topics.json" # トピックリストを保存するファイル名 (JSON形式)

def save_bot_message(text):
    """ボットのメッセージをログファイルに保存する関数"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # タイムスタンプ
    try:
        with open(BOT_MESSAGE_LOG_FILE, "a") as f:
            f.write(f"{timestamp}: {text}\n")
    except Exception as e:
        print(f"⚠️ メッセージログ保存エラー: {e}")
        
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

def load_topics():
    """トピックリストをファイルから読み込む関数"""
    try:
        with open(TOPICS_FILE, "r", encoding="utf-8") as f: # UTF-8 エンコーディングでファイルを開く
            topics = json.load(f) # JSON形式で読み込む
        print("✅ トピックリストをファイルから読み込みました。") # ログ出力
        return topics
    except FileNotFoundError:
        print("ℹ️ トピックリストファイルが見つかりませんでした。初期リストを作成します。") # ログ出力
        return None # ファイルがない場合は None を返す
    except json.JSONDecodeError:
        print("⚠️ トピックリストファイルのJSON形式が不正です。初期リストを作成します。") # ログ出力
        return None # JSON形式エラーの場合も None を返す
    except Exception as e:
        print(f"⚠️ トピックリスト読み込みエラー: {e}") # ログ出力
        return None # その他のエラーの場合も None を返す

def save_topics(topics):
    """トピックリストをファイルに保存する関数"""
    try:
        with open(TOPICS_FILE, "w", encoding="utf-8") as f: # UTF-8 エンコーディングでファイルを開く
            json.dump(topics, f, indent=2, ensure_ascii=False) # JSON形式で保存 (インデント付き、日本語文字化け対策)
        print("✅ トピックリストをファイルに保存しました。") # ログ出力
    except Exception as e:
        print(f"⚠️ トピックリスト保存エラー: {e}") # ログ出力
        
if __name__ == "__main__":
    # トピックリストの初期化処理 (ファイルから読み込む or 初期リスト作成)
    initial_topics = [ # 初期トピックリスト (ファイルがない場合に使用)
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
    ]
    loaded_topics = load_topics() # ファイルからトピックリストを読み込む
    if loaded_topics:
        topics = loaded_topics # ファイルから読み込めた場合はそちらを使用
    else:
        topics = initial_topics # ファイルから読み込めなかった場合は初期リストを使用
        save_topics(topics) # 初期リストをファイルに保存 (次回から読み込めるように)


    topic = random.choice(topics) # ランダムにトピックを選択
    print(f"📢 今日のトピック: {topic}") # 選択されたトピックを出力

    message = get_gemini_text(topic)

    if message:
        print(f"📨 送信するメッセージ: {message}")
        send_message(message)
    else:
        print("⚠️ 生成されたメッセージが空です。")
