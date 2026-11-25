"""Одноразовый скрипт: переводит строки ui.py на i18n."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / "app" / "ui.py"
source = path.read_text(encoding="utf-8")

pairs = [
    (
        'self.text.setPlaceholderText(f"Нажмите ▶ или {self.hotkey.spec.label()} и говорите…")',
        'self.text.setPlaceholderText(tr("placeholder", hotkey=self.hotkey.spec.label()))',
    ),
    (
        'self.text.setPlaceholderText(f"Нажмите ▶ или {spec.label()} и говорите…")',
        'self.text.setPlaceholderText(tr("placeholder", hotkey=spec.label()))',
    ),
    ('self.copy_btn = QPushButton("Копировать")', 'self.copy_btn = QPushButton(tr("btn.copy"))'),
    ('self.clear_btn = QPushButton("Очистить")', 'self.clear_btn = QPushButton(tr("btn.clear"))'),
    (
        'self.engine_btn.setToolTip("Клик — режим языка: Авто RU/EN → Русский → English")',
        'self.engine_btn.setToolTip(tr("btn.engine.tip"))',
    ),
    ('self.insert_check = QCheckBox("Вставлять")', 'self.insert_check = QCheckBox(tr("btn.insert"))'),
    (
        'self.insert_check.setToolTip("Автоматически вставлять распознанный текст в активное окно")',
        'self.insert_check.setToolTip(tr("btn.insert.tip"))',
    ),
    ('credits = QLabel("Создатели: ThreeR и DeepSeek")', 'credits = QLabel(tr("credits"))'),
    (
        'self.settings_btn_c.setToolTip("Настройки")',
        'self.settings_btn_c.setToolTip(tr("btn.settings.tip"))',
    ),
    ('self.expand_btn.setToolTip("Полное окно с текстом")', 'self.expand_btn.setToolTip(tr("btn.expand.tip"))'),
    ('self.minimize_btn_c.setToolTip("Свернуть в трей")', 'self.minimize_btn_c.setToolTip(tr("btn.minimize.tip"))'),
    ('close_btn.setToolTip("Закрыть приложение")', 'close_btn.setToolTip(tr("btn.close.tip"))'),
    (
        'self.hotkey_hint.setToolTip("Текущая горячая клавиша (меняется в настройках)")',
        'self.hotkey_hint.setToolTip(tr("hotkey.tip"))',
    ),
    (
        'self.engine_btn_compact.setToolTip("Клик — режим языка: Авто → Русский → English")',
        'self.engine_btn_compact.setToolTip(tr("btn.engine.tip"))',
    ),
    ('self.engine_btn.setText(MODE_LABELS[mode])', 'self.engine_btn.setText(tr(MODE_KEYS[mode]))'),
    (
        'self.engine_btn_compact.setText(MODE_LABELS[mode])',
        'self.engine_btn_compact.setText(tr(MODE_KEYS[mode]))',
    ),
    (
        'self.set_status("Для английского установите Whisper base в настройках", "#ffd27a")',
        'self.set_status(tr("status.need_english"), "#ffd27a")',
    ),
    ('self.set_status("Готов")', 'self.set_status(tr("status.ready"))'),
    ('self.set_status("Слушаю…", "#c9d2ff")', 'self.set_status(tr("status.listening"), "#c9d2ff")'),
    ('self.set_status("Говорите…", "#8fb4ff")', 'self.set_status(tr("status.speaking"), "#8fb4ff")'),
    ('self.set_status("Распознаю…", "#ffd27a")', 'self.set_status(tr("status.recognizing"), "#ffd27a")'),
    ('self.set_status("Загружаю модель…", "#ffd27a")', 'self.set_status(tr("status.loading"), "#ffd27a")'),
    ('self.set_status(f"Готов{lang_suffix}")', 'self.set_status(f"{tr(\'status.ready\')}{lang_suffix}")'),
    ('self.set_status("Ошибка распознавания", "#ff8fa3")', 'self.set_status(tr("status.error"), "#ff8fa3")'),
    ('self.set_status("Выберите движок в настройках ⚙", "#ffd27a")', 'self.set_status(tr("status.choose_engine"), "#ffd27a")'),
    ('self.set_status("Нет движков — нажмите ⚙", "#ffd27a")', 'self.set_status(tr("status.no_engines"), "#ffd27a")'),
    ('self.set_status("Скопировано")', 'self.set_status(tr("status.copied"))'),
]

changed = 0
for old, new in pairs:
    if old in source:
        source = source.replace(old, new)
        changed += 1

path.write_text(source, encoding="utf-8")
print(f"заменено {changed} из {len(pairs)}")
