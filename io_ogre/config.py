import bpy, os, sys, logging, pickle, mathutils
from pprint import pprint
from bpy.props import *

logger = logging.getLogger('config')

AXIS_MODES =  [
    ('xyz', 'xyz', 'no swapping'),
    ('xz-y', 'xz-y', 'ogre standard'),
    ('-xzy', '-xzy', 'non standard'),
]

MESH_TOOL_VERSIONS = [
    ('v1', 'v1', 'Export the mesh as a v1 object'),
    ('v2', 'v2', 'Export the mesh as a v2 object')
]

TANGENT_MODES =  [
    ('0', 'none', 'do not export'),
    ('3', 'generate', 'generate'),
    ('4', 'generate with parity', 'generate with parity')
]

CONFIG_PATH = bpy.utils.user_resource('CONFIG', path='scripts', create=True)
CONFIG_FILENAME = 'io_ogre.pickle'
CONFIG_FILEPATH = os.path.join(CONFIG_PATH, CONFIG_FILENAME)

_CONFIG_DEFAULTS_ALL = {
    # General
    'SWAP_AXIS' : 'xyz', # ogre standard is 'xz-y', but swapping is currently broken
    'MESH_TOOL_VERSION' : 'v2',
    'XML_DELETE' : True,
    
    # Scene
    'SCENE' : True,
    'SELECTED_ONLY' : True,
    'EXPORT_HIDDEN' : True,
    #'EXPORT_USER' : True,
    'FORCE_CAMERA' : True,
    'FORCE_LAMPS' : True,
    'NODE_ANIMATION' : True,
    #'NODE_KEYFRAMES' : False,
    
    # Materials
    'MATERIALS' : True,
    'COPY_SHADER_PROGRAMS' : True,
    'SEPARATE_MATERIALS' : True,
    'USE_FFP_PARAMETERS': False,
    
    # Textures
    'MAX_TEXTURE_SIZE' : 4096,
    'FORCE_IMAGE_FORMAT' : 'NONE',
    'TOUCH_TEXTURES' : True,
    'DDS_MIPS' : 16,
    
    # Armature
    'ONLY_DEFORMABLE_BONES' : False,
    'ONLY_KEYFRAMED_BONES' : False,
    'OGRE_INHERIT_SCALE' : False,
    'ARMATURE_ANIMATION' : True,
    'TRIM_BONE_WEIGHTS' : 0.01,
    'ONLY_KEYFRAMES' : False,

    # Mesh
    'MESH' : True,
    'MESH_OVERWRITE' : True,
    'ARRAY' : True,
    'EXTREMITY_POINTS' : 0,
    'GENERATE_EDGE_LISTS' : False,
    'GENERATE_TANGENTS' : "0",
    'OPTIMISE_ANIMATIONS' : True,
    'INTERFACE_TOGGLE': False,
    'OPTIMISE_VERTEX_BUFFERS' : True,
    'OPTIMISE_VERTEX_BUFFERS_OPTIONS' : 'puqs',
    
    # LOD
    'LOD_LEVELS' : 0,
    'LOD_DISTANCE' : 300,
    'LOD_PERCENT' : 40,
    'LOD_MESH_TOOLS' : False,
    
    # Pose Animation
    'SHAPE_ANIMATIONS' : True,
    'SHAPE_NORMALS' : True,
    
    # Logging
    'ENABLE_LOGGING' : False,
    #'DEBUG_LOGGING' : False,
    'SHOW_LOG_NAME' : False,
    
    # Import
    'IMPORT_NORMALS' : True,
    'MERGE_SUBMESHES' : True,
    'IMPORT_ANIMATIONS' : True,
    'ROUND_FRAMES' : True,
    'USE_SELECTED_SKELETON' : True,
    'IMPORT_SHAPEKEYS' : True
}

_CONFIG_TAGS_ = 'OGRETOOLS_XML_CONVERTER OGRETOOLS_MESH_UPGRADER MESH_PREVIEWER IMAGE_MAGICK_CONVERT USER_MATERIALS SHADER_PROGRAMS'.split()

''' todo: Change pretty much all of these windows ones. Make a smarter way of detecting
    Ogre tools from various default folders. Also consider making a installer that
    ships Ogre cmd line tools to ease the setup steps for end users. '''

_CONFIG_DEFAULTS_WINDOWS = {
    'OGRETOOLS_XML_CONVERTER' : 'C:\\OgreCommandLineTools\\OgreXMLConverter.exe',
    'OGRETOOLS_MESH_UPGRADER' : 'C:\\OgreCommandLineTools\\OgreMeshUpgrader.exe',
    'MESH_PREVIEWER' : 'ogre-meshviewer.bat',
    'IMAGE_MAGICK_CONVERT' : 'C:\\Program Files\\ImageMagick\\convert.exe',
    'USER_MATERIALS' : '',
    'SHADER_PROGRAMS' : 'C:\\'
}

