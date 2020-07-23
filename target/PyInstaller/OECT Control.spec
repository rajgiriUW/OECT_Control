# -*- mode: python -*-

block_cipher = None


a = Analysis(['C:\\DATA\\Linda\\OECT\\OECT_Control\\src\\main\\python\\KeithleyApp.py'],
             pathex=['C:\\DATA\\Linda\\OECT\\OECT_Control\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=['ipykernel.datapub', 'ipython', 'qtconsole', 'pyvisa'],
             hookspath=['c:\\users\\gingerlab\\.julia\\conda\\3\\envs\\python36\\lib\\site-packages\\fbs\\freeze\\hooks'],
             runtime_hooks=['C:\\DATA\\Linda\\OECT\\OECT_Control\\target\\PyInstaller\\fbs_pyinstaller_hook.py'],
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
          name='OECT Control',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True , icon='C:\\DATA\\Linda\\OECT\\OECT_Control\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='OECT Control')
