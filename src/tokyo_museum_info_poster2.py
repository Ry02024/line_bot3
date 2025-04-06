import os
import requests
import json
import random
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "").strip()
GEMINI_API = os.getenv("GEMINI_API_KEY", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()  # GitHub APIトークン
REPO_OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "").strip()  # リポジトリオーナー
REPO_NAME = os.getenv("GITHUB_REPOSITORY", "").strip().split("/")[-1]  # リポジトリ名
CACHE_FILE = "exhibition_cache.json"  # キャッシュファイル名

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
        """検索結果をLINE向けに要約する"""
        summary_prompt = f"""
        次の内容をLINE向けに要約してください。
        '🗓️{datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%Y年%-m月%-d日')}時点、東京で開催中の障がい者向け無料鑑賞ができる美術館情報です。'
        の文章から始めて下さい。特別展示を5つ調査して以下の様に教えて下さい。
        以下の形式で、展示名と美術館名を簡潔に整理してください：
        【特別展示】
        🎨展示名1：館名1
        🎨展示名2：館名2
        
        【常設展示】
        🏛️展示名3：館名3
        🏛️展示名4：館名4
        
        条件：
        - 特別展示と常設展示を明確に分類して並べてください。
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

    def get_exhibition_detail(self, exhibition_name, museum_name):
        """特定の展示についての簡単な説明を取得する"""
        detail_prompt = f"""
        東京の「{museum_name}」で開催されている「{exhibition_name}」について展示内容の簡単な説明（100文字程度）を調べてください。
        
        説明は以下の条件を満たすようにしてください：
        - 100文字程度で簡潔に
        - 展示の主要テーマを明確に
        - 障がい者の方々にとって参考になる情報があれば含める
        - ですます調の文体
        
        LINEで見やすいように冒頭に「🎨【今日のピックアップ】{exhibition_name}＠{museum_name}」と表示し、
        その後に説明文を続けてください。全体で4行以内にまとめてください。
        """
        
        response = self.search_client.send_message(detail_prompt)
        detail_text = ""
        for part in response.candidates[0].content.parts:
            if part.text:
                detail_text += part.text + "\n"
                
        # LINEに適した形式に整形
        formatting_prompt = f"""
        次の展示情報をLINE向けに整形してください：
        - 冒頭に「🎨【今日のピックアップ】{exhibition_name}＠{museum_name}」と表示
        - その後に展示内容の説明を続ける
        - 文章は100文字程度でシンプルに
        - 全体で4行以内に収める
        
        元の情報：
        {detail_text}
        """
        
        formatted_response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=formatting_prompt
        )
        
        return formatted_response.text.strip()

    def search_info(self, user_query):
        """検索を実行し、結果と要約を返す"""
        response = self.search_client.send_message(user_query)
        original_text = ""
        for part in response.candidates[0].content.parts:
            if part.text:
                original_text += part.text + "\n"
        summary_text = self.summary_client(original_text)
        return summary_text, original_text

    def send_message_to_line(self, message):
        """LINEグループにメッセージを送信する"""
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

    def extract_exhibitions(self, summary_text):
        """要約テキストから展示名と美術館名のペアを抽出する"""
        exhibitions = []
        special_exhibitions = []
        permanent_exhibitions = []
        
        lines = summary_text.split('\n')
        current_section = None
        
        for line in lines:
            if '【特別展示】' in line:
                current_section = 'special'
                continue
            elif '【常設展示】' in line:
                current_section = 'permanent'
                continue
                
            if '：' in line and ('🎨' in line or '🏛️' in line):
                parts = line.split('：')
                if len(parts) == 2:
                    exhibition_name = parts[0].replace('🎨', '').replace('🏛️', '').strip()
                    museum_name = parts[1].strip()
                    
                    if current_section == 'special':
                        special_exhibitions.append((exhibition_name, museum_name))
                    elif current_section == 'permanent':
                        permanent_exhibitions.append((exhibition_name, museum_name))
        
        # 特別展示と常設展示を分けて保持
        exhibitions = {
            'special': special_exhibitions,
            'permanent': permanent_exhibitions
        }
        
        return exhibitions

    def download_cache_from_github(self):
        """GitHubからキャッシュファイルをダウンロード"""
        try:
            # GitHub APIを使用してファイルの内容を取得
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CACHE_FILE}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                content = response.json()
                # Base64でエンコードされたコンテンツをデコード
                import base64
                file_content = base64.b64decode(content["content"]).decode('utf-8')
                
                # ファイルに保存
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                    
                print(f"✅ GitHubから{CACHE_FILE}をダウンロードしました")
                return True
            else:
                print(f"❌ GitHubからのファイル取得に失敗: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ GitHubからのファイル取得中にエラー発生: {e}")
            return False

    def upload_cache_to_github(self, cache_data):
        """GitHubにキャッシュファイルをアップロード"""
        try:
            # まずファイルに保存
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # GitHub CLI (gh)を使用してコミットとプッシュ
            # GitHub Actionsの認証情報を使用
            commands = [
                f'git config --global user.name "github-actions[bot]"',
                f'git config --global user.email "github-actions[bot]@users.noreply.github.com"',
                f'git add {CACHE_FILE}',
                f'git commit -m "Update exhibition cache {datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M")}"',
                f'git push'
            ]
            
            for cmd in commands:
                process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if process.returncode != 0:
                    print(f"❌ コマンド実行エラー: {cmd}")
                    print(f"エラー出力: {process.stderr}")
                    return False
            
            print(f"✅ {CACHE_FILE}をGitHubにアップロードしました")
            return True
            
        except Exception as e:
            print(f"❌ GitHubへのアップロード中にエラー発生: {e}")
            return False

    def morning_schedule(self):
        """朝9時に実行する一覧情報取得と保存のフロー"""
        # 基本情報の検索と送信
        query = "今日の東京の特別展示情報を5つ教えてください。障がい者向けに無料の展示を優先して教えてください。特別展示と常設展示を分けて教えてください。文章はですます調でお願いします。"
        summary, original_text = self.search_info(query)
        
        # 要約情報をLINEに送信
        self.send_message_to_line(summary)
        
        # 展示情報を抽出
        exhibitions = self.extract_exhibitions(summary)
        
        # 今日の情報をキャッシュに保存（後で詳細取得用に使う）
        cache_data = {
            'date': datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%Y-%m-%d'),
            'summary': summary,
            'special': [[e[0], e[1]] for e in exhibitions['special']],
            'permanent': [[e[0], e[1]] for e in exhibitions['permanent']]
        }
        
        # GitHubにアップロード
        self.upload_cache_to_github(cache_data)
            
        return "朝の情報送信と保存が完了しました。"

    def detail_schedule(self):
        """別の時間帯に実行する展示詳細1件のフロー"""
        try:
            # GitHubからキャッシュファイルをダウンロード
            cache_exists = self.download_cache_from_github()
            
            if not cache_exists:
                print("キャッシュファイルが見つからないか、ダウンロードに失敗しました。")
                return "キャッシュファイルが見つかりません。朝の情報を先に取得してください。"
            
            # キャッシュから情報を読み込む
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # 日付チェック（当日の情報かどうか）
            today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%Y-%m-%d')
            if cache_data['date'] != today:
                # 古い情報の場合は新しく取得
                print("キャッシュが古いため、新しい情報を取得します")
                self.morning_schedule()
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            
            # 展示情報の再構築
            special_exhibitions = [(item[0], item[1]) for item in cache_data['special']]
            permanent_exhibitions = [(item[0], item[1]) for item in cache_data['permanent']]
            
            # 特別展示を優先、ない場合は常設展示から選択
            if special_exhibitions:
                # 特別展示からランダムに1つ選択
                selected_exhibition = random.choice(special_exhibitions)
            elif permanent_exhibitions:
                # 常設展示からランダムに1つ選択
                selected_exhibition = random.choice(permanent_exhibitions)
            else:
                print("展示情報がありません")
                return "展示情報の取得に失敗しました。"
            
            # 選択した展示の詳細を取得して送信
            exhibition_name, museum_name = selected_exhibition
            exhibition_detail = self.get_exhibition_detail(exhibition_name, museum_name)
            self.send_message_to_line(exhibition_detail)
            
            return f"展示詳細「{exhibition_name}＠{museum_name}」の送信が完了しました。"
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return f"エラーが発生しました: {e}"

# 実行例
if __name__ == "__main__":
    gemini_api = GEMINI_API
    line_channel_access_token = LINE_CHANNEL_ACCESS_TOKEN
    line_group_id = LINE_GROUP_ID
    
    poster = GeminiLinePoster(gemini_api, line_channel_access_token, line_group_id)
    
    # コマンドライン引数で実行モードを指定可能（デフォルトは詳細情報）
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "detail"
    
    if mode == "morning":
        # 朝9時の実行モード
        result = poster.morning_schedule()
    else:
        # 詳細情報の実行モード（デフォルト）
        result = poster.detail_schedule()
    
    print(result)
