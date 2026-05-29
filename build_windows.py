import os
import sys
import shutil
from pathlib import Path

def build_windows_exe():
    """Build SortThem as Windows executable"""

    # Clean previous builds
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=SortThem',
        '--onefile',           # Single executable file
        '--windowed',          # No console window (GUI app)
        '--noconfirm',         # Overwrite output directory
        '--log-level=INFO',

        # Add data files
        '--add-data=README.md;.',

        # Windows-specific
        '--uac-admin',         # Request admin privileges if needed
        '--version-file=version.txt',  # Version info

        # Optimizations
        '--strip',             # Strip debug symbols
        '--noupx',             # Don't use UPX compression

        # Hidden imports (if any)
        '--hidden-import=pygame',

        # Main script
        'main.py'
    ]

    # Add icon if exists
    if os.path.exists('resources/icon.ico'):
        cmd.insert(-1, f'--icon=resources/icon.ico')

    # Run PyInstaller
    os.system(' '.join(cmd))

    print(f"\nExecutable created at: dist/SortThem.exe")
    print(f"Size: {os.path.getsize('dist/SortThem.exe') / 1024 / 1024:.2f} MB")

def create_version_file():
    """Create version info file for Windows"""
    version_content = '''
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should always contain four items
    # FileVersion (1.0.0.0)
    filevers=(1, 0, 0, 0),
    # ProductVersion (1.0.0.0)
    prodvers=(1, 0, 0, 0),
    # Flag mask
    mask=0x3f,
    # Flags (debug, prerelease, etc.)
    flags=0x0,
    # OS (Windows GUI)
    OS=0x40004,
    # File type (application)
    fileType=0x1,
    # Subtype (not used)
    subtype=0x0,
    # Date (not used)
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'SortThem'),
         StringStruct(u'FileDescription', u'SortThem - Image Organizer'),
         StringStruct(u'FileVersion', u'1.0.0.0'),
         StringStruct(u'InternalName', u'SortThem'),
         StringStruct(u'LegalCopyright', u'Copyright © 2026'),
         StringStruct(u'OriginalFilename', u'SortThem.exe'),
         StringStruct(u'ProductName', u'SortThem'),
         StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    with open('version.txt', 'w') as f:
        f.write(version_content)

if __name__ == '__main__':
    create_version_file()
    build_windows_exe()
