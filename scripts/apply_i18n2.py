"""Одноразовый скрипт: язык, кнопка переключения и retranslate в ui.py."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / "app" / "ui.py"
source = path.read_text(encoding="utf-8")

# Язык из настроек до построения интерфейса.
old_settings = "        self.settings = app_settings()"
new_settings = (
    "        self.settings = app_settings()\n"
    '        set_language(str(self.settings.value("language", "ru")))'
)
assert old_settings in source
source = source.replace(old_settings, new_settings)

# Подпись авторов нужна для переперевода — сохраняем как атрибут.
old_credits = '        credits = QLabel(tr("credits"))'
new_credits = '        self.credits = QLabel(tr("credits"))'
assert old_credits in source
source = source.replace(old_credits, new_credits)
source = source.replace("        credits.setStyleSheet(", "        self.credits.setStyleSheet(")
source = source.replace("        credits.setAlignment(", "        self.credits.setAlignment(")
source = source.replace("        layout.addWidget(credits)", "        layout.addWidget(self.credits)")

# Placeholder при смене горячей клавиши.
old_apply = (
    '        self.text.setPlaceholderText(tr("placeholder", hotkey=spec.label()))'
)
assert old_apply in source

# Методы переключения языка и переперевода — перед _toggle_window.
old_anchor = "    def _toggle_window(self) -> None:"
new_methods = '''    def _toggle_language(self) -> None:
        lang = "en" if current_language() == "ru" else "ru"
        set_language(lang)
        self.settings.setValue("language", lang)
        self.retranslate()

    def retranslate(self) -> None:
        self.settings_btn.setToolTip(tr("btn.settings.tip"))
        self.language_btn.setText("RU" if current_language() == "en" else "EN")
        self.language_btn.setToolTip(tr("btn.language.tip"))
        self.compact_btn.setToolTip(tr("btn.compact.tip"))
        self.minimize_btn.setToolTip(tr("btn.minimize.tip"))
        self.settings_btn_c.setToolTip(tr("btn.settings.tip"))
        self.expand_btn.setToolTip(tr("btn.expand.tip"))
        self.minimize_btn_c.setToolTip(tr("btn.minimize.tip"))
        self.hotkey_hint.setToolTip(tr("hotkey.tip"))
        self.copy_btn.setText(tr("btn.copy"))
        self.clear_btn.setText(tr("btn.clear"))
        self.insert_check.setText(tr("btn.insert"))
        self.insert_check.setToolTip(tr("btn.insert.tip"))
        self.engine_btn.setToolTip(tr("btn.engine.tip"))
        self.engine_btn_compact.setToolTip(tr("btn.engine.tip"))
        self.text.setPlaceholderText(tr("placeholder", hotkey=self.hotkey.spec.label()))
        self.credits.setText(tr("credits"))
        self._update_mode_label()
        self.tray.retranslate()
        if not self.recorder.running and not self._processing:
            self.set_status(tr("status.ready"))
        else:
            self.set_status(tr("status.listening"))

    def _toggle_window(self) -> None:'''
assert old_anchor in source
source = source.replace(old_anchor, new_methods)

path.write_text(source, encoding="utf-8")
print("ui.py обновлён")
