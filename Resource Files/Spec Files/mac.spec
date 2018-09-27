# -*- mode: python -*-

block_cipher = None


a = Analysis(['ww-gui.py'],
             pathex=['/Users/tazz/Dropbox/GUI WW'],
             binaries=[],
             datas=[],
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
          [],
          exclude_binaries=True,
          name='Assessment Disaggregation',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Assessment Disaggregation')
app = BUNDLE(coll,
             name='Assessment Disaggregation.app',
             icon='icon.icns',
             info_plist={
                'NSHighResolutionCapable': 'True'
             },
             bundle_identifier='com.bensresearch.assessmentdisaggregation')
