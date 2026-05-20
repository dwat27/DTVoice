"""DTVoice Settings UI - Configuration window with tabs."""
import os
import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

import config
from i18n import get_i18n
from history import get_history

logger = logging.getLogger(__name__)


class SettingsWindow:
    """Settings window with tabbed interface."""

    def __init__(
        self,
        on_settings_changed: Optional[Callable] = None,
        on_model_changed: Optional[Callable] = None,
        on_theme_changed: Optional[Callable] = None,
    ):
        self.on_settings_changed = on_settings_changed
        self.on_model_changed = on_model_changed
        self.on_theme_changed = on_theme_changed

        self.i18n = get_i18n()
        self.settings = self._load_settings()

        # Create main window
        self.root = tk.Toplevel()
        self.root.title(self.i18n.get("settings_title", "Settings"))
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Set window icon (use default for now)
        self.root.transient()  # Make it modal

        self._create_widgets()
        self._load_current_settings()

    def _load_settings(self) -> dict:
        """Load settings from file or return defaults."""
        settings_file = os.path.join(config.CONFIG_DIR, "settings.json")
        defaults = {
            "language": "auto",
            "theme": "dark",
            "hotkey_modifier": "ctrl",
            "hotkey_key": "win",
            "auto_stop_seconds": 60,
            "silence_detection_seconds": 3,
            "output_mode": "injection",
        }

        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except (json.JSONDecodeError, OSError, IOError):
                pass

        return defaults

    def _save_settings(self):
        """Save settings to file."""
        settings_file = os.path.join(config.CONFIG_DIR, "settings.json")
        os.makedirs(config.CONFIG_DIR, exist_ok=True)
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            if self.on_settings_changed:
                self.on_settings_changed(self.settings)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _create_widgets(self):
        """Create the tabbed interface."""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: General
        self._create_general_tab(notebook)

        # Tab 2: Hotkey
        self._create_hotkey_tab(notebook)

        # Tab 3: Theme
        self._create_theme_tab(notebook)

        # Tab 4: Model
        self._create_model_tab(notebook)

        # Tab 5: History
        self._create_history_tab(notebook)

        # Bottom buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            button_frame,
            text=self.i18n.get("settings_save", "Save"),
            command=self._on_save,
        ).pack(side="right", padx=(5, 0))

        ttk.Button(
            button_frame,
            text=self.i18n.get("settings_cancel", "Cancel"),
            command=self.root.destroy,
        ).pack(side="right")

    def _create_general_tab(self, notebook):
        """General settings tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text=self.i18n.get("settings_tab_general", "General"))

        # Language selection
        ttk.Label(tab, text=self.i18n.get("settings_language", "Language")).grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.lang_var = tk.StringVar(value=self.settings.get("language", "auto"))
        lang_combo = ttk.Combobox(
            tab,
            textvariable=self.lang_var,
            values=["auto", "pt-BR", "en-US"],
            state="readonly",
            width=15,
        )
        lang_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Output mode
        ttk.Label(tab, text=self.i18n.get("settings_output_mode", "Output Mode")).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.output_var = tk.StringVar(value=self.settings.get("output_mode", "injection"))
        output_combo = ttk.Combobox(
            tab,
            textvariable=self.output_var,
            values=["injection", "clipboard", "popup"],
            state="readonly",
            width=15,
        )
        output_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Auto-stop timeout
        ttk.Label(tab, text=self.i18n.get("settings_auto_stop", "Auto-stop (seconds)")).grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.auto_stop_var = tk.IntVar(value=self.settings.get("auto_stop_seconds", 60))
        ttk.Spinbox(
            tab, from_=10, to=300, textvariable=self.auto_stop_var, width=15
        ).grid(row=2, column=1, sticky="w", pady=5)

        # Silence detection
        ttk.Label(tab, text=self.i18n.get("settings_silence", "Silence detection (s)")).grid(
            row=3, column=0, sticky="w", pady=5
        )
        self.silence_var = tk.IntVar(value=self.settings.get("silence_detection_seconds", 3))
        ttk.Spinbox(
            tab, from_=1, to=30, textvariable=self.silence_var, width=15
        ).grid(row=3, column=1, sticky="w", pady=5)

    def _create_hotkey_tab(self, notebook):
        """Hotkey settings tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text=self.i18n.get("settings_tab_hotkey", "Hotkey"))

        ttk.Label(
            tab,
            text=self.i18n.get("settings_hotkey_desc", "Current hotkey: Left Ctrl + Left Win"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)

        # Modifier keys
        ttk.Label(tab, text=self.i18n.get("settings_modifier", "Modifier")).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.modifier_var = tk.StringVar(value=self.settings.get("hotkey_modifier", "ctrl"))
        modifier_combo = ttk.Combobox(
            tab,
            textvariable=self.modifier_var,
            values=["ctrl", "alt", "shift"],
            state="readonly",
            width=15,
        )
        modifier_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Key
        ttk.Label(tab, text=self.i18n.get("settings_key", "Key")).grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.key_var = tk.StringVar(value=self.settings.get("hotkey_key", "win"))
        key_combo = ttk.Combobox(
            tab,
            textvariable=self.key_var,
            values=["win", "F1", "F2", "F3", "space"],
            state="readonly",
            width=15,
        )
        key_combo.grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(
            tab,
            text=self.i18n.get("settings_hotkey_warning", "Hotkey changes require restart"),
            font=("TkDefaultFont", 9, "italic"),
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(20, 5))

    def _create_theme_tab(self, notebook):
        """Theme settings tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text=self.i18n.get("settings_tab_theme", "Theme"))

        ttk.Label(tab, text=self.i18n.get("settings_theme", "Theme")).grid(
            row=0, column=0, sticky="w", pady=10
        )

        self.theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        ttk.Radiobutton(
            tab,
            text=self.i18n.get("settings_theme_light", "Light"),
            variable=self.theme_var,
            value="light",
        ).grid(row=1, column=0, sticky="w", pady=5, padx=20)

        ttk.Radiobutton(
            tab,
            text=self.i18n.get("settings_theme_dark", "Dark"),
            variable=self.theme_var,
            value="dark",
        ).grid(row=2, column=0, sticky="w", pady=5, padx=20)

        ttk.Radiobutton(
            tab,
            text=self.i18n.get("settings_theme_system", "System"),
            variable=self.theme_var,
            value="system",
        ).grid(row=3, column=0, sticky="w", pady=5, padx=20)

    def _create_model_tab(self, notebook):
        """Model selection tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text=self.i18n.get("settings_tab_model", "Model"))

        ttk.Label(tab, text=self.i18n.get("settings_select_model", "Select Model")).grid(
            row=0, column=0, sticky="w", pady=5
        )

        # Model list
        self.model_var = tk.StringVar(value=config.DEFAULT_MODEL)

        models_frame = ttk.Frame(tab)
        models_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)

        # Create treeview for models
        columns = ("name", "language", "size", "wer")
        self.model_tree = ttk.Treeview(models_frame, columns=columns, show="headings", height=8)

        self.model_tree.heading("name", text=self.i18n.get("model_name", "Name"))
        self.model_tree.heading("language", text=self.i18n.get("model_language", "Language"))
        self.model_tree.heading("size", text=self.i18n.get("model_size", "Size"))
        self.model_tree.heading("wer", text="WER")

        self.model_tree.column("name", width=200)
        self.model_tree.column("language", width=100)
        self.model_tree.column("size", width=80)
        self.model_tree.column("wer", width=60)

        # Scrollbar
        scrollbar = ttk.Scrollbar(models_frame, orient="vertical", command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=scrollbar.set)

        self.model_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Populate model list
        for model_id, model_info in config.WHISPER_MODELS.items():
            self.model_tree.insert(
                "",
                "end",
                values=(
                    model_info["display_name"],
                    model_info["language"],
                    f"{model_info['size_mb']} MB",
                    model_info["wer"],
                ),
                tags=(model_id,),
            )

        # Select current model
        for item in self.model_tree.get_children():
            if self.model_tree.item(item, "tags")[0] == config.DEFAULT_MODEL:
                self.model_tree.selection_set(item)
                self.model_tree.see(item)
                break

    def _create_history_tab(self, notebook):
        """History management tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text=self.i18n.get("settings_tab_history", "History"))

        # History stats
        stats_frame = ttk.LabelFrame(tab, text=self.i18n.get("history_stats", "Statistics"), padding=10)
        stats_frame.pack(fill="x", pady=(0, 10))

        self.history_stats_label = ttk.Label(stats_frame, text="")
        self.history_stats_label.pack(anchor="w")

        # Clear history button
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(
            btn_frame,
            text=self.i18n.get("history_clear", "Clear History"),
            command=self._on_clear_history,
        ).pack(side="left")

        ttk.Button(
            btn_frame,
            text=self.i18n.get("history_refresh", "Refresh"),
            command=self._refresh_history_stats,
        ).pack(side="left", padx=(5, 0))

        # History list
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill="both", expand=True)

        columns = ("text", "timestamp", "chars")
        self.history_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        self.history_tree.heading("text", text=self.i18n.get("history_text", "Text"))
        self.history_tree.heading("timestamp", text=self.i18n.get("history_timestamp", "Time"))
        self.history_tree.heading("chars", text=self.i18n.get("history_chars", "Chars"))

        self.history_tree.column("text", width=300)
        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("chars", width=80)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Initial load
        self._refresh_history_stats()

    def _refresh_history_stats(self):
        """Refresh history statistics and list."""
        try:
            history = get_history()
            stats = history.get_stats()

            # Update stats label
            stats_text = (
                f"Total: {stats['total']} | "
                f"Characters: {stats['total_chars']} | "
                f"Words: {stats['total_words']}"
            )
            self.history_stats_label.config(text=stats_text)

            # Clear and repopulate tree
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

            for entry in history.get_recent(50):
                # Truncate text for display
                text = entry.get("text", "")[:50] + "..." if len(entry.get("text", "")) > 50 else entry.get("text", "")
                timestamp = entry.get("timestamp", "")[:19]
                chars = entry.get("char_count", 0)

                self.history_tree.insert(
                    "",
                    "end",
                    values=(text, timestamp, chars),
                    tags=(str(entry.get("id", "")),),
                )
        except Exception as e:
            logger.warning(f"Failed to refresh history stats: {e}")
            self.history_stats_label.config(text="Error loading history")

    def _on_clear_history(self):
        """Handle clear history button click."""
        i18n = get_i18n()
        result = messagebox.askyesno(
            i18n.get("history_clear_confirm_title", "Clear History"),
            i18n.get("history_clear_confirm", "Are you sure you want to clear all history? This cannot be undone."),
        )

        if result:
            try:
                history = get_history()
                history.clear()
                self._refresh_history_stats()
                messagebox.showinfo(
                    i18n.get("history_cleared", "History Cleared"),
                    i18n.get("history_cleared_msg", "All history has been cleared."),
                )
            except Exception as e:
                logger.error(f"Failed to clear history: {e}")
                messagebox.showerror("Error", f"Failed to clear history: {e}")

    def _load_current_settings(self):
        """Load current settings into UI."""
        self.lang_var.set(self.settings.get("language", "auto"))
        self.output_var.set(self.settings.get("output_mode", "injection"))
        self.theme_var.set(self.settings.get("theme", "dark"))
        self.modifier_var.set(self.settings.get("hotkey_modifier", "ctrl"))
        self.key_var.set(self.settings.get("hotkey_key", "win"))

    def _on_save(self):
        """Handle save button click."""
        # Update settings
        self.settings["language"] = self.lang_var.get()
        self.settings["output_mode"] = self.output_var.get()
        self.settings["theme"] = self.theme_var.get()
        self.settings["hotkey_modifier"] = self.modifier_var.get()
        self.settings["hotkey_key"] = self.key_var.get()
        self.settings["auto_stop_seconds"] = self.auto_stop_var.get()
        self.settings["silence_detection_seconds"] = self.silence_var.get()

        # Get selected model
        selected = self.model_tree.selection()
        if selected:
            item = selected[0]
            model_id = self.model_tree.item(item, "tags")[0]
            self.settings["model"] = model_id

            if model_id != config.DEFAULT_MODEL and self.on_model_changed:
                self.on_model_changed(model_id)

        # Save to file
        self._save_settings()

        # Notify theme change
        if self.on_theme_changed and self.settings["theme"] != config.settings.get("theme", "dark"):
            self.on_theme_changed(self.settings["theme"])

        messagebox.showinfo(
            self.i18n.get("settings_saved", "Settings"),
            self.i18n.get("settings_saved_msg", "Settings saved successfully!"),
        )
        self.root.destroy()

    def get_current_settings(self) -> dict:
        """Get current settings as a dict."""
        return {
            "language": self.settings.get("language", "auto"),
            "theme": self.settings.get("theme", "dark"),
            "hotkey_modifier": self.settings.get("hotkey_modifier", "ctrl"),
            "hotkey_key": self.settings.get("hotkey_key", "win"),
            "auto_stop_seconds": self.settings.get("auto_stop_seconds", 60),
            "silence_detection_seconds": self.settings.get("silence_detection_seconds", 3),
            "output_mode": self.settings.get("output_mode", "injection"),
        }

    def show(self):
        """Show the settings window (blocking)."""
        self.root.wait_window()