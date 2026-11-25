"""Диалог выбора движков распознавания: описание, установка и удаление."""

from __future__ import annotations

import threading
import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import models
from .settings import app_settings
from .i18n import tr
from .autostart import is_enabled as autostart_enabled
from .autostart import set_enabled as set_autostart
from .hotkeys import (
    CTRL_ANY,
    CTRL_LEFT,
    CTRL_NONE,
    CTRL_RIGHT,
    MODIFIER_VKS,
    VK_LCONTROL,
    VK_RCONTROL,
    HotkeySpec,
)
from .style import check_qss

# Что предлагается скачать при первом запуске: русский GigaAM v3 и лёгкий
# английский Whisper base. Multilingual — только для казахского/киргизского/узбекского.
DEFAULT_KEYS = {"gigaam", "whisper_base"}

DIALOG_STYLE = """
QDialog { background: #14161c; }QLabel { color: #e8eaed; }
QLabel#dialogTitle { color: #e8eaed; font-size: 13pt; font-weight: 600; }
QLabel#dialogHint { color: #8b93a7; font-size: 9pt; }
QLabel#modelTitle { color: #e8eaed; font-size: 10pt; font-weight: 600; }
QLabel#modelBullet { color: #9aa3b8; font-size: 8.5pt; }
QLabel#modelStatus { color: #4fd1a5; font-size: 8.5pt; }
QLabel#modelStatusMissing { color: #8b93a7; font-size: 8.5pt; }
QFrame#modelCard { background: rgba(255, 255, 255, 0.035); border-radius: 10px; }
QCheckBox { color: #e8eaed; font-size: 9pt; }
QProgressBar {
    background: rgba(255, 255, 255, 0.06); border: none; border-radius: 3px;
    max-height: 6px; color: transparent;
}
QProgressBar::chunk { background: #5b7cfa; border-radius: 3px; }
QPushButton#primary {
    background: #5b7cfa; color: #ffffff; border: none; border-radius: 8px;
    padding: 7px 18px; font-size: 9.5pt; font-weight: 600;
}
QPushButton#primary:hover { background: #6c8cff; }
QPushButton#primary:disabled { background: #3a4160; color: #9aa3b8; }
QPushButton#secondary {
    background: rgba(255, 255, 255, 0.06); color: #c7cddb;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px; padding: 7px 14px; font-size: 9.5pt;
}
QPushButton#secondary:hover {
    background: rgba(255, 255, 255, 0.11); color: #e8eaed;
    border-color: rgba(255, 255, 255, 0.26);
}
QPushButton#secondary:disabled { color: #5c6373; border-color: rgba(255, 255, 255, 0.08); }
""" + check_qss()


class _Worker(threading.Thread):
    """Последовательная установка/удаление в фоне."""

    def __init__(self, dialog: "ModelsDialog", tasks: list[tuple[str, str]], cancel: threading.Event) -> None:
        super().__init__(daemon=True)
        self._dialog = dialog
        self._tasks = tasks
        self._cancel = cancel

    def run(self) -> None:
        try:
            for action, key in self._tasks:
                if self._cancel.is_set():
                    raise models.Cancelled("скачивание отменено")
                if action == "install":
                    models.install(key, self._dialog.on_progress, self._cancel)
                else:
                    models.uninstall(key)
            self._dialog.worker_done.emit("")
        except models.Cancelled:
            self._dialog.cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            self._dialog.worker_done.emit(str(exc))


