# 🖼️ Gemini × LINE 展示情報通知Bot

## 📌 概要

このプロジェクトは、Google Gemini APIとLINE Messaging APIを用いて  
**東京で開催中の障がい者向け無料美術展情報を毎朝LINEに自動通知**するBotです。

- 🔍 GeminiがWebから展示情報を検索・要約
- 📩 LINEへわかりやすく整形された展示情報を送信
- 📁 情報はローカルファイルに保存し、後続処理に活用

## 🧰 使用技術

| ツール | 用途 |
|--------|------|
| Python | メインスクリプト実装 |
| Gemini API (Google Generative AI) | 展示情報の取得と要約 |
| LINE Messaging API | 通知メッセージ送信 |
| GitHub Actions | 毎朝の定時実行・スケジューリング管理 |
| GitHub Secrets | トークン等の機密情報管理 |

---

## 🔧 セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Secrets を GitHub に登録

GitHub のリポジトリ設定 → `Settings > Secrets and variables > Actions` にて以下を登録：

| 名称 | 内容 |
|------|------|
| `GEMINI_API_KEY` | Google Gemini API Key |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API トークン |
| `LINE_GROUP_ID` | 通知を送るグループのID |

### 3. Python環境構築（ローカルテスト用）

```bash
pip install -r requirements.txt
```

---

## 🚀 使用方法

### 展示情報を生成してLINEに送信（朝9時）

```bash
python src/post_exhibition_info.py summary
```

### 保存済みの展示リストから1件を詳細取得・要約・LINEに送信（10時〜14時）

```bash
python src/post_exhibition_info.py detail
```

---

## 🗓️ GitHub Actionsによるスケジューリング例

`.github/workflows/post-summary.yml`：

```yaml
schedule:
  - cron: '0 0 * * *'  # JST 9時（UTC 0時）に summary 実行
```

`.github/workflows/post-detail.yml`：

```yaml
schedule:
  - cron: '0 1-5 * * *'  # JST 10〜14時（UTC 1〜5時）に detail 実行
```

---

## 📁 ファイル構成

```plaintext
src/
  └ post_exhibition_info.py    # メイン処理（summary/detail切替）
  └ exhibition_message.txt     # 展示リスト保存ファイル
.github/
  └ workflows/
     ├ post-summary.yml        # summary 実行用 GitHub Actions
     └ post-detail.yml         # detail 実行用 GitHub Actions
README.md                      # このファイル
```

---

## 💡 今後の展望

- SlackやDiscordへの通知にも対応
- 障がい者向けイベントや福祉支援の情報にも拡張
- 利用者からのリクエスト対応（例：特定のジャンルのみ通知）
