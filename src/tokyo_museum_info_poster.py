import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

# 環境変数の取得（strip() で空白削除）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "").strip()
GEMINI_API = os.getenv("GEMINI_API_KEY", "").strip()

# Gemini API Key を環境変数から取得
GEMINI_API_KEY = os.getenv("GEMINI_API", "").strip()

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
    
    # ----- リトライ処理付き GET 関数 -----
    def robust_get(self, url, max_retries=3, timeout=20):
        for attempt in range(max_retries):
            try:
                r = requests.get(url, allow_redirects=True, timeout=timeout)
                return r
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                else:
                    return None
    
    # ----- リダイレクト先のURL取得 -----
    def get_final_url(self, redirect_url):
        r = self.robust_get(redirect_url)
        return r.url if r else None
    
    # ----- Gemini 応答の要約 -----
    def summary_client(self, original_text):
        summary_prompt = f"""
        以下のテキストを要約してください。
        可能であれば、文中の引用番号 ([1], [2], [10]など) は維持してください。

        --- Original Text ---
        {original_text}
        ---------------------
        """
        summary_response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=summary_prompt
        )
        return summary_response.text.strip()
    
    # ----- 参照サイト一覧生成 -----
    def serch_references(self, response):
        if not response.candidates[0].grounding_metadata:
            return "検索結果情報 (grounding_metadata) がありませんでした。"
        else:
            grounding_chunks = response.candidates[0].grounding_metadata.grounding_chunks
            if not grounding_chunks:
                return "URLが取得できませんでした。ご興味のある方はご自身でも調べてみて下さい。"
            else:
                ref_lines = []
                ref_lines.append("*取得した参照サイト一覧:*")
                for i, chunk in enumerate(grounding_chunks, start=1):
                    redirect_url = chunk.web.uri
                    final_url = self.get_final_url(redirect_url)
                    if final_url is None:
                        page_title = "（リダイレクト失敗）"
                    else:
                        try:
                            resp = self.robust_get(final_url)
                            if resp is None:
                                page_title = "（取得失敗）"
                            elif resp.status_code == 200:
                                page_title = "（取得成功）"
                            else:
                                page_title = f"（取得できませんでした: {resp.status_code}）"
                        except Exception as e:
                            page_title = f"（エラー: {str(e)}）"
                    ref_lines.append(f"{i}. <{final_url}|{page_title}>")
                return "\n.join(ref_lines)"
    
    # ----- search_info 関数 -----
    def search_info(self, user_query):
        response = self.search_client.send_message(user_query)
        original_text = ""
        for part in response.candidates[0].content.parts:
            if part.text:
                original_text += part.text + "\n"
        summary_text = self.summary_client(original_text)
        references_text = self.serch_references(response)
        return summary_text, references_text, response
    
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

    
    # ----- search_info を利用して LINE に投稿する関数 -----
    def post_search_result(self, query):
        summary, references, response = self.search_info(query)
        line_message = f"*要約結果:*\n{summary}\n\n{references}"
        self.send_message_to_line(line_message)

# ----------------------------------------
# メイン処理
# ----------------------------------------
if __name__ == "__main__":
    gemini_api = GEMINI_API
    line_channel_access_token = LINE_CHANNEL_ACCESS_TOKEN
    line_group_id = LINE_GROUP_ID

    poster = GeminiLinePoster(gemini_api, line_channel_access_token, line_group_id)
    
    # 現在時刻を取得
    current_hour = datetime.now(ZoneInfo("Asia/Tokyo")).hour
    
    # 今日の東京の美術館情報を取得してLINEに投稿
    poster.post_search_result("今日の東京の美術館情報を教えてください。障がい者向けに無料の美術館があれば教えてください。文章はですます調でお願いします。")
