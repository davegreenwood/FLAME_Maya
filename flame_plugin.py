import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.mel as mel
from flame_load import load_model, np

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

# TODO: Load model in the interface
model_path = '/Users/Shared/FLAME/generic_model.pkl'
model = load_model(model_path)
print 'model loaded from', model_path

# How many components will the plugin manipulate
N_POSE_CMP = 15
N_ID_CMP = 6
N_EXP_CMP = 6
# Scale each type of component to keep the sliders [-1, 1]
POSE_SCALE = 1.0
ID_SCALE = 3.0
EXP_SCALE = 3.0
# Maya prefers to fit on the grid nicely
GLB_SCALE = 10

# plug-in global variables
kAuthor = 'David Greenwood'
kVersion = '0.1'
kArch = 'Any'
kPluginId = OpenMaya.MTypeId(0xBEEF8)
kNodeName = 'flameNode'

# OpenMaya global values
kOutputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom
kInputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom
kInput = OpenMayaMPx.cvar.MPxGeometryFilter_input

# -----------------------------------------------------------------------------
# Plug-in Class
# -----------------------------------------------------------------------------


class FlameNode(OpenMayaMPx.MPxDeformerNode):

    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)

    @classmethod
    def nodeCreator(cls):
        '''Maya API node creator
        '''
        return OpenMayaMPx.asMPxPtr(cls())

    @classmethod
    def nodeInitializer(cls):
        '''
        Maya API node initialize, establish all the attributes
        '''
        floatattr = OpenMaya.MFnNumericAttribute()
        cls.pose_attrs = []
        cls.id_attrs = []
        cls.exp_attrs = []

        for i in range(1, N_POSE_CMP + 1):
            attr = floatattr.create('pose_component_{}'.format(i),
                                    'psc{}'.format(i),
                                    OpenMaya.MFnNumericData.kFloat, 0.0)
            floatattr.setKeyable(True)
            floatattr.setMin(-1.0)
            floatattr.setMax(1.0)
            cls.pose_attrs.append(attr)
            cls.addAttribute(attr)
            cls.attributeAffects(attr, kOutputGeom)

        for i in range(1, N_ID_CMP + 1):
            attr = floatattr.create('identity_component_{}'.format(i),
                                    'idc{}'.format(i),
                                    OpenMaya.MFnNumericData.kFloat, 0.0)
            floatattr.setKeyable(True)
            floatattr.setMin(-1.0)
            floatattr.setMax(1.0)
            cls.id_attrs.append(attr)
            cls.addAttribute(attr)
            cls.attributeAffects(attr, kOutputGeom)

        for i in range(1, N_EXP_CMP + 1):
            attr = floatattr.create('expression_component_{}'.format(i),
                                    'exc{}'.format(i),
                                    OpenMaya.MFnNumericData.kFloat, 0.0)
            floatattr.setKeyable(True)
            floatattr.setMin(-1.0)
            floatattr.setMax(1.0)
            cls.exp_attrs.append(attr)
            cls.addAttribute(attr)
            cls.attributeAffects(attr, kOutputGeom)

    def deform(self, pDataBlock, pGeometryIterator,
               pLocalToWorldMatrix, pGeometryIndex):
        ''' Deform each vertex using the geometry iterator. '''

        pose_values, n = [], N_POSE_CMP
        for attr in self.pose_attrs:
            handle = pDataBlock.inputValue(attr)
            value = handle.asFloat()
            pose_values.append(value * POSE_SCALE)
        model.pose[:n] = np.array(pose_values)[:]

        id_values, n = [], N_ID_CMP
        for attr in self.id_attrs:
            handle = pDataBlock.inputValue(attr)
            value = handle.asFloat()
            id_values.append(value * ID_SCALE)
        model.betas[:n] = np.array(id_values)[:]

        exp_values, n = [], N_EXP_CMP
        for attr in self.exp_attrs:
            handle = pDataBlock.inputValue(attr)
            value = handle.asFloat()
            exp_values.append(value * EXP_SCALE)
        model.betas[300:300 + n] = np.array(exp_values)[:]

        while not pGeometryIterator.isDone():
            vertexIndex = pGeometryIterator.index()
            x, y, z = (GLB_SCALE * model.r[vertexIndex][:3]).tolist()
            point = OpenMaya.MPoint(x, y, z)
            pGeometryIterator.setPosition(point)
            pGeometryIterator.next()
        pass


# -----------------------------------------------------------------------------
# initialize the script plug-in
# -----------------------------------------------------------------------------

def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(kNodeName, kPluginId,
                             FlameNode.nodeCreator,
                             FlameNode.nodeInitializer,
                             OpenMayaMPx.MPxNode.kDeformerNode)
    except:
        raise "Failed to register node: %s" % kNodeName


def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(kPluginId)
    except:
        raise "Failed to deregister node: %s" % kNodeName


# -----------------------------------------------------------------------------
# AE template mel NB. Maya needs to reboot to reflect changes in the mel_cmd
# -----------------------------------------------------------------------------

ae_ps_attr = 'editorTemplate  -label "POSE Comp {}" -addControl "psc{}";'
ae_ps_attrs = '\n\t'.join([ae_ps_attr.format(i, i)
                           for i in range(1, N_POSE_CMP + 1)])

ae_id_attr = 'editorTemplate  -label "ID Comp {}" -addControl "idc{}";'
ae_id_attrs = '\n\t'.join([ae_id_attr.format(i, i)
                           for i in range(1, N_ID_CMP + 1)])

ae_exp_attr = 'editorTemplate  -label "EXP Comp {}" -addControl "exc{}";'
ae_exp_attrs = '\n\t'.join([ae_exp_attr.format(i, i)
                            for i in range(1, N_EXP_CMP + 1)])

mel_cmd = '''
global proc AEflameNodeTemplate( string $nodeName ) {{
    editorTemplate -beginScrollLayout;
    editorTemplate -beginLayout "Pose" -collapse 0;
    {}
    editorTemplate -endLayout;
    editorTemplate -beginLayout "Identity" -collapse 0;
    {}
    editorTemplate -endLayout;
    editorTemplate -beginLayout "Expression" -collapse 0;
    {}
    editorTemplate -endLayout;
    AEdependNodeTemplate $nodeName;
    editorTemplate -addExtraControls;
    editorTemplate -endScrollLayout;
}}'''.format(ae_ps_attrs, ae_id_attrs, ae_exp_attrs)

mel.eval(mel_cmd)

# -----------------------------------------------------------------------------
# End
# -----------------------------------------------------------------------------
