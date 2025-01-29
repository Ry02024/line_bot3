import os

# 環境変数から API キーを取得
api_key = os.getenv("GOOGLE_API_KEY")

# 確認用メッセージ
if api_key:
    print(f"✅ GOOGLE_API_KEY が設定されています: {api_key[:5]}********")
else:
    print("❌ GOOGLE_API_KEY が設定されていません。")
