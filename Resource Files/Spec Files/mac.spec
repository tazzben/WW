# -*- mode: python -*-

block_cipher = None


a = Analysis(['ww-gui.py'],
             pathex=['/Users/tazz/Dropbox/GUI WW/Application'],
             binaries=[],
             datas=[],
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
          console=False , icon='icon.icns')
app = BUNDLE(exe,
             name='Assessment Disaggregation.app',
             icon='icon.icns',
             info_plist={
                'NSHighResolutionCapable': 'True'
             },
             bundle_identifier='com.bensresearch.assessmentdisaggregation')
