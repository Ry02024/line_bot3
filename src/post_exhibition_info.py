import os, sys, json
import random
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MESSAGE_FILE = "data/exhibition_message.txt"
DETAIL_HISTORY_FILE = "data/detail_history.json"

class GeminiLinePoster:
    def __init__(self, api_key, line_token, group_id):
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
        self.search_client = self.client.chats.create(
            model='gemini-2.0-flash-exp',
            config={'tools': [{'google_search': {}}]}
        )
        self.line_token = line_token
        self.group_id = group_id

    def send_to_line(self, message):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.line_token}"
        }
        body = {
            "to": self.group_id,
            "messages": [{"type": "text", "text": message}]
        }
        res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
        print("✅ LINE送信:", res.status_code, res.text)

    def generate_summary(self):
        query = "今日の東京の特別展示情報を5つ教えてください。障がい者向けに無料の展示を優先して教えてください。"
        response = self.search_client.send_message(query)
        original_text = "".join(part.text for part in response.candidates[0].content.parts if part.text)

        today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%Y年%-m月%-d日')
        prompt = f"""
🗓️{today}時点、東京で開催中の障がい者向け無料鑑賞ができる美術館情報です。

以下の形式で、展示名と館名を簡潔に整理してください：
🎨展示名1：館名1
🏛️展示名2：館名2

条件：
- 特別展示と常設展示に分類
- 見出し行（例: 🎨特別展示：）などは含めず、展示＋館名のペアだけ
- 詳細な説明不要、展示名＋館名のセットのみ
- 絵文字あり、LINEで見やすく
"""

        result = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt + "\n\n--- Original Text ---\n" + original_text
        )
        text = result.text.strip()
        with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        return text

def send_detail_one_by_one(self):
    if not os.path.exists(MESSAGE_FILE):
        print("❌ summaryがまだ生成されていません")
        return

    with open(MESSAGE_FILE, encoding="utf-8") as f:
        raw_text = f.read()

    # Geminiで見出しを除いて展示ペアだけを抽出
    extract_prompt = f"""
    以下の展示情報から、「展示名：館名」のペアだけを抽出してください。
    見出し（🎨特別展示：など）は除外してください。
    
    --- テキスト ---
    {raw_text}
    ------------------
    """
    extract_response = self.client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=extract_prompt
    )
    all_lines = [line.strip() for line in extract_response.text.strip().splitlines() if "：" in line]

    # --- 💾 履歴ファイルから既出の展示名を取得 ---
    sent_exhibitions = set()
    if os.path.exists(DETAIL_HISTORY_FILE):
        try:
            with open(DETAIL_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                sent_exhibitions = {entry["exhibition"].strip() for entry in history if "exhibition" in entry}
        except Exception as e:
            print(f"⚠️ 履歴読み込みエラー: {e}")

    # --- 🧹 重複を除いた展示リストを抽出 ---
    available_lines = []
    for line in all_lines:
        exhibition_candidate = line.split("：", 1)[0].strip("🎨🏛️✨🌟").strip()
        if exhibition_candidate not in sent_exhibitions:
            available_lines.append(line)

    if not available_lines:
        print("✅ 全展示はすでに送信済みです。新しい展示をお待ちください。")
        return

    line = random.choice(available_lines)
    exhibition, museum = line.replace("：", ":").split(":", 1)
    exhibition = exhibition.strip("🎨🏛️✨🌟").strip()
    museum = museum.strip()

    # 展示概要取得
    search_query = f"{exhibition} {museum} の展示概要を教えてください。"
    response = self.search_client.send_message(search_query)
    original_text = "".join(part.text for part in response.candidates[0].content.parts if part.text).strip()

    # 要約（LINE向け）
    prompt = f"""
    以下の展示紹介文を200文字以内で要約してください。視認性を意識し、文末は「です・ます」調でお願いします。
    料金や開催期間などの詳細情報は含めず、展示の概要のみを簡潔に記述してください。
    
    --- 原文 ---
    {original_text}
    ---------------------
    """
    summary_response = self.client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    detail_text = summary_response.text.strip()

    today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%-m月%-d日')
    message = f"🖼️ {today}の注目展示\n\n🎨{exhibition}（{museum}）\n\n{detail_text}"

    # --- JSON履歴保存 ---
    try:
        entry = {
            "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "exhibition": exhibition,
            "museum": museum,
            "detail_summary": detail_text,
        }

        history = []
        try:
            with open(DETAIL_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            if not isinstance(history, list):
                history = []
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        history.append(entry)
        with open(DETAIL_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"⚠️ 詳細履歴のJSON保存中にエラー: {e}")

    self.send_to_line(message)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "summary"
    poster = GeminiLinePoster(GEMINI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_GROUP_ID)
    if mode == "summary":
        summary = poster.generate_summary()
        poster.send_to_line(summary)
    elif mode == "detail":
        poster.send_detail_one_by_one()
    else:
        print("❌ 無効なモードです。'summary' または 'detail' を指定してください。")
