"""DTVoice Transcription History - Store and retrieve past transcriptions."""
import os
import json
import datetime
import logging
from typing import List, Optional

import config


class TranscriptionHistory:
    """Manages transcription history with JSON storage."""

    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self.history_file = os.path.join(config.CONFIG_DIR, "history.json")
        self._history: List[dict] = []
        self._load_history()

    def _load_history(self):
        """Load history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
            except (json.JSONDecodeError, OSError, IOError):
                self._history = []
        else:
            self._history = []

    def _save_history(self):
        """Save history to file."""
        os.makedirs(config.CONFIG_DIR, exist_ok=True)
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except (OSError, IOError) as e:
            logging.warning(f"Failed to save history: {e}")

    def add(self, text: str, model_id: Optional[str] = None, duration: Optional[float] = None):
        """Add a new transcription to history."""
        entry = {
            "id": len(self._history) + 1,
            "text": text,
            "timestamp": datetime.datetime.now().isoformat(),
            "model": model_id or config.DEFAULT_MODEL,
            "duration": duration,
            "char_count": len(text),
            "word_count": len(text.split()),
        }

        self._history.insert(0, entry)  # Most recent first

        # Trim to max entries
        if len(self._history) > self.max_entries:
            self._history = self._history[: self.max_entries]

        self._save_history()
        return entry

    def get_all(self) -> List[dict]:
        """Get all history entries."""
        return self._history.copy()

    def get_recent(self, count: int = 10) -> List[dict]:
        """Get recent N entries."""
        return self._history[:count].copy()

    def search(self, query: str) -> List[dict]:
        """Search history for text matching query."""
        query_lower = query.lower()
        return [entry for entry in self._history if query_lower in entry["text"].lower()]

    def delete(self, entry_id: int) -> bool:
        """Delete a history entry by ID."""
        original_len = len(self._history)
        self._history = [e for e in self._history if e["id"] != entry_id]
        if len(self._history) < original_len:
            self._save_history()
            return True
        return False

    def clear(self):
        """Clear all history."""
        self._history = []
        self._save_history()

    def get_stats(self) -> dict:
        """Get statistics about history."""
        if not self._history:
            return {
                "total": 0,
                "total_chars": 0,
                "total_words": 0,
                "avg_chars_per_entry": 0,
                "models_used": {},
            }

        total_chars = sum(e["char_count"] for e in self._history)
        total_words = sum(e["word_count"] for e in self._history)

        # Count models used
        models_used = {}
        for entry in self._history:
            model = entry.get("model", "unknown")
            models_used[model] = models_used.get(model, 0) + 1

        return {
            "total": len(self._history),
            "total_chars": total_chars,
            "total_words": total_words,
            "avg_chars_per_entry": total_chars // len(self._history),
            "models_used": models_used,
        }


# Global instance
_history_instance: Optional[TranscriptionHistory] = None


def get_history() -> TranscriptionHistory:
    """Get the global history instance."""
    global _history_instance
    if _history_instance is None:
        _history_instance = TranscriptionHistory()
    return _history_instance