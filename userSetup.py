# this file should be stored in, or symlinked from:
# ~/Library/Preferences/Autodesk/maya/<Version>/scripts/

import sys
import maya.cmds as cmds

env_packages = '/Users/Shared/anaconda/envs/maya2018/lib/python2.7/site-packages'
maya_python_path = '/Users/Shared/Autodesk/maya/python'
sys.path.insert(0, env_packages)
sys.path.insert(0, maya_python_path)

# Uncomment the following two lines to open ports for an external editor:
# cmds.commandPort(name='localhost:7001', sourceType='mel', echoOutput=True)
# cmds.commandPort(name='localhost:7002', sourceType='python', echoOutput=True)

msg = '--------------------------------------------------------------------\n'
msg += 'userSetup.py\n'
msg += '--------------------------------------------------------------------\n'

cmds.evalDeferred('print msg')
