"""Плавающее окно диктовки: компактный и полный режимы."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import models, paths
from .settings import app_settings
from .audio import Recorder
from .dialogs import ModelsDialog
from .engines import Engines
from .hotkeys import GlobalHotkey, HotkeySpec
from .recognizer import MODE_AUTO, MODE_EN, MODE_RU, Recognizer
from .style import check_qss, gear_icon, mic_icon
from .tray import Tray
from .win import make_noactivate, paste_text

MODE_CYCLE = [MODE_AUTO, MODE_RU, MODE_EN]
MODE_LABELS = {
    MODE_AUTO: "Авто RU/EN",
    MODE_RU: "Русский",
    MODE_EN: "English",
}

COMPACT_SIZE = (216, 252)
FULL_SIZE = (480, 340)
MIN_FULL_SIZE = (420, 300)

STYLES = """
#card {
    background: rgba(18, 20, 26, 247);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
}
QLabel#title { color: #e8eaed; font-size: 10pt; font-weight: 600; }
QLabel#status { color: #8b93a7; font-size: 9pt; }
QLabel#statusCompact { color: #8b93a7; font-size: 8.5pt; }
QLabel#hotkeyHint { color: #9aa3b8; font-size: 9pt; }
QPushButton#close {
    color: #c7cddb; border: 1px solid rgba(255, 255, 255, 0.14);
    background: rgba(255, 255, 255, 0.06);
    font-size: 10.5pt; padding: 0; border-radius: 8px;
}
QPushButton#close:hover {
    color: #ff8fa3; background: rgba(255, 92, 122, 0.16);
    border-color: rgba(255, 92, 122, 0.5);
}
QPushButton#tool {
    color: #c7cddb; border: 1px solid rgba(255, 255, 255, 0.14);
    background: rgba(255, 255, 255, 0.06);
    font-size: 10pt; padding: 0; border-radius: 8px;
}
QPushButton#tool:hover {
    color: #e8eaed; background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.26);
}
QPushButton#mic {
    border: none; border-radius: 26px; background: #5b7cfa;
    color: #ffffff; font-size: 17px; padding: 0;
}
QPushButton#mic:hover { background: #6c8cff; }
QPushButton#mic[recording="true"] { background: #ff5c7a; }
QPushButton#mic[recording="true"]:hover { background: #ff738c; }
QPushButton#micBig {
    border: none; border-radius: 30px; background: #5b7cfa;
    color: #ffffff; font-size: 19px; padding: 0;
}
QPushButton#micBig:hover { background: #6c8cff; }
QPushButton#micBig[recording="true"] { background: #ff5c7a; }
QPushButton#micBig[recording="true"]:hover { background: #ff738c; }
QPushButton#engine {
    color: #e8eaed; background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 8px; padding: 4px 12px; font-size: 8.5pt;
}
QPushButton#engine:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(143, 180, 255, 0.55);
}
QPushButton#engine:focus { border-color: rgba(143, 180, 255, 0.7); }
QPushButton#engineCompact {
    color: #e8eaed; background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 7px; padding: 3px 8px; font-size: 8pt;
}
QPushButton#engineCompact:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(143, 180, 255, 0.55);
}
QPushButton.small {
    color: #c7cddb; background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.13);
    border-radius: 7px; padding: 4px 11px; font-size: 8.5pt;
}
QPushButton.small:hover {
    color: #e8eaed; background: rgba(255, 255, 255, 0.10);
    border-color: rgba(255, 255, 255, 0.24);
}
QCheckBox { color: #9aa3b8; font-size: 8.5pt; spacing: 6px; }
QCheckBox:disabled { color: #5c6373; }
QTextEdit {
    background: transparent; border: none; color: #dfe3ea;
    font-size: 10.5pt; selection-background-color: #3d55a8;
}
QMenu {
    background: #1b1e26; color: #e8eaed;
    border: 1px solid rgba(255, 255, 255, 0.10); padding: 4px;
}
QMenu::item { padding: 5px 16px; border-radius: 6px; }
QMenu::item:selected { background: rgba(255, 255, 255, 0.08); }
QMenu::separator { height: 1px; background: rgba(255, 255, 255, 0.08); margin: 4px 8px; }
""" + check_qss()


class LevelBar(QWidget):
    """Тонкая полоска громкости."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._value = 0.0
        self.setFixedHeight(4)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 16))
        p.drawRoundedRect(rect, 2, 2)
        if self._value > 0.005:
            w = max(3, int(rect.width() * self._value))
            p.setBrush(QColor("#5b7cfa"))
            p.drawRoundedRect(0, 0, w, rect.height(), 2, 2)


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TalkText")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMinimumSize(300, 100)

        self.settings = app_settings()
        self.engines = Engines()
        self.recognizer = Recognizer(self.engines)
        self.recorder = Recorder()
        self.hotkey = GlobalHotkey(HotkeySpec.from_json(self.settings.value("hotkey")))
        self.tray = Tray(self)
        self._drag_pos: QPoint | None = None
        self._models_ready = False
        self._processing = 0
        self._last_lang = ""
        self._quit_requested = False
        self._tray_hint_shown = False
        self._compact = self.settings.value("compact", True, type=bool)
        self._mode_index = min(int(self.settings.value("mode", 0)), len(MODE_CYCLE) - 1)
        stored_size = self.settings.value("size")
        self._full_size = (
            QSize(stored_size) if isinstance(stored_size, QSize) and not stored_size.isEmpty()
            else QSize(*FULL_SIZE)
        )
        self._resize_edges_set: set[str] = set()
        self._resize_start = QPoint()
        self._resize_geometry = QRect()
        self.setMouseTracking(True)

        self._build_ui()
        self._connect()
        self._restore_state()
        self.hotkey.start()
        self._reload_engines()
        make_noactivate(int(self.winId()))
        QTimer.singleShot(400, self._check_first_run)

    # --- построение интерфейса -------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)

        self.card = QFrame(self)
        self.card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(34)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 170))
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        card_layout.addWidget(self.stack)
        self.stack.addWidget(self._build_full_page())
        self.stack.addWidget(self._build_compact_page())

    def _build_full_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(6)
        logo = QLabel()
        logo_pixmap = QPixmap(str(paths.resource("logo.png")))
        if not logo_pixmap.isNull():
            logo.setPixmap(logo_pixmap.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo)
        title = QLabel("TalkText")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch(1)
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("tool")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setIcon(gear_icon())
        self.settings_btn.setIconSize(QSize(17, 17))
        self.settings_btn.setToolTip("Настройки: движки и горячая клавиша")
        self.compact_btn = QPushButton("⤡")
        self.compact_btn.setObjectName("tool")
        self.compact_btn.setFixedSize(28, 28)
        self.compact_btn.setToolTip("Компактный режим")
        self.minimize_btn = QPushButton("—")
        self.minimize_btn.setObjectName("tool")
        self.minimize_btn.setFixedSize(28, 28)
        self.minimize_btn.setToolTip("Свернуть в трей")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Закрыть приложение")
        header.addWidget(self.settings_btn)
        header.addWidget(self.compact_btn)
        header.addWidget(self.minimize_btn)
        header.addWidget(close_btn)
        layout.addLayout(header)

        main_row = QHBoxLayout()
        main_row.setSpacing(14)
        self.mic = QPushButton()
        self.mic.setObjectName("micBig")
        self.mic.setFixedSize(60, 60)
        self.mic.setIcon(mic_icon(False))
        self.mic.setIconSize(QSize(26, 26))
        self.mic.setCursor(Qt.PointingHandCursor)
        self.mic.setProperty("recording", False)
        main_row.addWidget(self.mic)

        info = QVBoxLayout()
        info.setSpacing(8)
        info.addStretch(1)
        self.status = QLabel("Готов")
        self.status.setObjectName("status")
        info.addWidget(self.status)
        self.level = LevelBar()
        info.addWidget(self.level)
        info.addStretch(1)
        main_row.addLayout(info, 1)
        layout.addLayout(main_row)

        self.text = QTextEdit()
        self.text.setObjectName("text")
        self.text.setReadOnly(True)
        self.text.setPlaceholderText(f"Нажмите ▶ или {self.hotkey.spec.label()} и говорите…")
        layout.addWidget(self.text, 1)

        footer = QHBoxLayout()
        footer.setSpacing(4)
        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.setProperty("class", "small")
        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.setProperty("class", "small")
        self.engine_btn = QPushButton()
        self.engine_btn.setObjectName("engine")
        self.engine_btn.setCursor(Qt.PointingHandCursor)
        self.engine_btn.setToolTip("Клик — режим языка: Авто RU/EN → Русский → English")
        self.insert_check = QCheckBox("Вставлять")
        self.insert_check.setToolTip("Автоматически вставлять распознанный текст в активное окно")
        footer.addWidget(self.copy_btn)
        footer.addWidget(self.clear_btn)
        footer.addStretch(1)
        footer.addWidget(self.engine_btn)
        footer.addWidget(self.insert_check)
        layout.addLayout(footer)

        credits = QLabel("Создатели: ThreeR и DeepSeek")
        credits.setStyleSheet("color: #5c6373; font-size: 7.5pt;")
        credits.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits)

        close_btn.clicked.connect(self._quit)
        return page

    def _build_compact_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 8, 14, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(4)
        self.settings_btn_c = QPushButton()
        self.settings_btn_c.setObjectName("tool")
        self.settings_btn_c.setFixedSize(24, 24)
        self.settings_btn_c.setIcon(gear_icon())
        self.settings_btn_c.setIconSize(QSize(14, 14))
        self.settings_btn_c.setToolTip("Настройки")
        self.expand_btn = QPushButton("⤢")
        self.expand_btn.setObjectName("tool")
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.setToolTip("Полное окно с текстом")
        self.minimize_btn_c = QPushButton("—")
        self.minimize_btn_c.setObjectName("tool")
        self.minimize_btn_c.setFixedSize(24, 24)
        self.minimize_btn_c.setToolTip("Свернуть в трей")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close")
        close_btn.setFixedSize(24, 24)
        close_btn.setToolTip("Закрыть приложение")
        top.addWidget(self.settings_btn_c)
        top.addWidget(self.expand_btn)
        top.addStretch(1)
        top.addWidget(self.minimize_btn_c)
        top.addWidget(close_btn)
        layout.addLayout(top)

        layout.addStretch(1)
        self.mic_compact = QPushButton()
        self.mic_compact.setObjectName("mic")
        self.mic_compact.setFixedSize(52, 52)
        self.mic_compact.setIcon(mic_icon(False))
        self.mic_compact.setIconSize(QSize(22, 22))
        self.mic_compact.setCursor(Qt.PointingHandCursor)
        self.mic_compact.setProperty("recording", False)
        layout.addWidget(self.mic_compact, 0, Qt.AlignHCenter)
        layout.addSpacing(2)

        self.hotkey_hint = QLabel(self.hotkey.spec.label())
        self.hotkey_hint.setObjectName("hotkeyHint")
        self.hotkey_hint.setAlignment(Qt.AlignCenter)
        self.hotkey_hint.setToolTip("Текущая горячая клавиша (меняется в настройках)")
        layout.addWidget(self.hotkey_hint)

        self.status_compact = QLabel("Готов")
        self.status_compact.setObjectName("statusCompact")
        self.status_compact.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_compact)

        self.level_compact = LevelBar()
        self.level_compact.setFixedWidth(118)
        layout.addWidget(self.level_compact, 0, Qt.AlignHCenter)
        layout.addStretch(1)

        self.engine_btn_compact = QPushButton()
        self.engine_btn_compact.setObjectName("engineCompact")
        self.engine_btn_compact.setCursor(Qt.PointingHandCursor)
        self.engine_btn_compact.setToolTip("Клик — режим языка: Авто → Русский → English")
        self.engine_btn_compact.setMinimumHeight(28)
        layout.addWidget(self.engine_btn_compact)

        close_btn.clicked.connect(self._quit)
        return page

    def _connect(self) -> None:
        for button in (self.mic, self.mic_compact):
            button.clicked.connect(self.toggle_recording)
        self.hotkey.activated.connect(self.toggle_recording)
        self.hotkey.failed.connect(lambda msg: self.set_status(msg, "#ff8fa3"))
        self.copy_btn.clicked.connect(self._copy_all)
        self.clear_btn.clicked.connect(self._clear)
        for button in (self.engine_btn, self.engine_btn_compact):
            button.clicked.connect(self._cycle_mode)
        for button in (self.settings_btn, self.settings_btn_c):
            button.clicked.connect(self._open_settings)
        self.compact_btn.clicked.connect(lambda: self.set_compact(True))
        self.expand_btn.clicked.connect(lambda: self.set_compact(False))
        for button in (self.minimize_btn, self.minimize_btn_c):
            button.clicked.connect(self._minimize_to_tray)
        self.tray.toggle_window.connect(self._toggle_window)
        self.tray.toggle_recording.connect(self.toggle_recording)
        self.tray.quit.connect(self._quit)
        self.recorder.segment_ready.connect(self._on_segment)
        self.recorder.level_changed.connect(self._on_level)
        self.recorder.speaking_changed.connect(self._on_speaking)
        self.recorder.error.connect(self._on_error)
        self.recognizer.results.connect(self._on_results)
        self.recognizer.ready.connect(self._on_models_ready)
        self.recognizer.error.connect(self._on_error)
        self.recognizer.language.connect(self._on_language)

    def _restore_state(self) -> None:
        self.insert_check.setChecked(self.settings.value("insert", True, type=bool))
        self._apply_compact(self._compact, save=False)
        # Стартуем в правом нижнем углу рабочей области — над часами, не закрывая панель задач.
        # Вокруг окна есть прозрачная тень (24 px), поэтому окно сдвигаем на её ширину:
        # карточка ложится впритык к краю, а тень справа и снизу обрезается экраном.
        area = QGuiApplication.primaryScreen().availableGeometry()
        shadow = 24
        self.move(
            area.right() - self.width() + shadow + 1,
            area.bottom() - self.height() + shadow + 1,
        )
        self._update_mode_label()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        make_noactivate(int(self.winId()))
        self.tray.set_window_visible(True)

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        self.tray.set_window_visible(False)

    # --- окно и трей -----------------------------------------------------------

    def set_compact(self, compact: bool) -> None:
        if compact == self._compact:
            return
        self._apply_compact(compact, save=True)

    def _apply_compact(self, compact: bool, *, save: bool) -> None:
        self._compact = compact
        self.stack.setCurrentIndex(1 if compact else 0)
        if compact:
            self.setMinimumSize(*COMPACT_SIZE)
            self.setMaximumSize(COMPACT_SIZE[0], COMPACT_SIZE[1])
            self.resize(*COMPACT_SIZE)
        else:
            self.setMinimumSize(*MIN_FULL_SIZE)
            self.setMaximumSize(16777215, 16777215)
            self.resize(self._full_size)
        self._clamp_to_screen()
        if save:
            self.settings.setValue("compact", compact)

    def _clamp_to_screen(self) -> None:
        screen = QGuiApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        x = min(max(self.x(), area.left()), area.right() - self.width())
        y = min(max(self.y(), area.top()), area.bottom() - self.height())
        self.move(x, y)

    def _toggle_window(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def _minimize_to_tray(self) -> None:
        self.hide()
        if not self._tray_hint_shown:
            self._tray_hint_shown = True
            self.tray.notify("Свёрнуто в трей. Клик по значку — вернуть окно.")

    def _quit(self) -> None:
        self._quit_requested = True
        self._save_state()
        self.hotkey.stop()
        self.recorder.stop()
        self.tray.hide()
        QApplication.quit()

    def _save_state(self) -> None:
        if not self._compact:
            self._full_size = self.size()
        self.settings.setValue("size", self._full_size)
        self.settings.setValue("insert", self.insert_check.isChecked())
        self.settings.setValue("mode", self._mode_index)

    # --- язык и режим ----------------------------------------------------------

    def current_mode(self) -> str:
        return MODE_CYCLE[self._mode_index]

    def _cycle_mode(self) -> None:
        self._mode_index = (self._mode_index + 1) % len(MODE_CYCLE)
        self.settings.setValue("mode", self._mode_index)
        self._update_mode_label()
        self.recognizer.preload(self._preload_for_mode())
        if self.current_mode() == MODE_EN and not ({"whisper", "whisper_base"} & models.available_engines()):
            self.set_status("Для английского установите Whisper base в настройках", "#ffd27a")

    def _preload_for_mode(self) -> list[str]:
        mode = self.current_mode()
        available = models.available_engines()
        if mode == MODE_RU:
            order = ["gigaam", "gigaam_ml", "whisper", "whisper_base"]
        elif mode == MODE_EN:
            order = ["whisper", "whisper_base", "gigaam_ml"]
        else:
            order = ["whisper", "gigaam", "whisper_base", "gigaam_ml"]
        return [key for key in order if key in available]

    def _update_mode_label(self) -> None:
        mode = self.current_mode()
        self.engine_btn.setText(MODE_LABELS[mode])
        self.engine_btn_compact.setText(MODE_LABELS[mode])

    def _on_language(self, lang: str) -> None:
        self._last_lang = lang

    # --- запись ----------------------------------------------------------------

    def toggle_recording(self) -> None:
        if self.recorder.running:
            self.recorder.stop()
            self._set_recording_visual(False)
            self.tray.set_recording(False)
            if not self._processing and self._models_ready:
                self.set_status("Готов")
            self._on_level(0.0)
            return
        self.recorder.start()
        if not self.recorder.running:
            return
        self._set_recording_visual(True)
        self.tray.set_recording(True)
        self.set_status("Слушаю…", "#c9d2ff")

    def _set_recording_visual(self, recording: bool) -> None:
        for button, size in ((self.mic, 26), (self.mic_compact, 22)):
            button.setIcon(mic_icon(recording))
            button.setIconSize(QSize(size, size))
            button.setProperty("recording", recording)
            self._repolish(button)

    def _on_level(self, value: float) -> None:
        self.level.set_value(value)
        self.level_compact.set_value(value)

    def _on_speaking(self, speaking: bool) -> None:
        if not self.recorder.running:
            return
        if speaking:
            self.set_status("Говорите…", "#8fb4ff")
        else:
            self.set_status("Слушаю…", "#c9d2ff")

    def _on_segment(self, audio) -> None:
        self._processing += 1
        self.set_status("Распознаю…", "#ffd27a")
        self.recognizer.submit(audio, self.current_mode())

    # --- результаты -------------------------------------------------------------

    def _on_results(self, results) -> None:
        self._processing = max(0, self._processing - 1)
        lang_suffix = f" · {self._last_lang.upper()}" if self._last_lang else ""
        if not self._models_ready:
            self.set_status("Загружаю модель…", "#ffd27a")
        elif self.recorder.running:
            self.set_status("Слушаю…", "#c9d2ff")
        else:
            self.set_status(f"Готов{lang_suffix}")

        _short, _lang, text, error, _elapsed = results[0]
        if error:
            self._append_error(error)
            return
        self._append_text(text)
        if self.insert_check.isChecked():
            paste_text(text)

    def _append_text(self, text: str) -> None:
        if not text:
            return
        if self.text.toPlainText().strip():
            self.text.append("")
        self.text.insertPlainText(text)
        self._scroll_bottom()

    def _append_error(self, error: str) -> None:
        self.text.append(f"<div style='color:#ff8fa3;font-size:9pt'>{_escape(error)}</div>")
        self._scroll_bottom()
        self.set_status("Ошибка распознавания", "#ff8fa3")

    def _scroll_bottom(self) -> None:
        QTimer.singleShot(0, self._do_scroll_bottom)

    def _do_scroll_bottom(self) -> None:
        bar = self.text.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_models_ready(self) -> None:
        self._models_ready = True
        if not self.recorder.running and not self._processing:
            self.set_status("Готов")

    def _on_error(self, message: str) -> None:
        self.set_status(message, "#ff8fa3")
        self._append_error(message)

    # --- настройки и первый запуск -----------------------------------------------

    def _check_first_run(self) -> None:
        if models.available_engines():
            return
        self.set_status("Выберите движок в настройках ⚙", "#ffd27a")
        self._open_settings()

    def _open_settings(self) -> None:
        dialog = ModelsDialog(self)
        dialog.exec()
        self._apply_hotkey(HotkeySpec.from_json(self.settings.value("hotkey")))
        self._reload_engines()

    def _apply_hotkey(self, spec: HotkeySpec) -> None:
        self.hotkey.set_spec(spec)
        self.settings.setValue("hotkey", spec.to_json())
        self.text.setPlaceholderText(f"Нажмите ▶ или {spec.label()} и говорите…")
        self.hotkey_hint.setText(spec.label())

    def _reload_engines(self) -> None:
        available = models.available_engines()
        self._models_ready = False
        if not available:
            self.set_status("Нет движков — нажмите ⚙", "#ffd27a")
            return
        self.recognizer.preload(self._preload_for_mode())

    # --- сервис ----------------------------------------------------------------

    def set_status(self, text: str, color: str = "#8b93a7") -> None:
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {color};")
        short = text.rstrip("…")
        self.status_compact.setText(short)
        self.status_compact.setStyleSheet(f"color: {color};")

    def _copy_all(self) -> None:
        text = self.text.toPlainText().strip()
        if text:
            QGuiApplication.clipboard().setText(text)
            self.set_status("Скопировано")

    def _clear(self) -> None:
        self.text.clear()
        if not self.recorder.running:
            self.set_status("Готов")

    @staticmethod
    def _repolish(widget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def closeEvent(self, event) -> None:  # noqa: N802
        # Крестик (и Alt+F4) закрывает программу; свернуть в трей — кнопка «—».
        event.accept()
        self._quit()

    # --- перетаскивание и изменение размера окна ----------------------------------

    RESIZE_EDGE = 7

    def _is_interactive(self, pos: QPoint) -> bool:
        node = self.childAt(pos)
        while node is not None and node is not self.card:
            if isinstance(node, (QPushButton, QCheckBox, QTextEdit)):
                return True
            node = node.parentWidget()
        return False

    def _edges_at(self, pos: QPoint) -> set[str]:
        if self._compact:
            return set()
        g = self.card.geometry()
        edges: set[str] = set()
        if abs(pos.x() - g.left()) <= self.RESIZE_EDGE:
            edges.add("left")
        if abs(pos.x() - g.right()) <= self.RESIZE_EDGE:
            edges.add("right")
        if abs(pos.y() - g.top()) <= self.RESIZE_EDGE:
            edges.add("top")
        if abs(pos.y() - g.bottom()) <= self.RESIZE_EDGE:
            edges.add("bottom")
        return edges

    @staticmethod
    def _resize_cursor(edges: set[str]):
        if edges in ({"left", "top"}, {"right", "bottom"}):
            return Qt.SizeFDiagCursor
        if edges in ({"right", "top"}, {"left", "bottom"}):
            return Qt.SizeBDiagCursor
        if edges & {"left", "right"}:
            return Qt.SizeHorCursor
        return Qt.SizeVerCursor

    def _resize_to(self, global_pos: QPoint) -> None:
        delta = global_pos - self._resize_start
        rect = QRect(self._resize_geometry)
        if "left" in self._resize_edges_set:
            rect.setLeft(rect.left() + delta.x())
        if "right" in self._resize_edges_set:
            rect.setRight(rect.right() + delta.x())
        if "top" in self._resize_edges_set:
            rect.setTop(rect.top() + delta.y())
        if "bottom" in self._resize_edges_set:
            rect.setBottom(rect.bottom() + delta.y())
        min_w, min_h = MIN_FULL_SIZE
        if rect.width() < min_w:
            if "left" in self._resize_edges_set:
                rect.setLeft(rect.right() - min_w + 1)
            else:
                rect.setRight(rect.left() + min_w - 1)
        if rect.height() < min_h:
            if "top" in self._resize_edges_set:
                rect.setTop(rect.bottom() - min_h + 1)
            else:
                rect.setBottom(rect.top() + min_h - 1)
        self.setGeometry(rect)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        edges = self._edges_at(pos)
        if event.button() == Qt.LeftButton and edges:
            self._resize_edges_set = edges
            self._resize_start = event.globalPosition().toPoint()
            self._resize_geometry = self.geometry()
            return
        if event.button() == Qt.LeftButton and not self._is_interactive(pos):
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        if self._resize_edges_set:
            self._resize_to(event.globalPosition().toPoint())
        elif self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        else:
            edges = self._edges_at(pos)
            if edges:
                self.setCursor(self._resize_cursor(edges))
            elif not self._is_interactive(pos):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._resize_edges_set:
            self._resize_edges_set = set()
            if not self._compact:
                self._full_size = self.size()
            self.unsetCursor()
        self._drag_pos = None
        super().mouseReleaseEvent(event)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
