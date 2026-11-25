"""Локализация интерфейса: русский и английский, переключение без перезапуска."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

# key: (русский, английский)
_STRINGS: dict[str, tuple[str, str]] = {
    # окно
    "placeholder": (
        "Нажмите ▶ или {hotkey} и говорите…",
        "Press ▶ or {hotkey} and speak…",
    ),
    "credits": ("Создатели: ThreeR и DeepSeek", "Creators: ThreeR and DeepSeek"),
    "status.ready": ("Готов", "Ready"),
    "status.listening": ("Слушаю…", "Listening…"),
    "status.speaking": ("Говорите…", "Speak…"),
    "status.recognizing": ("Распознаю…", "Recognizing…"),
    "status.loading": ("Загружаю модель…", "Loading model…"),
    "status.error": ("Ошибка распознавания", "Recognition error"),
    "status.copied": ("Скопировано", "Copied"),
    "status.no_engines": ("Нет движков — нажмите ⚙", "No engines — open settings ⚙"),
    "status.choose_engine": ("Выберите движок в настройках ⚙", "Choose an engine in settings ⚙"),
    "status.need_english": (
        "Для английского установите Whisper base в настройках",
        "Install Whisper base in settings for English",
    ),
    "status.hotkey_busy": (
        "Горячая клавиша занята другой программой",
        "The hotkey is taken by another app",
    ),
    "btn.copy": ("Копировать", "Copy"),
    "btn.clear": ("Очистить", "Clear"),
    "btn.insert": ("Вставлять", "Insert"),
    "btn.insert.tip": (
        "Автоматически вставлять распознанный текст в активное окно",
        "Automatically insert recognized text into the active window",
    ),
    "btn.engine.tip": (
        "Клик — режим языка: Авто RU/EN → Русский → English",
        "Click — language mode: Auto RU/EN → Russian → English",
    ),
    "mode.auto": ("Авто RU/EN", "Auto RU/EN"),
    "mode.ru": ("Русский", "Russian"),
    "mode.en": ("English", "English"),
    "btn.settings.tip": ("Настройки: движки и горячая клавиша", "Settings: engines and hotkey"),
    "btn.compact.tip": ("Компактный режим", "Compact mode"),
    "btn.expand.tip": ("Полное окно с текстом", "Full window with text"),
    "btn.minimize.tip": ("Свернуть в трей", "Minimize to tray"),
    "btn.close.tip": ("Закрыть приложение", "Close the app"),
    "btn.language.tip": ("Переключить язык интерфейса на English", "Switch interface language to Русский"),
    "hotkey.tip": (
        "Текущая горячая клавиша (меняется в настройках)",
        "Current hotkey (change it in settings)",
    ),
    # трей
    "tray.tooltip.ready": ("TalkText — готов", "TalkText — ready"),
    "tray.tooltip.recording": ("TalkText — слушаю", "TalkText — listening"),
    "tray.hide": ("Скрыть окно", "Hide window"),
    "tray.show": ("Показать окно", "Show window"),
    "tray.start": ("Начать распознавание", "Start recognition"),
    "tray.stop": ("Остановить распознавание", "Stop recognition"),
    "tray.quit": ("Закрыть TalkText", "Quit TalkText"),
    "tray.notify": (
        "Свёрнуто в трей. Клик по значку — вернуть окно.",
        "Minimized to tray. Click the icon to restore the window.",
    ),
    # настройки
    "dlg.title": ("Настройки", "Settings"),
    "dlg.hotkey": ("Горячая клавиша", "Hotkey"),
    "dlg.autostart": ("Автозапуск", "Autostart"),
    "dlg.autostart.check": ("Запускать при входе в Windows", "Run at Windows startup"),
    "dlg.donate": ("Отблагодарить автора", "Support the author"),
    "dlg.donate.tip": ("Открыть страницу донатов в браузере", "Open the donation page in a browser"),
    "dlg.cancel": ("Отмена", "Cancel"),
    "dlg.apply": ("Применить", "Apply"),
    "dlg.delete": ("Удалить", "Delete"),
    "dlg.delete.tip": ("Удалить движок с диска", "Delete the engine from disk"),
    "dlg.recommended": ("Рекомендовано", "Recommended"),
    "dlg.installed": ("Установлена · {mb} МБ на диске", "Installed · {mb} MB on disk"),
    "dlg.missing": ("Не установлена · потребуется ~{mb} МБ", "Not installed · ~{mb} MB to download"),
    "dlg.cancel_download": ("Отменить скачивание", "Cancel download"),
    "dlg.cancelling": ("Отменяю…", "Cancelling…"),
    "dlg.downloading": (
        "{title}: {done} из {total} МБ ({pct}%)",
        "{title}: {done} of {total} MB ({pct}%)",
    ),
    "dlg.cancelled": (
        "Скачивание отменено. Уже загруженное сохранено — можно продолжить позже.",
        "Download cancelled. Already downloaded is kept — you can continue later.",
    ),
    "dlg.delete.title": ("Удалить движок?", "Delete engine?"),
    "dlg.delete.question": (
        "Удалить «{title}» с диска?\nЕго можно будет скачать снова.",
        "Delete «{title}» from disk?\nYou can download it again.",
    ),
    "dlg.error.title": ("Ошибка загрузки", "Download error"),
    "dlg.capture": ("Нажмите комбинацию…", "Press a combination…"),
    "dlg.hint": (
        "Сбер-движки лучше понимают русский и работают без видеокарты. Whisper точнее "
        "на английском, но занимает ~4.7 ГБ и нужен GPU. Скачиваются только отмеченные варианты.",
        "Sber engines understand Russian better and work without a GPU. Whisper is more accurate "
        "in English but takes ~4.7 GB and needs a GPU. Only checked engines are downloaded.",
    ),
    "dlg.autostart.error": (
        "Не удалось изменить автозапуск: {error}",
        "Could not change autostart: {error}",
    ),
    # движки
    "model.gigaam.title": ("GigaAM v3 — русский", "GigaAM v3 — Russian"),
    "model.gigaam.badge": ("Русский", "Russian"),
    "model.gigaam.b1": ("Лучшее качество на русском языке", "Best quality for Russian"),
    "model.gigaam.b2": ("Ставит пунктуацию и заглавные буквы", "Adds punctuation and capitalization"),
    "model.gigaam.b3": (
        "Работает на процессоре — видеокарта не нужна",
        "Runs on the CPU — no GPU needed",
    ),
    "model.whisper.title": ("Whisper large-v3 — английский", "Whisper large-v3 — English"),
    "model.whisper.badge": ("Английский", "English"),
    "model.whisper.b1": (
        "Лучший английский: пунктуация, заглавные, имена",
        "Best English: punctuation, capitalization, names",
    ),
    "model.whisper.b2": (
        "Очень надёжен на шуме и сложной лексике",
        "Very robust on noise and hard vocabulary",
    ),
    "model.whisper.b3": (
        "Занимает ~4.7 ГБ и требует видеокарту NVIDIA",
        "Takes ~4.7 GB and needs an NVIDIA GPU",
    ),
    "model.whisper_base.title": ("Whisper base — английский, лёгкий", "Whisper base — English, light"),
    "model.whisper_base.badge": ("Английский", "English"),
    "model.whisper_base.b1": (
        "Английский с пунктуацией и заглавными, без видеокарты",
        "English with punctuation, no GPU required",
    ),
    "model.whisper_base.b2": (
        "Всего ~100 МБ — замена GigaAM Multilingual для английского",
        "Only ~100 MB — replaces GigaAM Multilingual for English",
    ),
    "model.whisper_base.b3": (
        "Слабее Whisper large-v3, но и места занимает в 45 раз меньше",
        "Weaker than Whisper large-v3 but 45× smaller",
    ),
    "model.gigaam_ml.title": (
        "GigaAM Multilingual — русский и английский",
        "GigaAM Multilingual — Russian and English",
    ),
    "model.gigaam_ml.badge": ("RU + EN", "RU + EN"),
    "model.gigaam_ml.b1": (
        "Распознаёт 5 языков: русский, английский, казахский, киргизский, узбекский",
        "Recognizes 5 languages: Russian, English, Kazakh, Kyrgyz, Uzbek",
    ),
    "model.gigaam_ml.b2": (
        "Не ставит пунктуацию и заглавные буквы",
        "No punctuation or capitalization",
    ),
    "model.gigaam_ml.b3": (
        "Для английского лучше Whisper base — Multilingual пишет его кириллицей",
        "For English use Whisper base — Multilingual writes it in Cyrillic",
    ),
    "model.cuda.title": (
        "Библиотеки NVIDIA (для Whisper)",
        "NVIDIA libraries (for Whisper)",
    ),
}

LANGUAGES = ("ru", "en")


class _I18n(QObject):
    changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._lang = "ru"

    @property
    def language(self) -> str:
        return self._lang

    def set_language(self, lang: str) -> None:
        if lang not in LANGUAGES or lang == self._lang:
            return
        self._lang = lang
        self.changed.emit(lang)

    def tr(self, key: str, **kwargs: object) -> str:
        pair = _STRINGS.get(key)
        if pair is None:
            return key
        text = pair[0] if self._lang == "ru" else pair[1]
        return text.format(**kwargs) if kwargs else text


i18n = _I18n()


def tr(key: str, **kwargs: object) -> str:
    return i18n.tr(key, **kwargs)


def set_language(lang: str) -> None:
    i18n.set_language(lang)


def current_language() -> str:
    return i18n.language
