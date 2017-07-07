# -*- mode: python -*-

block_cipher = None


a = Analysis(['ww-gui.py'],
             pathex=['C:\\Users\\Ben\\Desktop\\WW'],
             binaries=[],
             datas=[('icon.ico','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Assessment Disaggregation',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='icon.ico')
