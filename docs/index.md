# AI Chat Test API

このサイトでは、ローカルで動作する AI Chat Test API の使い方と API 仕様を説明します。

## 概要

FastAPI と SQLite を使ったチャット API です。チャットエンドポイントは会話履歴を Ollama に送信し、生成された返答とユーザー発言をローカルのデータベースに保存します。

このドキュメントサイトは API サーバーをホストしません。API は開発者のローカル環境からのみ利用します。

## ローカルで起動する

依存関係をインストールし、Ollama と利用モデルを準備します。

```bash
uv sync
ollama serve
ollama pull gemma2:2b
```

別のターミナルで API を起動します。

```bash
uv run uvicorn aichattest.main:app --app-dir src --reload
```

ローカル API の Swagger UI は <http://127.0.0.1:8000/docs>、ヘルスチェックは <http://127.0.0.1:8000/health> です。

## 設定

- Ollama 接続先: `OLLAMA_BASE_URL`（既定値: `http://localhost:11434`）
- Ollama モデル: `OLLAMA_MODEL`（既定値: `gemma2:2b`）
- SQLite データベース: `data/chat.db`

チャット API が Ollama に接続できない場合は `502` を返します。その場合もユーザー発言はデータベースに保存され、会話の履歴 API から確認できます。

## API リファレンス

[API リファレンス](api.md)でエンドポイント、パラメーター、レスポンス形式を確認できます。