class ModelsDialog(QDialog):
    worker_done = Signal(str)
    cancelled = Signal()

    DEFAULT_SIZE = (620, 702)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.title"))
        self.setModal(True)
        self.setMinimumWidth(620)
        self.setStyleSheet(DIALOG_STYLE)
        self._settings = app_settings()
        saved_geometry = self._settings.value("settings_geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(*self.DEFAULT_SIZE)
        self._checks: dict[str, QCheckBox] = {}
        self._status_labels: dict[str, QLabel] = {}
        self._delete_buttons: dict[str, QPushButton] = {}
        self._cards: dict[str, QFrame] = {}
        self._worker: _Worker | None = None
        self._cancel: threading.Event | None = None
        self._build()
        self.worker_done.connect(self._on_worker_done)
        self.cancelled.connect(self._on_cancelled)

    # --- интерфейс -------------------------------------------------------------

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        title = QLabel(tr("dlg.title"))
        title.setObjectName("dialogTitle")
        title.setStyleSheet("color: #e8eaed; font-size: 13pt; font-weight: 600;")
        layout.addWidget(title)

        hint = QLabel(tr("dlg.hint"))
        hint.setObjectName("dialogHint")
        hint.setStyleSheet("color: #8b93a7; font-size: 9pt;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        hotkey_row = QHBoxLayout()
        hotkey_row.setSpacing(8)
        hotkey_title = QLabel(tr("dlg.hotkey"))
        hotkey_title.setStyleSheet("color: #9aa3b8; font-size: 9pt;")
        self.hotkey_btn = QPushButton(self._hotkey().label())
        self.hotkey_btn.setObjectName("secondary")
        self.hotkey_btn.setToolTip("Нажмите, чтобы задать другую комбинацию")
        self.hotkey_btn.clicked.connect(self._start_capture)
        hotkey_row.addWidget(hotkey_title)
        hotkey_row.addWidget(self.hotkey_btn)
        hotkey_row.addStretch(1)
        layout.addLayout(hotkey_row)

        autostart_row = QHBoxLayout()
        autostart_title = QLabel(tr("dlg.autostart"))
        autostart_title.setStyleSheet("color: #9aa3b8; font-size: 9pt;")
        self.autostart_check = QCheckBox(tr("dlg.autostart.check"))
        self.autostart_check.setChecked(autostart_enabled())
        self.autostart_check.toggled.connect(self._on_autostart)
        autostart_row.addWidget(autostart_title)
        autostart_row.addWidget(self.autostart_check)
        autostart_row.addStretch(1)
        layout.addLayout(autostart_row)

        self._capturing = False
        self._ctrl_side = CTRL_NONE

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        content = QWidget()
        content.setStyleSheet("QWidget { background: transparent; }")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 4, 0, 4)
        content_layout.setSpacing(8)
        for spec in models.describe():
            content_layout.addWidget(self._model_card(spec))
        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("dialogHint")
        layout.addWidget(self.progress_label)

        buttons = QHBoxLayout()
        self.donate_btn = QPushButton(tr("dlg.donate"))
        self.donate_btn.setObjectName("secondary")
        self.donate_btn.setToolTip(tr("dlg.donate.tip"))
        self.donate_btn.clicked.connect(
            lambda: webbrowser.open("https://pay.cloudtips.ru/p/a87b504b")
        )
        buttons.addWidget(self.donate_btn)
        buttons.addStretch(1)
        self.cancel_btn = QPushButton(tr("dlg.cancel"))
        self.cancel_btn.setObjectName("secondary")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.apply_btn = QPushButton(tr("dlg.apply"))
        self.apply_btn.setObjectName("primary")
        self.apply_btn.clicked.connect(self._apply)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.apply_btn)
        layout.addLayout(buttons)

    def _model_card(self, spec: models.ModelSpec) -> QFrame:
        card = QFrame()
        card.setObjectName("modelCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)

        check = QCheckBox()
        first_run = not models.installed_keys()
        check.setChecked(
            models.installed(spec.key) or (first_run and spec.key in DEFAULT_KEYS)
        )
        self._checks[spec.key] = check
        row.addWidget(check, 0, Qt.AlignTop)

        column = QVBoxLayout()
        column.setSpacing(2)
        heading = QHBoxLayout()
        name = QLabel(tr(f"model.{spec.key}.title"))
        name.setObjectName("modelTitle")
        heading.addWidget(name)
        badge_text = tr(f"model.{spec.key}.badge")
        if badge_text != f"model.{spec.key}.badge":
            badge = QLabel(badge_text)
            badge.setObjectName("modelStatusMissing")
            badge.setStyleSheet(
                "color:#8fb4ff; background:rgba(91,124,250,0.15); border-radius:6px; padding:1px 7px;"
            )
            heading.addWidget(badge)
        if spec.recommended:
            recommended = QLabel(tr("dlg.recommended"))
            recommended.setStyleSheet(
                "color:#4fd1a5; background:rgba(79,209,165,0.14); border-radius:6px; padding:1px 7px;"
            )
            heading.addWidget(recommended)
        heading.addStretch(1)
        delete_btn = QPushButton(tr("dlg.delete"))
        delete_btn.setStyleSheet(
            "color:#ff8fa3; background:rgba(255,92,122,0.10);"
            " border:1px solid rgba(255,92,122,0.35); border-radius:6px;"
            " padding:2px 9px; font-size:8pt;"
        )
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setToolTip(tr("dlg.delete.tip"))
        delete_btn.setVisible(models.installed(spec.key))
        delete_btn.clicked.connect(lambda _=False, key=spec.key: self._on_delete(key))
        self._delete_buttons[spec.key] = delete_btn
        heading.addWidget(delete_btn)
        column.addLayout(heading)

        for number in (1, 2, 3):
            bullet = tr(f"model.{spec.key}.b{number}")
            if bullet == f"model.{spec.key}.b{number}":
                break
            label = QLabel("· " + bullet)
            label.setObjectName("modelBullet")
            label.setWordWrap(True)
            column.addWidget(label)

        status = QLabel()
        status.setObjectName("modelStatus")
        self._status_labels[spec.key] = status
        column.addWidget(status)
        self._update_status(spec)

        row.addLayout(column, 1)
        self._cards[spec.key] = card
        return card

    def _update_status(self, spec: models.ModelSpec) -> None:
        label = self._status_labels[spec.key]
        if models.installed(spec.key):
            label.setText(tr("dlg.installed", mb=models.disk_usage_mb(spec.key)))
            label.setObjectName("modelStatus")
            label.setStyleSheet("color: #4fd1a5; font-size: 8.5pt;")
        else:
            label.setText(tr("dlg.missing", mb=spec.size_mb))
            label.setStyleSheet("color: #8b93a7; font-size: 8.5pt;")

    # --- горячая клавиша ---------------------------------------------------------

    def _hotkey(self) -> HotkeySpec:
        return HotkeySpec.from_json(app_settings().value("hotkey"))

    def _start_capture(self) -> None:
        self._capturing = True
        self._ctrl_side = CTRL_NONE
        self.hotkey_btn.setText(tr("dlg.capture"))
        self.hotkey_btn.setStyleSheet("border-color: #8fb4ff;")
        self.setFocus()

    def _on_autostart(self, enabled: bool) -> None:
        try:
            set_autostart(enabled)
        except OSError as exc:
            QMessageBox.warning(
                self, tr("dlg.autostart"), tr("dlg.autostart.error", error=exc)
            )
            self.autostart_check.blockSignals(True)
            self.autostart_check.setChecked(not enabled)
            self.autostart_check.blockSignals(False)

    def _finish_capture(self, spec: HotkeySpec | None) -> None:
        self._capturing = False
        self._ctrl_side = CTRL_NONE
        current = self._hotkey()
        if spec is not None:
            app_settings().setValue("hotkey", spec.to_json())
            current = spec
        self.hotkey_btn.setText(current.label())
        self.hotkey_btn.setStyleSheet("")

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if not self._capturing:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Escape:
            self._finish_capture(None)
            return
        vk = event.nativeVirtualKey()
        if vk in (VK_LCONTROL, VK_RCONTROL):
            self._ctrl_side = CTRL_RIGHT if vk == VK_RCONTROL else CTRL_LEFT
            return
        if vk == 0 or vk in MODIFIER_VKS:
            return
        mods = event.modifiers()
        if mods & Qt.ControlModifier:
            ctrl = self._ctrl_side if self._ctrl_side else CTRL_ANY
        else:
            ctrl = CTRL_NONE
        spec = HotkeySpec(
            vk=vk,
            ctrl=ctrl,
            alt=bool(mods & Qt.AltModifier),
            shift=bool(mods & Qt.ShiftModifier),
            win=bool(mods & Qt.MetaModifier),
        )
        self._finish_capture(spec)

    # --- действия --------------------------------------------------------------

    def _apply(self) -> None:
        tasks: list[tuple[str, str]] = []
        to_remove: list[str] = []
        for key, check in self._checks.items():
            want = check.isChecked()
            have = models.installed(key)
            if want and not have:
                tasks.append(("install", key))
            elif not want and have:
                to_remove.append(key)

        if to_remove and not tasks:
            names = ", ".join(tr(f"model.{key}.title") for key in to_remove)
            answer = QMessageBox.question(
                self,
                tr("dlg.delete.title"),
                tr("dlg.delete.question", title=names),
            )
            if answer != QMessageBox.Yes:
                return

        tasks.extend(("remove", key) for key in to_remove)
        if not tasks:
            self.accept()
            return

        self._set_busy(True)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self._cancel = threading.Event()
        self._worker = _Worker(self, tasks, self._cancel)
        self._worker.start()

    def on_progress(self, key: str, done: int, total: int) -> None:
        percent = int(done * 100 / total) if total else 0
        self.progress.setValue(min(percent, 100))
        self.progress_label.setText(
            tr(
                "dlg.downloading",
                title=tr(f"model.{key}.title"),
                done=f"{done / 1048576:.0f}",
                total=f"{total / 1048576:.0f}",
                pct=percent,
            )
        )

    def _refresh_cards(self) -> None:
        for spec in models.describe():
            self._update_status(spec)
            self._checks[spec.key].setChecked(models.installed(spec.key))
            self._delete_buttons[spec.key].setVisible(models.installed(spec.key))

    def _on_delete(self, key: str) -> None:
        answer = QMessageBox.question(
            self,
            tr("dlg.delete.title"),
            tr("dlg.delete.question", title=tr(f"model.{key}.title")),
        )
        if answer != QMessageBox.Yes:
            return
        models.uninstall(key)
        self._refresh_cards()

    def _on_worker_done(self, error: str) -> None:
        self._cancel = None
        self._set_busy(False)
        self.progress.setVisible(False)
        self.progress_label.setText("")
        self._refresh_cards()
        if error:
            QMessageBox.warning(self, tr("dlg.error.title"), error)
            return
        self.accept()

    def _on_cancelled(self) -> None:
        self._cancel = None
        self._set_busy(False)
        self.progress.setVisible(False)
        self._refresh_cards()
        self.progress_label.setText(tr("dlg.cancelled"))

    def _set_busy(self, busy: bool) -> None:
        self.apply_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText(tr("dlg.cancel_download") if busy else tr("dlg.cancel"))
        for check in self._checks.values():
            check.setEnabled(not busy)

    def _on_cancel(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            if self._cancel is not None:
                self._cancel.set()
                self.cancel_btn.setText(tr("dlg.cancelling"))
                self.cancel_btn.setEnabled(False)
            return
        self.reject()

    def done(self, result: int) -> None:
        # Сохраняем размер и при «Применить», и при «Отмене», и при закрытии крестиком.
        if self._worker is None or not self._worker.is_alive():
            self._settings.setValue("settings_geometry", self.saveGeometry())
        super().done(result)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._worker is not None and self._worker.is_alive():
            event.ignore()
            return
        super().closeEvent(event)
