# Maya FLAME Plug-in

Implements a deformer plug-in for the FLAME model.

### Requirements

FLAME repository:

    git clone git@github.com:Rubikplayer/flame-fitting.git

### Set Up

Create a conda environment with the environment.yml file, this will provide the python modules, which can be appended to the mayapy sys path.

Edit the path to the site-packages directory in flame_load.py

Edit the model path in flame_plugin.py

Place the flame_plugin.py and flame_load.py in the MAYA_PLUGIN_PATH

The plugin is implemented as a deformer, so requires a base mesh. One can be extracted using the helloworld.py example from the FLAME repo.

In Maya, with the imported mesh selected, issue:

    deformer -typ flameNode

The controls are accessed from the node's attribute editor in the normal way.


