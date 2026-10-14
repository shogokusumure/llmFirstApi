# AI Chat Test

## 起動方法

```bash
uv sync
uv run uvicorn aichattest.main:app --app-dir src --reload
```

APIドキュメントは起動後に <http://127.0.0.1:8000/docs> で確認できます。

## ドキュメントサイト

公開ドキュメント: <https://shogokusumure.github.io/llmFirstApi/>

GitHub Pages では API の OpenAPI 仕様と利用方法を公開します。API サーバー自体は公開せず、ローカルからのみ利用します。

```bash
uv sync --all-groups
uv run python scripts/export_openapi.py
uv run mkdocs serve
```

ブラウザーで <http://127.0.0.1:8000/> を開くと、ドキュメントサイトを確認できます。APIリファレンスはビルド時にアプリから生成するため、エンドポイントを変更した場合は OpenAPI 仕様も再生成してください。

### GitHub Pages への公開

このリポジトリでは GitHub Actions で Pages に自動公開します。`main` ブランチへの push 後、`Docs` ワークフローが成功するとサイトが更新されます。Pages の公開元はリポジトリの **Settings → Pages → Build and deployment → Source** で **GitHub Actions** に設定します。

GitHub Pages の公開範囲は GitHub プランによって異なります。標準の Pages 公開ではサイトはインターネット上で閲覧可能です。公開するドキュメントに秘密情報や実データを含めないでください。Pages のビルドでは OpenAPI 仕様とドキュメントのみを公開し、API サーバーは起動しません。

## データベース

- SQLiteファイル: `data/chat.db`
- スキーマ定義: `src/aichattest/migrations/*.sql`
- 適用済みマイグレーション: `schema_migrations` テーブル
- 会話と発言の内容はローカルDBに保存されます。DBファイルやバックアップはGitに登録しないでください。

### スキーマ変更の方針

1. `src/aichattest/migrations/` に、次の連番を使ったSQLファイルを追加します（例: `002_add_message_status.sql`）。
2. 変更内容は新しいSQLファイルに記述します。すでに適用済みのSQLファイルは編集・削除・改名しません。
3. マイグレーションSQLには `BEGIN` / `COMMIT` を書きません。アプリが適用記録と合わせてトランザクションで実行します。
4. アプリ起動時に、未適用のSQLファイルがファイル名順に一度だけ適用されます。適用状況は `schema_migrations` で確認できます。
5. マイグレーション後は、会話作成・メッセージ保存・履歴取得を確認してから変更を共有します。

適用済みの変更を取り消す場合も、過去のSQLを書き換えず、新しいマイグレーションで前向きに修正します。

### バックアップと復元

スキーマ変更など重要な作業の前には、アプリを停止してからDBファイルをコピーします。

```bash
cp data/chat.db data/chat.db.bak
```

復元する場合はアプリを停止し、バックアップを `data/chat.db` に戻してから起動します。起動時に未適用のマイグレーションが実行されるため、復元DBにも現在のスキーマ変更が反映される場合があります。

## API

- `POST /conversations`: 会話を作成
- `GET /conversations`: 会話一覧を取得
- `DELETE /conversations/{conversation_id}`: 会話とその発言を削除
- `POST /conversations/{conversation_id}/messages`: `user` または `assistant` の発言を保存
- `GET /conversations/{conversation_id}/messages`: 会話の発言を取得
- `POST /conversations/{conversation_id}/chat`: ユーザー発言を保存し、会話履歴をOllamaに渡して、返答を保存して返す

### Ollama

Ollamaを起動し、利用するモデルを取得してからAPIを起動します。

```bash
ollama serve
ollama pull gemma2:2b
uv run uvicorn aichattest.main:app --app-dir src --reload
```

接続先は `OLLAMA_BASE_URL`（既定値: `http://localhost:11434`）、モデルは `OLLAMA_MODEL`（既定値: `gemma2:2b`）で変更できます。チャットAPIのリクエスト例:

```json
{"content": "こんにちは"}
```

応答には保存された `user_message` と `assistant_message` が含まれます。Ollamaへの接続や応答形式に問題がある場合は `502` を返します。その場合もユーザー発言はDBに残り、履歴APIから確認できます。