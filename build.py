import PyInstaller.__main__
import os

# Asegúrate de que el directorio dist existe
if not os.path.exists('dist'):
    os.makedirs('dist')

PyInstaller.__main__.run([
    'src/main.py',
    '--name=3DPrinter',
    '--windowed',
    '--onefile',
    '--clean',
    '--add-data=src/ui/languages.py;ui',
    '--hidden-import=PyQt6',
    '--hidden-import=pymata4',
    '--hidden-import=serial',
    '--noconsole',
    '--icon=resources/icon.ico'
]) 