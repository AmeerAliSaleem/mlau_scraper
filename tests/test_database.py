"""Tests for database functions."""

from unittest.mock import MagicMock, patch
import pytest

from src.database import get_supabase_client

class TestGetSupabaseClient:
    """Test Supabase client creation."""

    @patch.dict(
        "os.environ", {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }
    )
    @patch("src.database.create_client")
    def test_get_supabase_client_with_credentials(self, mock_create_client: MagicMock) -> None:
        """Test get_supabase_client returns client when credentials are available."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        result = get_supabase_client()

        assert result is not None
        assert result == mock_client
        mock_create_client.assert_called_once_with("https://test.supabase.co", "test-key")

    @patch.dict("os.environ", {}, clear=True)
    def test_get_supabase_client_without_credentials(self) -> None:
        """Test get_supabase_client returns None when both credentials are missing."""
        result = get_supabase_client()
        assert result is None