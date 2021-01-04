# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
		 
a = Analysis(['TrxComAggregator.py'],
             pathex=['C:\\projects\\software\\TrxComAggregator'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='TrxComAggregator',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )

import shutil
shutil.copyfile('settings.cfg', '{0}/settings.cfg'.format(DISTPATH))
shutil.copyfile('logging.conf', '{0}/logging.conf'.format(DISTPATH))
