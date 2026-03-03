# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para empacotar o backend FastAPI como executável Windows.
Uso: pyinstaller backend_server.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Coletar todos os submódulos necessários
hidden_imports = (
    collect_submodules('app') +
    collect_submodules('uvicorn') +
    collect_submodules('sqlalchemy') +
    collect_submodules('pydantic') +
    collect_submodules('pydantic_core') +
    collect_submodules('fastapi') +
    collect_submodules('starlette') +
    collect_submodules('passlib') +
    collect_submodules('jose') +
    collect_submodules('email_validator') +
    collect_submodules('slowapi') +
    collect_submodules('multipart') +
    collect_submodules('dotenv') +
    collect_submodules('httpx') +
    collect_submodules('anyio') +
    collect_submodules('reportlab') +
    collect_submodules('PIL') +
    [
        'aiosqlite',
        'bcrypt',
        'dbfread',
        'aiofiles',
        'pythonjsonlogger',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ]
)

# Coletar data files
datas = collect_data_files('pydantic') + collect_data_files('pydantic_core') + collect_data_files('reportlab')

a = Analysis(
    ['run_server.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LojaAPI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LojaAPI',
)
