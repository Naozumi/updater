# -*- mode: python -*-

block_cipher = None
path = 'D:\\Projects\\NordInvasion\\GIT-Updater-Private'

a = Analysis(['updater.py'],
             pathex=[path],
             binaries=None,
             datas=[
                 (path + '\\resource\\*', 'resource'),
                 (path + '\\resource\\lang\\*', 'resource\\lang'),
             ],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='updater.exe',
          debug=False,
          strip=None,
          upx=False,
          console=False , icon='resource\\favicon.ico')
