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
    "status.last": (
        "Последняя фраза: {engine} · язык {lang} · {sec:.2f} с",
        "Last phrase: {engine} · language {lang} · {sec:.2f} s",
    ),
    "status.no_engines": ("Нет движков — нажмите ⚙", "No engines — open settings ⚙"),
    "status.choose_engine": ("Выберите движок в настройках ⚙", "Choose an engine in settings ⚙"),
    "status.need_english": (
        "Для английского скачайте Whisper turbo (видеокарта) или small/base (процессор)",
        "For English download Whisper turbo (GPU) or small/base (CPU)",
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
    "btn.lang.tip": ("Язык распознавания", "Recognition language"),
    "btn.engine.tip": ("Движок распознавания", "Recognition engine"),
    "btn.picker.tip": (
        "Выбрать язык и движок распознавания",
        "Choose recognition language and engine",
    ),
    "mode.auto": ("Авто RU/EN", "Auto RU/EN"),
    "mode.ru": ("Русский", "Russian"),
    "mode.en": ("English", "English"),
    "menu.language": ("Язык", "Language"),
    "menu.engine": ("Движок", "Engine"),
    "engine.auto": ("Авто — по языку", "Auto — by language"),
    "engine.auto.short": ("Авто", "Auto"),
    "mode.auto.tip": (
        "Язык каждой фразы определяется автоматически: русская идёт в GigaAM, английская в Whisper",
        "Each phrase's language is detected: Russian goes to GigaAM, English to Whisper",
    ),
    "mode.ru.tip": ("Всё считать русским, определение языка не запускать", "Treat everything as Russian"),
    "mode.en.tip": ("Всё считать английским, определение языка не запускать", "Treat everything as English"),
    "engine.auto.tip": (
        "Подбирать движок под язык каждой фразы (рекомендуется)",
        "Pick the engine for each phrase's language (recommended)",
    ),
    "engine.gigaam.tip": (
        "Русский на процессоре: устойчив к шуму, всегда с пунктуацией",
        "Russian on the CPU: noise-resistant, always punctuated",
    ),
    "engine.whisper_ru.tip": (
        "Русский: лучший WER в тишине, но на шуме слабее GigaAM; нужна видеокарта",
        "Russian: best WER in a quiet room, weaker in noise than GigaAM; needs a GPU",
    ),
    "engine.whisper_turbo.tip": (
        "Английский: лучший WER и 0.3 с на фразу; нужна видеокарта",
        "English: best WER and 0.3 s per phrase; needs a GPU",
    ),
    "engine.whisper_small.tip": (
        "Английский без видеокарты; на процессоре ~6 с на фразу",
        "English without a GPU; ~6 s per phrase on the CPU",
    ),
    "engine.whisper_base.tip": (
        "Английский для слабых ПК: 102 МБ, 0.9 с на фразу",
        "English for weak PCs: 102 MB, 0.9 s per phrase",
    ),
    "engine.gigaam_ml.tip": (
        "Казахский, киргизский, узбекский; без пунктуации",
        "Kazakh, Kyrgyz, Uzbek; no punctuation",
    ),
    "engine.gigaam": ("GigaAM v3", "GigaAM v3"),
    "engine.gigaam.short": ("GigaAM", "GigaAM"),
    "engine.whisper_ru.short": ("Podlodka", "Podlodka"),
    "engine.whisper_turbo.short": ("turbo", "turbo"),
    "engine.whisper_small.short": ("small", "small"),
    "engine.whisper_base.short": ("base", "base"),
    "engine.gigaam_ml.short": ("Multilingual", "Multilingual"),
    "engine.whisper": ("Whisper large-v3", "Whisper large-v3"),
    "engine.whisper_ru": ("Whisper turbo RU (Podlodka)", "Whisper turbo RU (Podlodka)"),
    "engine.whisper_turbo": ("Whisper large-v3-turbo", "Whisper large-v3-turbo"),
    "engine.whisper_small": ("Whisper small", "Whisper small"),
    "engine.whisper_base": ("Whisper base", "Whisper base"),
    "engine.gigaam_ml": ("GigaAM Multilingual", "GigaAM Multilingual"),
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
    "btn.autoclear": ("Автоочистка", "Auto-clear"),
    "btn.autoclear.tip": (
        "Очищать историю перед каждой новой записью: остаётся только текст текущей диктовки",
        "Clear the history before each new recording: only the current dictation stays",
    ),
    "dlg.donate": ("Отблагодарить автора", "Support the author"),
    "dlg.donate.tip": ("Открыть страницу донатов в браузере", "Open the donation page in a browser"),
    "dlg.cancel": ("Отмена", "Cancel"),
    "dlg.apply": ("Применить", "Apply"),
    "dlg.delete": ("Удалить", "Delete"),
    "dlg.delete.tip": ("Удалить движок с диска", "Delete the engine from disk"),
    "dlg.recommended": ("Рекомендовано", "Recommended"),
    "dlg.recommend.tip": (
        "Подобрать движки под этот компьютер: видеокарта, память, свободное место",
        "Pick engines that fit this PC: GPU, memory, free disk space",
    ),
    "dlg.recommend.nothing": (
        "мало свободного места — ничего не отмечено",
        "not enough free disk space — nothing selected",
    ),
    "dlg.recommend.slow": (
        "видеокарты нет: английский будет считаться на процессоре — около 6 секунд на фразу",
        "no GPU: English will run on the CPU — about 6 seconds per phrase",
    ),
    "dlg.installed": ("Установлена · {mb} МБ на диске", "Installed · {mb} MB on disk"),
    "dlg.disabled": ("выключена", "disabled"),
    "dlg.use.tip": (
        "Использовать этот движок. Снятая галочка файлы не удаляет — движок просто "
        "пропадает из выбора в окне; удаление — кнопкой «Удалить»",
        "Use this engine. Unchecking keeps the files — the engine just disappears from "
        "the window's picker; use the Delete button to remove it",
    ),
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
        "Русский: GigaAM v3 — на процессоре и устойчив к шуму; Podlodka — точнее в тишине, "
        "но нужна видеокарта. Английский: turbo — лучший и требует видеокарту; small и base "
        "работают на процессоре (small точнее, base быстрее). Кнопка «Рекомендовано» подберёт "
        "набор под этот компьютер.",
        "Russian: GigaAM v3 runs on the CPU and handles noise; Podlodka is more accurate in a "
        "quiet room but needs a GPU. English: turbo is the best and needs a GPU; small and base "
        "run on the CPU (small is more accurate, base is faster). The “Recommended” button picks "
        "a set for this PC.",
    ),
    "dlg.hint.extra": (
        "Галочка значит «использовать движок»: снятая галочка ничего не удаляет, "
        "движок просто пропадает из выбора в окне. Удаление — кнопкой «Удалить».",
        "The checkbox means “use this engine”: unchecking removes nothing, the engine "
        "just disappears from the window's picker. Use the Delete button to remove files.",
    ),
    "dlg.autostart.error": (
        "Не удалось изменить автозапуск: {error}",
        "Could not change autostart: {error}",
    ),
    # движки
    "model.gigaam.title": ("GigaAM v3 — русский, по умолчанию", "GigaAM v3 — Russian, default"),
    "model.gigaam.badge": ("Русский", "Russian"),
    "model.gigaam.b1": (
        "Русский: WER 11.7% в тишине и 11.3% при шуме — не боится фона",
        "Russian: 11.7% WER in silence, 11.3% in noise — handles background well",
    ),
    "model.gigaam.b2": (
        "Всегда ставит пунктуацию и заглавные буквы; ~0.5 с на фразу",
        "Always adds punctuation and capitalization; ~0.5 s per phrase",
    ),
    "model.gigaam.b3": (
        "216 МБ, работает на процессоре — видеокарта не нужна",
        "216 MB, runs on the CPU — no GPU needed",
    ),
    "model.whisper_ru.title": (
        "Whisper-Podlodka-Turbo — русский для тихой комнаты",
        "Whisper-Podlodka-Turbo — Russian for a quiet room",
    ),
    "model.whisper_ru.badge": ("Русский", "Russian"),
    "model.whisper_ru.b1": (
        "Русский: WER 10.8% — лучший результат на чистой речи",
        "Russian: 10.8% WER — the best result on clean speech",
    ),
    "model.whisper_ru.b2": (
        "На шуме слабее GigaAM (17.6% против 11.3%) — берите для тишины",
        "Weaker than GigaAM in noise (17.6% vs 11.3%) — use it in a quiet room",
    ),
    "model.whisper_ru.b3": (
        "1.5 ГБ и видеокарта NVIDIA; английский — как turbo, с пунктуацией",
        "1.5 GB and an NVIDIA GPU; English is like turbo, with punctuation",
    ),
    "model.whisper_turbo.title": (
        "Whisper large-v3-turbo — английский, быстрый",
        "Whisper large-v3-turbo — English, fast",
    ),
    "model.whisper_turbo.badge": ("Английский", "English"),
    "model.whisper_turbo.b1": (
        "Английский: WER 2.9% на чистой речи, 4.9% на сложной — лучший",
        "English: 2.9% WER on clean speech, 4.9% on hard speech — the best",
    ),
    "model.whisper_turbo.b2": (
        "0.3 с на фразу на видеокарте; пунктуация и заглавные",
        "0.3 s per phrase on GPU; punctuation and capitalization",
    ),
    "model.whisper_turbo.b3": (
        "1.5 ГБ, видеокарта NVIDIA обязательна — без неё не заработает",
        "1.5 GB, an NVIDIA GPU is required — it won't run without one",
    ),
    "model.whisper_small.title": (
        "Whisper small — английский без видеокарты",
        "Whisper small — English without a GPU",
    ),
    "model.whisper_small.badge": ("Английский", "English"),
    "model.whisper_small.b1": (
        "Английский: WER 3.0% — точнее base, но грубее turbo",
        "English: 3.0% WER — better than base, rougher than turbo",
    ),
    "model.whisper_small.b2": (
        "На процессоре медленно: ~6 секунд на фразу (на видеокарте 0.2 с)",
        "Slow on the CPU: ~6 seconds per phrase (0.2 s on a GPU)",
    ),
    "model.whisper_small.b3": (
        "463 МБ; работает и на процессоре, и на видеокарте",
        "463 MB; works on the CPU and on a GPU",
    ),
    "model.whisper_base.title": ("Whisper base — английский, самый лёгкий", "Whisper base — English, the lightest"),
    "model.whisper_base.badge": ("Английский", "English"),
    "model.whisper_base.b1": (
        "Английский: WER 3.7% — грубее small, зато 0.9 с на фразу",
        "English: 3.7% WER — rougher than small but 0.9 s per phrase",
    ),
    "model.whisper_base.b2": (
        "102 МБ — вариант для очень слабых и старых ПК",
        "102 MB — the option for very weak and old PCs",
    ),
    "model.whisper_base.b3": (
        "Только процессор; пунктуацию и заглавные ставит",
        "CPU only; adds punctuation and capitalization",
    ),
    "model.gigaam_ml.title": (
        "GigaAM Multilingual — казахский, киргизский, узбекский",
        "GigaAM Multilingual — Kazakh, Kyrgyz, Uzbek",
    ),
    "model.gigaam_ml.badge": ("RU + EN", "RU + EN"),
    "model.gigaam_ml.b1": (
        "Единственный движок для казахского, киргизского и узбекского",
        "The only engine for Kazakh, Kyrgyz and Uzbek",
    ),
    "model.gigaam_ml.b2": (
        "Русский: WER 5.5% — лучший, но без пунктуации и заглавных",
        "Russian: 5.5% WER — the best, but no punctuation or capitalization",
    ),
    "model.gigaam_ml.b3": (
        "214 МБ, процессор; английский пишет кириллицей — не его случай",
        "214 MB, CPU; writes English in Cyrillic — not the one for English",
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
