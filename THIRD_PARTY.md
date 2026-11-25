# Сторонние компоненты TalkText

Сам TalkText распространяется по лицензии MIT — см. файл `LICENSE` рядом с программой.
Ниже перечислено, что ещё используется, под какими лицензиями и где эти лицензии
взять целиком.

## Входит в сборку (папка `_internal`)

| Компонент | Версия | Лицензия |
|---|---|---|
| PySide6 / Qt 6 | 6.12.0 | LGPL-3.0 (или GPL-3.0, или коммерческая) |
| onnx-asr | 0.12.0 | MIT |
| onnxruntime | 1.31.0 | MIT |
| faster-whisper | 1.2.1 | MIT |
| CTranslate2 | 4.8.5 | MIT |
| silero-vad-lite (Silero VAD) | 0.4.0 | MIT |
| sounddevice | 0.5.6 | MIT |
| PortAudio (внутри sounddevice) | — | MIT |
| NumPy | 2.5.4 | BSD-3-Clause |
| certifi | 2026.10.19 | MPL-2.0 |

Исходные тексты лицензий:

- LGPL-3.0 — <https://www.gnu.org/licenses/lgpl-3.0.txt>, условия Qt — <https://www.qt.io/licensing>
- MIT — <https://opensource.org/license/mit>
- BSD-3-Clause — <https://opensource.org/license/bsd-3-clause>
- MPL-2.0 — <https://www.mozilla.org/media/MPL/2.0/index.txt>

Библиотеки Qt лежат в `_internal` отдельными файлами DLL и по LGPL могут быть
заменены на совместимые сборки Qt 6.12. Исходный код TalkText открыт:
<https://github.com/NoobDev68/TalkText>.

## Движки — скачиваются по желанию, в архив программы не входят

| Движок | Откуда | Лицензия |
|---|---|---|
| GigaAM v3 | `istupakov/gigaam-v3-onnx` (на основе `ai-sage/GigaAM-v3`, Salute Developers) | MIT |
| GigaAM Multilingual | `istupakov/gigaam-multilingual-ctc-onnx` | MIT |
| Whisper base | `istupakov/whisper-base-onnx` (на основе `openai/whisper-base`) | Apache-2.0 |
| Whisper large-v3 | `Systran/faster-whisper-large-v3` (на основе `openai/whisper-large-v3`) | MIT |

- MIT / Apache-2.0 — <https://opensource.org/license/mit>, <https://www.apache.org/licenses/LICENSE-2.0>

## CUDA-библиотеки — только для Whisper на видеокарте NVIDIA

NVIDIA cuBLAS, cuDNN и CUDA Runtime скачиваются с PyPI по желанию пользователя и
распространяются по проприетарной лицензии NVIDIA (EULA, файл `License.txt` в
каждом пакете). В архив программы не входят, вместе с TalkText не лицензируются.

## Товарные знаки

Windows — товарный знак Microsoft Corporation. NVIDIA, CUDA, cuBLAS и cuDNN —
товарные знаки NVIDIA Corporation. Qt и PySide — товарные знаки The Qt Company.
Остальные названия принадлежат их владельцам.
