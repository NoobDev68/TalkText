"""Создаёт консольную копию spec для диагностики запуска exe."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / "TalkText.spec").read_text(encoding="utf-8")
debug = source.replace('name="TalkText"', 'name="TalkTextDebug"').replace("console=False", "console=True")
(ROOT / "TalkTextDebug.spec").write_text(debug, encoding="utf-8")
print("TalkTextDebug.spec готов")
