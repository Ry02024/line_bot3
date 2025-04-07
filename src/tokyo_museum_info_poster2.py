import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "").strip()
GEMINI_API = os.getenv("GEMINI_API_KEY", "").strip()
MESSAGE_FILE = "exhibition_message.txt"  # 保存するテキストファイル名

class GeminiLinePoster:
    def __init__(self, gemini_api, line_channel_access_token, line_group_id):
        self.gemini_api = gemini_api
        self.line_channel_access_token = line_channel_access_token
        self.line_group_id = line_group_id

        self.client = genai.Client(api_key=self.gemini_api, http_options={'api_version': 'v1alpha'})
        self.search_client = self.client.chats.create(
            model='gemini-2.0-flash-exp',
            config={'tools': [{'google_search': {}}]}
        )

    def summary_client(self, original_text):
        summary_prompt = f"""
        次の内容をLINE向けに要約してください。

        '🗓️{datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%Y年%-m月%-d日')}時点、東京で開催中の障がい者向け無料鑑賞ができる美術館情報です。'
        の文章から始めて下さい。特別展示を5つ調査して以下の様に教えて下さい。

        以下の形式で、展示名と美術館名を簡潔に整理してください：
        🎨展示名1：館名1
        🏛️展示名2：館名2

        条件：
        - 特別展示と通常展示を分類して並べてください。
        - マークダウンやリンク表記は不要です。
        - 詳細な日程や説明文は不要です（展示名＋館名のセットだけで結構です）。
        - 絵文字を使い、LINEで視認性が高いフォーマットにしてください。

        --- Original Text ---
        {original_text}
        ---------------------
        """

        summary_response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=summary_prompt
        )
        return summary_response.text.strip()

    def search_info(self, user_query):
        response = self.search_client.send_message(user_query)
        original_text = ""
        for part in response.candidates[0].content.parts:
            if part.text:
                original_text += part.text + "\n"
        summary_text = self.summary_client(original_text)
        return summary_text

    # LINEへの送信
    def send_message_to_line(self, message):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.line_channel_access_token}"
        }
        data = {
            "to": self.line_group_id,
            "messages": [{"type": "text", "text": message}]
        }
        response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
        if response.status_code == 200:
            print("✅ メッセージ送信成功")
        else:
            print(f"❌ メッセージ送信失敗: {response.status_code}, {response.text}")
    
    # メッセージをファイルに保存するだけ
    def save_message(self, message):
        with open(MESSAGE_FILE, 'w', encoding='utf-8') as f:
            f.write(message)
        print(f"✅ メッセージを {MESSAGE_FILE} に保存しました")

# 例: 実行ブロック
if __name__ == "__main__":
    gemini_api = GEMINI_API
    line_channel_access_token = LINE_CHANNEL_ACCESS_TOKEN
    line_group_id = LINE_GROUP_ID

    poster = GeminiLinePoster(gemini_api, line_channel_access_token, line_group_id)
    query = "今日の東京の特別展示情報を5つ教えてください。障がい者向けに無料の展示を優先して教えてください。文章はですます調でお願いします。"
    summary = poster.search_info(query)
    
    # LINEにメッセージ送信
    poster.send_message_to_line(summary)
    
    # メッセージをファイルに保存
    poster.save_message(summary)