_CONFIG_DEFAULTS_UNIX = {
    # do not use absolute paths like /usr/bin/exe_name. some distris install to /usr/local/bin ...
    # just trust the env PATH variable
    'IMAGE_MAGICK_CONVERT' : 'convert',
    'OGRETOOLS_XML_CONVERTER' : 'OgreXMLConverter',
    'OGRETOOLS_MESH_UPGRADER' : 'OgreMeshUpgrader',
    'MESH_PREVIEWER' : 'ogre-meshviewer',
    'USER_MATERIALS' : '',
    'SHADER_PROGRAMS' : '~/',
    #'USER_MATERIALS' : '~/ogre_src_v1-7-3/Samples/Media/materials',
    #'SHADER_PROGRAMS' : '~/ogre_src_v1-7-3/Samples/Media/materials/programs',
}

# Unix: Replace ~ with absolute home dir path
if sys.platform.startswith('linux') or sys.platform.startswith('darwin') or sys.platform.startswith('freebsd'):
    for tag in _CONFIG_DEFAULTS_UNIX:
        path = _CONFIG_DEFAULTS_UNIX[ tag ]
        if path.startswith('~'):
            _CONFIG_DEFAULTS_UNIX[ tag ] = os.path.expanduser( path )
        elif tag.startswith('OGRETOOLS') and not os.path.isfile( path ):
            _CONFIG_DEFAULTS_UNIX[ tag ] = os.path.join( '/usr/bin', os.path.split( path )[-1] )
    del tag
    del path


## PUBLIC API continues

def load_config():
    config_dict = {}

    # Check if the config file exists and load it
    if os.path.isfile( CONFIG_FILEPATH ):
        try:
            with open( CONFIG_FILEPATH, 'rb' ) as f:
                config_dict = pickle.load( f )
        except:
            logger.error('Can not read config from %s' % CONFIG_FILEPATH)

    # Load default values from _CONFIG_DEFAULTS_ALL if they don't exist after loading config from file
    for tag in _CONFIG_DEFAULTS_ALL:
        if tag not in config_dict:
            config_dict[ tag ] = _CONFIG_DEFAULTS_ALL[ tag ]

    # Load default values from _CONFIG_DEFAULTS_WINDOWS or _CONFIG_DEFAULTS_UNIX if they don't exist after loading config from file
    for tag in _CONFIG_TAGS_:
        if tag not in config_dict:
            if sys.platform.startswith('win'):
                config_dict[ tag ] = _CONFIG_DEFAULTS_WINDOWS[ tag ]
            elif sys.platform.startswith('linux') or sys.platform.startswith('darwin') or sys.platform.startswith('freebsd'):
                config_dict[ tag ] = _CONFIG_DEFAULTS_UNIX[ tag ]
            else:
                logger.error('Unknown platform: %s' % sys.platform)
                assert 0

    # Setup temp hidden RNA to expose the file paths
    for tag in _CONFIG_TAGS_:
        default = config_dict[ tag ]
        #func = eval( 'lambda self,con: config_dict.update( {"%s" : self.%s} )' %(tag,tag) )
        func = lambda self,con: config_dict.update( {tag : getattr(self,tag,default)} )
        if type(default) is bool:
            prop = BoolProperty( name=tag,
                                 description='updates bool setting',
                                 default=default,
                                 options={'SKIP_SAVE'},
                                 update=func)
        else:
            prop = StringProperty( name=tag,
                    description='updates path setting',
                    maxlen=128,
                    default=default,
                    options={'SKIP_SAVE'},
                    update=func)
        setattr( bpy.types.WindowManager, tag, prop )

    return config_dict

# Global CONFIG dictionary
CONFIG = load_config()

def get(name, default=None):
    global CONFIG
    if name in CONFIG:
        return CONFIG[name]
    return default

def update(**kwargs):
    for k,v in kwargs.items():
        if k not in _CONFIG_DEFAULTS_ALL:
            logger.warn("Trying to set CONFIG['%s'] = %s, but it is not a known config setting" % (k,v))
        CONFIG[k] = v
    save_config()

def save_config():
    global CONFIG
    #for key in CONFIG: print( '%s = %s' %(key, CONFIG[key]) )
    if os.path.isdir( CONFIG_PATH ):
        try:
            with open( CONFIG_FILEPATH, 'wb' ) as f:
                pickle.dump( CONFIG, f, -1 )
        except:
            logger.error('Can not write to %s' % CONFIG_FILEPATH)
    else:
        logger.error('Config directory %s does not exist' % CONFIG_PATH)

def update_from_addon_preference(context):
    addon_preferences = context.preferences.addons["io_ogre"].preferences

    for key in _CONFIG_TAGS_:
        addon_pref_value = getattr(addon_preferences,key,None)
        if addon_pref_value is not None:
            CONFIG[key] = addon_pref_value
