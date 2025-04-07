import os
import sys
import random
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MESSAGE_FILE = "exhibition_message.txt"

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
        query = "今日の東京の特別展示情報を5つ教えてください。障がい者向けに無料の展示を優先して教えてください。文章はですます調でお願いします。"
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
        - マークダウン・リンク不要
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
            lines = [line for line in f.read().splitlines() if line.strip() and ("：" in line)]

        if not lines:
            print("❌ 特別展示のデータが見つかりません")
            return

        line = random.choice(lines)
        exhibition, museum = line.replace("：", ":").split(":")
        exhibition = exhibition.strip("🎨🏛️✨🌟").strip()
        museum = museum.strip()

        query = f"""
        「{exhibition}」という展示が「{museum}」で開催されています。
        この展示の概要を200文字以内で教えてください。
        簡潔でLINE向けに読みやすくまとめてください。
        日程・料金などの詳細は不要です。
        """

        response = self.search_client.send_message(query)
        detail_text = "".join(part.text for part in response.candidates[0].content.parts if part.text).strip()

        # メッセージ整形
        today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%-m月%-d日')
        message = f"🖼️ {today}の注目展示\n\n🎨{exhibition}（{museum}）\n\n{detail_text}"
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
