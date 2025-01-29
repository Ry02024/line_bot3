import os
import requests
import time
from google.api_core.exceptions import InternalServerError
import google.generativeai as genai

# 環境変数からGemini APIのURLとAPIキーを取得
gemini_api_key = os.getenv("GEMINI_API_KEY")

def get_gemini_text(topic, retries=3, delay=5, api_key=gemini_api_key):
    """
    Gemini APIを使って、指定されたトピックについて100字以内の説明文を生成する関数。
    `topic`: 説明してほしいトピック
    `retries`: エラー発生時のリトライ回数
    `delay`: リトライ時の待機時間（秒）
    """
    genai.configure(api_key=api_key)

    prompt = f"""
    以下のトピックについて、100字以内で簡潔に丁寧語で説明してください。
    トピック: {topic}
    """

    for attempt in range(retries):
        try:
            # Gemini APIにリクエストを送信
            response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
            if not response.text:
                raise ValueError("Gemini APIで有効なレスポンスが得られませんでした。")
            return response.text.strip()  # 正常なレスポンスを返す

        except InternalServerError as e:
            print(f"❌ Gemini APIエラー (リトライ {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
            if attempt == retries - 1:
                return "テスト"  # 最後の試行で失敗したら "テスト" を返す

        except Exception as e:
            print(f"❌ その他のエラー: {e}")
            return "テスト"  # その他のエラー時も "テスト" を返す
