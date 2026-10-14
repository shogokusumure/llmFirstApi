import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient

from aichattest import database
from aichattest.main import app


class ChatEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_dir = Path(self.temp_dir.name)
        self.db_dir_patch = patch.object(database, "DB_DIR", db_dir)
        self.db_path_patch = patch.object(database, "DB_PATH", db_dir / "chat.db")
        self.db_dir_patch.start()
        self.db_path_patch.start()
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()
        response = self.client.post("/conversations")
        self.conversation_id = response.json()["id"]

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.db_path_patch.stop()
        self.db_dir_patch.stop()
        self.temp_dir.cleanup()

    @staticmethod
    def ollama_response(content: str) -> httpx.Response:
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": content}},
            request=httpx.Request("POST", "http://localhost:11434/api/chat"),
        )

    @patch("aichattest.llm.httpx.post")
    def test_chat_saves_both_messages_and_sends_history(self, post: Mock) -> None:
        post.side_effect = [self.ollama_response("こんにちは"), self.ollama_response("はい、どうぞ")]

        first_response = self.client.post(
            f"/conversations/{self.conversation_id}/chat",
            json={"content": "こんにちは"},
        )
        second_response = self.client.post(
            f"/conversations/{self.conversation_id}/chat",
            json={"content": "質問があります"},
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.json()["assistant_message"]["content"], "はい、どうぞ")
        sent_messages = post.call_args_list[1].kwargs["json"]["messages"]
        self.assertEqual(
            sent_messages,
            [
                {"role": "user", "content": "こんにちは"},
                {"role": "assistant", "content": "こんにちは"},
                {"role": "user", "content": "質問があります"},
            ],
        )
        history = self.client.get(f"/conversations/{self.conversation_id}/messages")
        self.assertEqual([message["role"] for message in history.json()], ["user", "assistant", "user", "assistant"])

    @patch("aichattest.llm.httpx.post")
    def test_ollama_failure_keeps_user_message(self, post: Mock) -> None:
        post.side_effect = httpx.ConnectError(
            "Ollama is unavailable",
            request=httpx.Request("POST", "http://localhost:11434/api/chat"),
        )

        response = self.client.post(
            f"/conversations/{self.conversation_id}/chat",
            json={"content": "保存されますか"},
        )

        self.assertEqual(response.status_code, 502)
        history = self.client.get(f"/conversations/{self.conversation_id}/messages")
        self.assertEqual([message["role"] for message in history.json()], ["user"])
        self.assertEqual(history.json()[0]["content"], "保存されますか")

    @patch("aichattest.llm.httpx.post")
    def test_chat_returns_not_found_without_calling_ollama(self, post: Mock) -> None:
        response = self.client.post("/conversations/missing/chat", json={"content": "Hello"})

        self.assertEqual(response.status_code, 404)
        post.assert_not_called()

    def test_delete_conversation_removes_conversation_and_messages(self) -> None:
        message_response = self.client.post(
            f"/conversations/{self.conversation_id}/messages",
            json={"role": "user", "content": "削除対象"},
        )
        self.assertEqual(message_response.status_code, 201)

        response = self.client.delete(f"/conversations/{self.conversation_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertNotIn(
            self.conversation_id,
            [conversation["id"] for conversation in self.client.get("/conversations").json()],
        )
        with database.get_db_connection() as connection:
            message_count = connection.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                (self.conversation_id,),
            ).fetchone()[0]
        self.assertEqual(message_count, 0)
        self.assertEqual(
            self.client.get(f"/conversations/{self.conversation_id}/messages").status_code,
            404,
        )

    def test_delete_missing_conversation_returns_not_found(self) -> None:
        response = self.client.delete("/conversations/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Conversation not found")


if __name__ == "__main__":
    unittest.main()
