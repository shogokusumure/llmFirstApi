import unittest
from unittest.mock import Mock, patch

from aichattest import main


class EntrypointTests(unittest.TestCase):
    @patch("aichattest.uvicorn.run")
    def test_main_binds_server_to_localhost(self, run: Mock) -> None:
        main()

        run.assert_called_once_with(
            "aichattest.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
        )


if __name__ == "__main__":
    unittest.main()
