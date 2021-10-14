# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\joelc\\PycharmProjects\\RS_Logger'],
             binaries=[],
             datas=[('RSLogger\\img\\pause.png', 'RSLogger\\img'), ('RSLogger\\img\\rs_icon.ico', 'RSLogger\\img'), ('RSLogger\\img\\questionmark_15.png', 'RSLogger\\img'), ('RSLogger\\img\\record.png', 'RSLogger\\img'), ('RSLogger\\img\\refresh_15.png', 'RSLogger\\img')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='RSLogger',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='RSLogger\\img\\rs_icon.ico')
