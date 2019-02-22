# Maya FLAME Plug-in

Implements a deformer plug-in for the FLAME model.

### Requirements

FLAME repository:

    git clone git@github.com:Rubikplayer/flame-fitting.git

### Set Up

* Create a conda environment with the environment.yml file, this will provide the python modules, which can be appended to the mayapy sys path.

* A file, `userSetup.py`, is provided that shows an example of how to load modules from a virtual environment, this should be edited to include the path to your own virtual environment. This file should be placed in the `MAYA_SCRIPT_PATH`.

* Edit the model path in `flame_plugin.py` - future versions will load the model from the Maya interface.

* Place the `flame_plugin.py` in the `MAYA_PLUG_IN_PATH`.

* Place `flame_load.py` in Maya's `PYTHONPATH`. This can be set in a number of ways - the Maya documentation gives detailed examples. The provided `userSetup.py` can be used to achieve this.

### Usage

The first step is to load the plugin in the Maya workspace. Do this with:
Windows > Settings/Preferences > Plugin Manager, then selecting flame_plugin.py
in the dialogue. The plugin prints to console the path from which the model was loaded.

The plugin is implemented as a deformer, so requires a base mesh.
One can be extracted using the `helloworld.py` example from the FLAME repo. Or, there is a starter Maya scene file provided - `head.ma` that has an imported mesh in the scene.

In Maya, with the imported mesh selected, issue in the command line:

    deformer -typ flameNode

The controls are accessed from the node's attribute editor in the normal way.
