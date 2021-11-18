# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\joelc\\AppData\\Local\\Programs\\Python\\Python37-32\\lib\\site-packages\\cv2'],
             binaries=[],
             datas=[('rs_icon.ico', '.'), ('RSLogger\\img\\questionmark_15.png', 'RSLogger\\img'), ('RSLogger\\img\\record.png', 'RSLogger\\img'), ('RSLogger\\img\\pause.png', 'RSLogger\\img'), ('C:\\Users\\joelc\\AppData\\Local\\Programs\\Python\\Python37-32\\lib\\site-packages\\cv2\\opencv_videoio_ffmpeg454.dll', '.')],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
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
          name='RS_Logger',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='rs_icon.ico')
