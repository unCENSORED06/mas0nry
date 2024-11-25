# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['mas0nry.py'],  # Your script name
    pathex=['.'],  # Path where your script is located
    binaries=[],  # Remove this as we're adding the assets via `datas`
    datas=[  # Use this for adding data files (like images, audio, etc.)
        ('mas0nry.png', '.'),  # Image file
        ('about.wav', '.'),    # Audio file
    ],
    hiddenimports=[  # Ensure all necessary libraries are included
        'flask',           # Flask web framework
        'werkzeug',        # Flask server dependencies
        'jinja2',          # Flask templating engine
        'itsdangerous',    # Flask security
        'flask.cli',       # Command-line interface for Flask
        'requests',        # Requests library for HTTP requests
        'PyQt6.QtWidgets', # PyQt6 UI elements
        'PyQt6.QtGui',     # PyQt6 GUI and widgets
        'PyQt6.QtCore',    # PyQt6 core components
        'PyQt6.QtMultimedia', # PyQt6 multimedia features
        'PyQt6.QtWebEngineWidgets',  # PyQt6 for web views
        'PyQt6.QtNetwork', # PyQt6 network features
        'PIL',             # Python Imaging Library (Pillow)
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # Binaries to include (none for now, since it's handled by `datas`)
    a.datas,  # Data files to include (in this case, assets like the image and audio)
    [],
    name='mas0nry',  # The name of the generated executable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to `True` if you want a console window, `False` for a windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
