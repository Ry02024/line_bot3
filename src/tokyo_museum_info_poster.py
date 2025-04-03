import os
import requests
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "").strip()
GEMINI_API = os.getenv("GEMINI_API_KEY", "").strip()

class GeminiLinePoster:
    def __init__(self, gemini_api, line_channel_access_token, line_group_id):
        self.gemini_api = gemini_api
        self.line_channel_access_token = line_channel_access_token
        self.line_group_id = line_group_id

        # Gemini クライアントの初期化
        self.client = genai.Client(api_key=self.gemini_api, http_options={'api_version': 'v1alpha'})
        self.search_client = self.client.chats.create(
            model='gemini-2.0-flash-exp',
            config={'tools': [{'google_search': {}}]}
        )

    # HTTP GET（リトライ付き）※使っていないが一応保持
    def robust_get(self, url, max_retries=3, timeout=20):
        for attempt in range(max_retries):
            try:
                r = requests.get(url, allow_redirects=True, timeout=timeout)
                return r
            except Exception:
                if attempt < max_retries - 1:
                    continue
                else:
                    return None

    # 要約生成
    def summary_client(self, original_text):
        summary_prompt = f"""
        以下のテキストを要約してください。
        可能であれば、文中の引用番号 ([1], [2], [10]など) は維持してください。
        特別展示と通常展示がある場合は、できる限り分類して記述してください。

        --- Original Text ---
        {original_text}
        ---------------------
        """
        summary_response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=summary_prompt
        )
        return summary_response.text.strip()

    # Gemini検索＆要約
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

    # 特別展示の内容に応じて絵文字を選択
    def select_emoji_by_content(self, content):
        content = content.lower()
        if any(keyword in content for keyword in ["現代", "絵画", "油彩", "アート", "美術"]):
            return random.choice(["🎨", "🖼️", "🖌️"])
        elif any(keyword in content for keyword in ["彫刻", "立体", "ブロンズ", "石", "像"]):
            return random.choice(["🗿", "🧱", "🏺"])
        elif any(keyword in content for keyword in ["歴史", "古代", "江戸", "縄文", "文化財"]):
            return random.choice(["🏛️", "📜", "🪙"])
        elif any(keyword in content for keyword in ["浮世絵", "日本", "和", "着物"]):
            return random.choice(["🎎", "🗾", "🈶"])
        elif any(keyword in content for keyword in ["演劇", "衣装", "舞台", "能", "歌舞伎"]):
            return random.choice(["🎭", "👘", "👗"])
        elif any(keyword in content for keyword in ["音楽", "ピアノ", "バイオリン", "演奏"]):
            return random.choice(["🎼", "🎻", "🎹"])
        elif any(keyword in content for keyword in ["子ども", "こども", "教育", "学び", "ファミリー"]):
            return random.choice(["🧸", "📚", "🧑‍🏫"])
        else:
            return random.choice(["🎨", "🖼️", "🏛️"])  # デフォルト

    # メイン処理：検索→整形→LINE投稿
    def post_search_result(self, query):
        summary = self.search_info(query)
        exhibitions = summary.split('\n')

        special_exhibitions = []
        for i, exhibition in enumerate(exhibitions, start=1):
            if "特別展示" in exhibition:
                emoji = self.select_emoji_by_content(exhibition)
                special_exhibitions.append(f"{emoji}{i}.{exhibition}")

        if not special_exhibitions:
            line_message = "本日の特別展示情報は見つかりませんでした。"
        else:
            line_message = "本日の特別展示情報\n\n" + "\n".join(special_exhibitions)

        self.send_message_to_line(line_message)

# メイン実行
if __name__ == "__main__":
    gemini_api = GEMINI_API
    line_channel_access_token = LINE_CHANNEL_ACCESS_TOKEN
    line_group_id = LINE_GROUP_ID

    poster = GeminiLinePoster(gemini_api, line_channel_access_token, line_group_id)

    # 東京の今日の美術館情報を投稿
    poster.post_search_result("今日の東京の美術館情報を教えてください。障がい者向けに無料の美術館があれば教えてください。文章はですます調でお願いします。")
