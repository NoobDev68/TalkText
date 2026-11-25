# -*- mode: python ; coding: utf-8 -*-
"""Сборка портативного TalkText: exe + _internal, модели ставятся рядом отдельно."""

from PyInstaller.utils.hooks import collect_all

datas = [
    ("resources/icon.png", "resources"),
    ("resources/logo.png", "resources"),
    ("resources/check.png", "resources"),
    ("vendor/onnx_asr-0.12.0.dist-info", "onnx_asr-0.12.0.dist-info"),
]
binaries = []
hiddenimports = ["onnx_asr"]

for package in ("silero_vad_lite", "certifi"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

a = Analysis(
    ["main.py"],
    pathex=["vendor"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=[
        "torch",
        "torchaudio",
        "transformers",
        "tensorflow",
        "tkinter",
        "pandas",
        "matplotlib",
        "gradio",
        "pydub",
        "pytest",
        "uvicorn",
        "websockets",
        "lxml",
        "pydantic",
        "rich",
        "orjson",
        "opentelemetry",
        "grpc",
        "fsspec",
        "anyio",
        "PIL",
        "IPython",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TalkText",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="resources/icon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TalkText",
)
