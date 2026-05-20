"""Tests for history module."""
import os
import json
import tempfile
import shutil
import pytest
from history import TranscriptionHistory


class TestTranscriptionHistory:
    """Test TranscriptionHistory class."""

    @pytest.fixture
    def temp_config_dir(self, monkeypatch):
        """Create a temporary config directory."""
        temp_dir = tempfile.mkdtemp()
        import config
        monkeypatch.setattr(config, "CONFIG_DIR", temp_dir)
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def history(self, temp_config_dir):
        """Create a TranscriptionHistory instance with temp directory."""
        return TranscriptionHistory(max_entries=10)

    def test_add_increases_count(self, history):
        """Adding an entry should increase history count."""
        assert history.get_stats()["total"] == 0
        history.add("Hello world")
        assert history.get_stats()["total"] == 1

    def test_add_stores_text(self, history):
        """Added text should be stored correctly."""
        test_text = "Test transcription"
        history.add(test_text)
        recent = history.get_recent(1)
        assert recent[0]["text"] == test_text

    def test_add_includes_metadata(self, history):
        """Entry should include metadata."""
        test_text = "Test with metadata"
        entry = history.add(test_text, model_id="test/model", duration=1.5)

        assert "id" in entry
        assert "timestamp" in entry
        assert entry["model"] == "test/model"
        assert entry["duration"] == 1.5
        assert entry["char_count"] == len(test_text)
        assert entry["word_count"] == len(test_text.split())

    def test_get_recent_respects_count(self, history):
        """get_recent should return at most count entries."""
        for i in range(15):
            history.add(f"Text {i}")

        recent = history.get_recent(5)
        assert len(recent) == 5

    def test_max_entries_enforced(self, history):
        """History should not exceed max_entries."""
        for i in range(15):
            history.add(f"Text {i}")

        assert len(history.get_all()) == 10  # max_entries is 10

    def test_search_finds_text(self, history):
        """search should find matching entries."""
        history.add("Hello world")
        history.add("Goodbye world")
        history.add("Hello there")

        results = history.search("Hello")
        assert len(results) == 2

    def test_search_case_insensitive(self, history):
        """search should be case insensitive."""
        history.add("HELLO world")
        results = history.search("hello")
        assert len(results) == 1

    def test_delete_removes_entry(self, history):
        """delete should remove entry by ID."""
        entry = history.add("To be deleted")
        entry_id = entry["id"]

        assert history.delete(entry_id) is True
        assert history.get_stats()["total"] == 0

    def test_delete_invalid_id_returns_false(self, history):
        """delete with invalid ID should return False."""
        history.add("Test")
        assert history.delete(9999) is False

    def test_clear_removes_all(self, history):
        """clear should remove all entries."""
        history.add("Entry 1")
        history.add("Entry 2")
        history.clear()
        assert history.get_stats()["total"] == 0

    def test_get_stats_empty(self, history):
        """get_stats should return valid stats for empty history."""
        stats = history.get_stats()
        assert stats["total"] == 0
        assert stats["total_chars"] == 0
        assert stats["total_words"] == 0
        assert isinstance(stats["models_used"], dict)

    def test_get_stats_with_entries(self, history):
        """get_stats should calculate correct stats."""
        history.add("Hello world", duration=1.0)
        history.add("Goodbye world friend", duration=2.0)

        stats = history.get_stats()
        assert stats["total"] == 2
        assert stats["total_chars"] == 29  # 11 + 18
        assert "remynd/whisper-small-pt" in stats["models_used"]

    def test_entries_ordered_by_recent(self, history):
        """Most recent entries should come first."""
        history.add("First")
        history.add("Second")
        history.add("Third")

        recent = history.get_recent(3)
        assert recent[0]["text"] == "Third"
        assert recent[1]["text"] == "Second"
        assert recent[2]["text"] == "First"

    def test_persistence(self, temp_config_dir):
        """History should persist across instances."""
        history1 = TranscriptionHistory()
        history1.add("Persistent entry")

        # Create new instance with same config dir
        history2 = TranscriptionHistory()
        assert history2.get_stats()["total"] == 1
        assert history2.get_recent(1)[0]["text"] == "Persistent entry"