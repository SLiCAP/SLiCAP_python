# -*- coding: utf-8 -*-
"""
SLiCAP scripts for configuration management.

#. Main configuration is stored in ~/SLiCAP/SLiCAP.ini
#. Project configuration is stored in <project folder>/SLiCAP.ini

Configuration settings are imported as global (ini.<setting>)
"""

import configparser
import os
import platform
import re
import inspect
import requests
import shutil
from os.path import expanduser
from datetime import datetime
from sympy import Symbol
from SLiCAP.__init__ import __version__ as INSTALLVERSION


def check_for_updates(timeout=3):
    """
    Contacts GitHub for the latest SLiCAP release, stores the result in the
    main configuration file (~/SLiCAP/SLiCAP.ini), and returns it.

    Runs on demand only (GUI: Help > Check for updates); deliberately never
    on import, so importing SLiCAP is fast and works offline.

    :param timeout: Network timeout in seconds, defaults to 3.
    :type timeout: int, float

    :return: Latest release version, or 'Unknown' when GitHub could not be
             reached. Compare with ini.install_version.
    :rtype: str
    """
    global latest_version
    latest = _get_latest_version(timeout)
    if latest != "Unknown":
        latest_version = latest
        config_dict = _read_main_config()
        if 'version' in config_dict:
            config_dict['version']['latest_version'] = latest
            _write_main_config(config_dict)
    return latest

def _get_latest_version(timeout=3):
    """
    Gets the SLiCAP version from Github

    Returns
    -------
    String Version.
    """
    try:
        response = requests.get(
            "https://api.github.com/repos/SLiCAP/SLiCAP_python/releases/latest",
            timeout=timeout)
        version = response.json()["tag_name"]
    except BaseException:
        print("Could not determine the latest available version of SLiCAP on github.")
        version = "Unknown"
    return version

def _find_installed_software():
    """Best-effort, NON-INTERACTIVE detection of external-tool commands.

    External schematic tools (KiCad, gEDA/lepton, LTspice) are DEPRECATED —
    schematic capture is done in the SLiCAP GUI; only NGspice matters. Nothing
    is scanned or prompted: commands found on the PATH are picked up. On Windows
    NGspice is an unpacked zip (not on the PATH), so the standard download
    location (``C:\\Spice64\\bin``) is probed too. Anything not found is left an
    empty string, for the user to set in the GUI.
    """
    names = {'kicad': 'kicad-cli', 'geda': 'gnetlist',
             'lepton-eda': 'lepton-cli', 'ngspice': 'ngspice',
             'ltspice': 'ltspice',
             # LaTeX toolchain — stored like ngspice so rendering uses an
             # absolute path, not the GUI's launch-time PATH (Anton, 2026-07-25).
             'pdflatex': 'pdflatex', 'dvisvgm': 'dvisvgm'}
    commands = {key: (shutil.which(cmd) or '') for key, cmd in names.items()}
    if commands['lepton-eda']:
        commands['geda'] = shutil.which('lepton-netlist') or commands['geda']
    if not commands['ngspice']:
        commands['ngspice'] = _find_ngspice_fallback()
    return commands

def _ngspice_std_locations():
    """Standard NGspice executable locations per OS (used when it is not on the
    PATH): Windows unpacked zip, macOS Homebrew, Linux."""
    system = platform.system()
    if system == 'Windows':
        b = os.path.join('C:\\', 'Spice64', 'bin')
        return [os.path.join(b, 'ngspice_con.exe'),   # console build: batch runs
                os.path.join(b, 'ngspice.exe')]
    if system == 'Darwin':
        return ['/opt/homebrew/bin/ngspice',          # Apple Silicon Homebrew
                '/usr/local/bin/ngspice']             # Intel Homebrew
    return ['/usr/bin/ngspice', '/usr/local/bin/ngspice']

def _find_ngspice_fallback():
    """NGspice is not always on the PATH — a Windows unpacked zip, or a macOS
    GUI launched with a truncated PATH. Probe the standard install locations;
    '' when none exist (the user sets it in the GUI)."""
    for cand in _ngspice_std_locations():
        if os.path.isfile(cand):
            return cand
    return ''

def _generate_project_config():
    project_paths = {"html"          : 'html/',
                     "cir"           : 'cir/',
                     "lib"           : 'lib/',
                     "csv"           : 'csv/',
                     "txt"           : 'txt/',
                     "img"           : 'img/',
                     "sch"           : 'sch/',
                     "results"       : 'results/',
                     "sphinx"        : 'sphinx/',
                     "tex"           : 'tex/',
                     "tex_snippets"  : 'tex/SLiCAPdata/',
                     "rst_snippets"  : 'sphinx/SLiCAPdata/',
                     "html_snippets" : 'sphinx/SLiCAPdata/',
                     "myst_snippets" : 'sphinx/SLiCAPdata/',
                     "md_snippets"   : 'sphinx/SLiCAPdata/',
                     "project"       : os.path.abspath('.') + '/'
                    }
    project_config = configparser.ConfigParser()
    project_config['math']         = {"laplace"               : "s",
                                    "frequency"             : "f",
                                    "numer"                 : "MECPP",
                                    "denom"                 : "MECPP",
                                    "lambdify"              : "numpy",
                                    "stepfunction"          : True,
                                    "factor"                : True,
                                    "maxrecsubst"           : 15,
                                    "reducematrix"          : True,
                                    }
    project_config['balancing']    = {"update_srcnames"       : True,
                                    "pair_ext"              : "P,N",
                                    "remove_param_pair_ext" : True}
    project_config['plot']         = {"axisheight"            : 5,
                                    "axiswidth"             : 7,
                                    "defaultcolors"         : "r,b,g,c,m,y,k",
                                    "defaultmarkers"        : "",
                                    "legendloc"             : "best",
                                    "plotfontsize"          : 12,
                                    "plotfiletype"          : "svg",
                                    "linewidth"             : 2,
                                    "markersize"            : 7,
                                    "linetype"              : "-",
                                    "svgmargin"             : 1
                                    }                            
    project_config['gaincolors']   = {"asymptotic"            : "r",
                                    "gain"                  : "b",
                                    "loopgain"              : "k",
                                    "servo"                 : "m",
                                    "direct"                : "g",
                                    "ideal"                 : "c",
                                    "vi"                    : "c"
                                    }
    # GUI/schematic settings: sch_scale = scene units per millimeter.
    # Default 2 (resistor pin-to-pin = 50 units = 25 mm); book projects
    # targeting narrow LaTeX figure widths use 4-5 (Anton, 2026-07-15).
    project_config['gui']          = {'sch_scale'             : 2.0}
    project_config['display']      = {'Hz'                    : True,
                                    'Digits'                : 4,
                                    'notebook'              : False,
                                    'scalefactors'          : False,
                                    'engnotation'           : True}
    try: 
        _author = os.getlogin()
    except:
        _author = 'default'
        
    project_config['project']      = {'author'         : _author,
                                    'created'        : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'last_updated'   : '',
                                    'title'          : ''
                                    }
    project_config['projectpaths'] = project_paths
    project_config['html']         = {'current_index'  : 'index.html',
                                    'current_page'   : 'index.html',
                                    'pages'          : '',
                                    'prefix'         : ''
                                    }
    project_config['labels']        = {
                                    }
    return project_config
     
def _generate_main_config():
    install_path  = inspect.getfile(_find_installed_software).replace('\\', '/').split('/')
    install_path  = '/'.join(install_path[0:-2]) + '/'
    slicap_home   = expanduser("~").replace('\\', '/')
    home_path     = slicap_home + '/'
    install_paths = {"install"     : install_path,
                     "user"        : home_path,
                     "docs"        : os.path.join(install_path, 'SLiCAP/docs/html/'),
                     "mainlibs"    : os.path.join(install_path, 'SLiCAP/files/lib/'),
                     "kicadsyms"   : os.path.join(install_path, 'SLiCAP/files/kicad/SLiCAP.kicad_sym'),
                     "ngspicesyms" : os.path.join(install_path, 'SLiCAP/files/kicad/SPICE.kicad_sym'),
                     "gedasyms"    : os.path.join(install_path, 'SLiCAP/files/gSchem/'),
                     "leptonsyms"  : os.path.join(install_path, 'SLiCAP/files/lepton-eda/'),
                     "ltspicesyms" : os.path.join(install_path, 'SLiCAP/files/LTspice/'),
                     "latexfiles"  : os.path.join(install_path, 'SLiCAP/files/tex/'),
                     "sphinxfiles" : os.path.join(install_path, 'SLiCAP/files/sphinx/'),
                     }
    
    commands = _find_installed_software()
    # Optional fast determinant engine (see SLiCAP_GiNAC.md); empty = not
    # installed, det(method='MECPP') then falls back to the Python 'ME'.
    commands.setdefault('slicap_det', shutil.which('slicap_det') or '')
    main_config = configparser.ConfigParser()
    # The latest release is fetched on demand only (check_for_updates());
    # generating the configuration must work offline.
    main_config['version']      = {"install_version" : INSTALLVERSION,
                                     "latest_version" : "Unknown"}
    main_config['installpaths'] = install_paths
    main_config['commands']     = commands
    return main_config

def _generate_default_config():
    default_config = {'version':{'install_version'   : '',
                                 'latest_version'    : ''},
                      'installpaths':{"install"      : '',
                                       "user"        : '',
                                       "docs"        : '',
                                       "mainlibs"    : '',
                                       "kicadsyms"   : '',
                                       "ngspicesyms" : '',
                                       "gedasyms"    : '',
                                       "leptonsyms"  : '',
                                       "ltspicesyms" : '',
                                       "latexfiles"  : '',
                                       "sphinxfiles" : ''},
                      'commands':{'ltspice'          : '',
                                  'kicad'            : '',
                                  'geda'             : '',
                                  'lepton-eda'       : '',
                                  'ngspice'          : '',
                                  'slicap_det'       : '',
                                  'pdflatex'         : '',
                                  'dvisvgm'          : ''}
                      }
    return default_config

def _get_home_path():
    slicap_home  = expanduser("~").replace('\\', '/') + '/'
    return slicap_home

def main_config_path():
    """Location of the MAIN configuration file: ~/SLiCAP/SLiCAP.ini.

    The main configuration lives in its own folder so it can never collide
    with a project's SLiCAP.ini (decided 2026-07-15: with the old location
    ~/SLiCAP.ini, a project in the home directory silently destroyed the
    main configuration). A visible folder — not a hidden dot-folder — for
    Windows friendliness. A pre-existing main configuration at the legacy
    location is migrated automatically by _read_main_config().
    """
    return os.path.join(expanduser("~"), "SLiCAP", "SLiCAP.ini")

def _cwd_is_main_config_dir():
    """True when the current working directory is the main-configuration
    folder (~/SLiCAP): a project there would collide with the main
    SLiCAP.ini — the folder is reserved (found 2026-07-15 while closing
    the home-directory collision)."""
    return (os.path.abspath(os.getcwd())
            == os.path.abspath(os.path.dirname(main_config_path())))

def _read_project_config():
    try:
        if _cwd_is_main_config_dir():
            print("Warning: " + os.path.dirname(main_config_path()) +
                  " holds the main configuration and cannot be a SLiCAP "
                  "project directory. Using default project settings; "
                  "start SLiCAP from a project folder.")
            return _generate_project_config()
        if os.path.isfile("./SLiCAP.ini"):
            # strict=False tolerates duplicate option keys — an outside
            # run can leave a malformed [labels]/[html] section that would
            # otherwise raise DuplicateOptionError (Anton, 2026-07-16).
            config_dict = configparser.ConfigParser(strict=False)
            with open("SLiCAP.ini") as f:
                config_dict.read_file(f)
        else:
            print("Generating project configuration file: SLiCAP.ini.\n")
            config_dict = _generate_project_config()
            _write_project_config(config_dict)
    except Exception:
        # A corrupt project ini self-heals to defaults instead of returning
        # an empty config that then crashes downstream with missing keys
        # (inherited-fragility quick fix; the real fix is to stop storing
        # html/label RUN STATE in the project config — big TODO).
        print("Warning: project SLiCAP.ini could not be read; "
              "regenerating default project settings.")
        config_dict = _generate_project_config()
    return config_dict

def _migrate_legacy_main_config(path):
    """One-time migration of a MAIN configuration from the legacy location
    ~/SLiCAP.ini to ~/SLiCAP/SLiCAP.ini (preserves hand-edited command
    paths). A legacy file WITHOUT main-config sections is a project file
    of a project living in the home directory — left untouched."""
    legacy = _get_home_path() + "SLiCAP.ini"
    if not os.path.isfile(legacy):
        return False
    probe = configparser.ConfigParser(strict=False)
    try:
        with open(legacy) as f:
            probe.read_file(f)
    except Exception:
        return False
    if not (probe.has_section("commands")
            or probe.has_section("installpaths")):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    os.replace(legacy, path)
    print("Main configuration file moved to: " + path + "\n")
    return True

def _read_main_config():
    try:
        path = main_config_path()
        if not os.path.isfile(path):
            _migrate_legacy_main_config(path)
        if  os.path.isfile(path):
            config_dict = configparser.ConfigParser(strict=False)
            with open(path) as f:
                config_dict.read_file(f)
        else:
            print("Generating main configuration file: " + path + "\n")
            config_dict = _generate_main_config()
            _write_main_config(config_dict)
    except:
        config_dict = configparser.ConfigParser()
    return config_dict

def _write_project_config(config_dict):
    if _cwd_is_main_config_dir():
        # ~/SLiCAP/SLiCAP.ini is the MAIN configuration — never write a
        # project configuration over it (see _cwd_is_main_config_dir)
        return
    with open("SLiCAP.ini", "w") as f:
        config_dict.write(f)

def _write_main_config(config_dict):
    path = main_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        config_dict.write(f)
        
def _update_project_config():
    config_dict = _read_project_config()
    config_dict['project']['title']        = project_title
    config_dict['project']['author']       = author
    config_dict['project']['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config_dict["html"]["current_page"]    = html_index
    config_dict["html"]["current_index"]   = html_page
    config_dict["html"]["prefix"]          = html_prefix
    config_dict["html"]["pages"]           = (',').join(html_pages)
    config_dict["labels"]                  = html_labels
    _write_project_config(config_dict)
    
def _update_ini_files():
    generate        = False # Will be set to True is main config is corrupted
    main_config     = _read_main_config()
    main_keys       = main_config.keys()
    default_config  = _generate_default_config()
    default_keys    = default_config.keys()
    for default_key in default_keys:
        if default_key not in main_keys:
            generate = True
            break
        sub_keys      = default_config[default_key].keys()
        main_sub_keys = main_config[default_key].keys()
        for sub_key in sub_keys:
            if sub_key not in main_sub_keys:
                generate = True
                break
        if generate:
            break
    if generate:
        print("Updating main configuration file; this may take a while.")
        main_config = _generate_main_config()
        main_keys   = main_config.keys()   # refresh so del loop targets the new config

    # Keep the last known latest release; the network check runs only on
    # demand via check_for_updates(), so importing SLiCAP works offline.
    try:
        known_latest = main_config['version']['latest_version'] or "Unknown"
    except Exception:
        known_latest = "Unknown"
    main_config['version']      = {"install_version" : INSTALLVERSION,
                                   "latest_version" : known_latest}
    # Remove unused entries
    del_keys = []
    for key in main_keys:
        if key != "DEFAULT" and key not in default_keys:
            del_keys.append(key)
    for key in del_keys:
        del main_config[key]
    
    # Update main configuration file
    _write_main_config(main_config)

    # Update project configuration file
    project_config = _read_project_config()
    proj_keys = project_config.keys()
    default_config = _generate_project_config()
    default_keys = default_config.keys()
    for default_key in default_keys:
        if default_key not in proj_keys:
            project_config[default_key] = default_config[default_key]
        sub_keys     = default_config[default_key].keys()
        prj_sub_keys = project_config[default_key].keys()
        for sub_key in sub_keys:
            if sub_key not in prj_sub_keys:
                project_config[default_key][sub_key] = default_config[default_key][sub_key]

    # Remove unused entries
    del_keys = []
    for key in proj_keys:
        if key != "DEFAULT" and key not in default_keys:
            del_keys.append(key)
    for key in del_keys:
        del project_config[key]
    _write_project_config(project_config)
    
    return main_config, project_config    

def dump(section="all"):
    """
    Prints the global SLiCAP settings.
    
    :param sections: "all", or name of section to be printed:
                     - VERSION
                     - INSTALL
                     - COMMANDS
                     - PROJECT
                     - PATHS
                     - HTML
                     - DSIPLAY
                     - MATH
                     - PLOT
                     - BALANCING
                     
                     
    :type section: str, list
    
    :return None:
    :rtype NoneType:
        
    :example:
        
    >>> import SLiCAP as sl
    >>> sl.ini.dump()
    """
    section = section.upper()
    if section == 'ALL' or section == "VERSION":
        print("\nVERSION")
        print("-------")
        print('ini.install_version        =', install_version)
        print('ini.latest_version         =', latest_version)
    if section == 'ALL' or section == "INSTALL":
        print("\nINSTALL")
        print("-------")
        print('ini.install_path           =', install_path)
        print('ini.home_path              =', home_path)
        print('ini.main_lib_path          =', main_lib_path)
        print('ini.doc_path               =', doc_path)
        print('ini.kicad_syms             =', kicad_syms)
        print('ini.ngspice_syms           =', ngspice_syms)
        print('ini.ltspice_syms           =', ltspice_syms)
        print('ini.gnetlist_syms          =', gnetlist_syms)
        print('ini.lepton_eda_syms        =', lepton_eda_syms)
        print('ini.latex_files            =', latex_files)
        print('ini.sphinx_files           =', sphinx_files)
    if section == 'ALL' or section == "COMMANDS":    
        print("\nCOMMANDS")
        print("--------")
        print('ini.kicad                  =', kicad)
        print('ini.ltspice                =', ltspice)
        print('ini.gnetlist               =', gnetlist)
        print('ini.lepton_eda             =', lepton_eda)
        print('ini.ngspice                =', ngspice)
        print('ini.slicap_det             =', slicap_det)
    if section == 'ALL' or section == "PROJECT":
        print("\nPROJECT")
        print("-------")
        print('ini.project_title          =', project_title)
        print('ini.author                 =', author)
        print('ini.created                =', created)
        print('ini.last_updated           =', last_updated)
    if section == 'ALL' or section == "PATHS":    
        print("\nPATHS")
        print("-----")
        print('ini.project_path           =', project_path)
        print('ini.html_path              =', html_path)
        print('ini.cir_path               =', cir_path)
        print('ini.img_path               =', img_path)
        print('ini.csv_path               =', csv_path)
        print('ini.results_path           =', results_path)
        print('ini.txt_path               =', txt_path)
        print('ini.tex_path               =', tex_path)
        print('ini.user_lib_path          =', user_lib_path)
        print('ini.sphinx_path            =', sphinx_path)
        print('ini.tex_snippets           =', tex_snippets)
        print('ini.html_snippets          =', html_snippets)
        print('ini.rst_snippets           =', rst_snippets)
        print('ini.myst_snippets          =', myst_snippets)
        print('ini.md_snippets            =', md_snippets)
    if section == 'ALL' or section == "HTML":    
        print("\nHTML")
        print("----")
        print('ini.html_prefix            =', html_prefix)
        print('ini.html_index             =', html_index )
        print('ini.html_page              =', html_page)
        print('ini.html_pages')
        for page in html_pages:
            print("\t", page)
        
        print('ini.html_labels')
        for label in html_labels.keys():
            print("label :", label)
            print("\ttype        :", html_labels[label][0])
            print("\thref        :", html_labels[label][1])
            print("\tdescription :", html_labels[label][2])
    if section == 'ALL' or section == "DISPLAY":       
        print("\nDISPLAY")
        print("-------")
        print('ini.hz                     =', hz)
        print('ini.disp                   =', disp)
        print('ini.scalefactors           =', scalefactors)
        print('ini.eng_notation           =', eng_notation)
    if section == 'ALL' or section == "MATH":
        print("\nMATH")
        print("----")
        print('ini.laplace                =', laplace)
        print('ini.frequency              =', frequency)
        print('ini.numer                  =', numer)
        print('ini.denom                  =', denom)
        print('ini.lambdify               =', lambdify)
        print('ini.step_function          =', step_function)
        print('ini.factor                 =', factor)
        print('ini.max_rec_subst          =', max_rec_subst)
        print('ini.reduce_matrix          =', reduce_matrix)
        #print('ini.reduce_circuit         =', reduce_circuit)
    if section == 'ALL' or section == "PLOT":        
        print("\nPLOT")
        print("----")
        print('ini.gain_colors_gain       =', gain_colors_gain)
        print('ini.gain_colors_loopgain   =', gain_colors_loopgain)
        print('ini.gain_colors_asymptotic =', gain_colors_asymptotic)
        print('ini.gain_colors_servo      =', gain_colors_servo)
        print('ini.gain_colors_direct     =', gain_colors_direct)
        print('ini.gain_colors_vi         =', gain_colors_vi)   
        print('ini.gain_colors_ideal      =', gain_colors_ideal)   
        print('ini.axis_height            =', axis_height)
        print('ini.axis_width             =', axis_width)
        print('ini.line_width             =', line_width)
        print('ini.line_type              =', line_type)
        print('ini.plot_fontsize          =', plot_fontsize)
        print('ini.marker_size            =', marker_size)
        print('ini.legend_loc             =', legend_loc)
        print('ini.default_colors         =', default_colors)
        print('ini.default_markers        =', default_markers)
        print('ini.plot_file_type         =', plot_file_type)
        print('ini.svg_margin             =', svg_margin)
    if section == 'ALL' or section == "BALANCING":    
        print("\nBALANCING")
        print("---------")
        print('ini.pair_ext               =', pair_ext)
        print('ini.update_srcnames        =', update_srcnames)
        print('ini.remove_param_pair_ext  =', remove_param_pair_ext)
    
# Define global variables from ini files

main_config, project_config = _update_ini_files()

install_version       = main_config['version']['install_version']
latest_version        = main_config['version']['latest_version']

install_path          = main_config['installpaths']['install']
home_path             = main_config['installpaths']['user']
main_lib_path         = main_config['installpaths']['mainlibs']
doc_path              = main_config['installpaths']['docs']
kicad_syms            = main_config['installpaths']['kicadsyms']
ngspice_syms          = main_config['installpaths']['ngspicesyms']
ltspice_syms          = main_config['installpaths']['ltspicesyms']
gnetlist_syms         = main_config['installpaths']['gedasyms']
lepton_eda_syms       = main_config['installpaths']['leptonsyms']
latex_files           = main_config['installpaths']['latexfiles']
sphinx_files          = main_config['installpaths']['sphinxfiles']

kicad                 = main_config['commands']['kicad']
ltspice               = main_config['commands']['ltspice']
gnetlist              = main_config['commands']['geda']
lepton_eda            = main_config['commands']['lepton-eda']
ngspice               = main_config['commands']['ngspice']
slicap_det            = main_config['commands'].get('slicap_det', '')
# LaTeX toolchain (absolute paths, like ngspice) — the migration in
# _update_ini_files() adds these keys to older configs; .get keeps a transient
# or corrupted config from raising here.
pdflatex              = main_config['commands'].get('pdflatex', '')
dvisvgm               = main_config['commands'].get('dvisvgm', '')

project_title         = project_config['project']['title']
author                = project_config['project']['author']
created               = project_config['project']['created']
last_updated          = project_config['project']['last_updated']

project_path          = project_config['projectpaths']['project']
html_path             = project_config['projectpaths']['html']
cir_path              = project_config['projectpaths']['cir']
img_path              = project_config['projectpaths']['img']
csv_path              = project_config['projectpaths']['csv']
txt_path              = project_config['projectpaths']['txt']
tex_path              = project_config['projectpaths']['tex']
user_lib_path         = project_config['projectpaths']['lib']
schematic_path        = project_config['projectpaths'].get('sch', 'sch/')
# design-data manifest + result artifacts (SLNG.md "Design data panel");
# .get(): projects created before this key existed keep working
results_path          = project_config['projectpaths'].get('results', 'results/')
sphinx_path           = project_config['projectpaths']['sphinx']
tex_snippets          = project_config['projectpaths']['tex_snippets']
html_snippets         = project_config['projectpaths']['html_snippets']
rst_snippets          = project_config['projectpaths']['rst_snippets']
myst_snippets         = project_config['projectpaths']['myst_snippets']
md_snippets           = project_config['projectpaths']['md_snippets']

html_prefix           = project_config['html']['prefix']
html_index            = project_config['html']['current_index']
html_page             = project_config['html']['current_page']
html_pages            = project_config['html']['pages'].split(',')
html_pages            = [page.strip() for page in html_pages]

html_labels           = project_config['labels']
new_labels = {}
for key in html_labels.keys():
    label = html_labels[key]
    label = html_labels[key][1:-1].split(',')
    label = [item.strip()[1:-1] for item in label]
    new_labels[key] = label
html_labels = new_labels
    
hz                    = eval(project_config['display']['Hz'])
disp                  = eval(project_config['display']['digits'])
scalefactors          = eval(project_config['display']['scalefactors'])
eng_notation          = eval(project_config['display']['engnotation'])

laplace               = Symbol(project_config['math']['laplace'])
frequency             = Symbol(project_config['math']['frequency'])
numer                 = project_config['math']['numer']
denom                 = project_config['math']['denom']
sch_scale             = float(project_config['gui']['sch_scale'])
lambdify              = project_config['math']['lambdify']
step_function         = eval(project_config['math']['stepfunction'])
factor                = eval(project_config['math']['factor'])
max_rec_subst         = eval(project_config['math']['maxrecsubst'])
reduce_matrix         = eval(project_config['math']['reducematrix'])

gain_colors_gain      = project_config['gaincolors']['gain']
gain_colors_asymptotic= project_config['gaincolors']['asymptotic']
gain_colors_loopgain  = project_config['gaincolors']['loopgain']
gain_colors_direct    = project_config['gaincolors']['direct']
gain_colors_servo     = project_config['gaincolors']['servo']
gain_colors_ideal     = project_config['gaincolors']['ideal']
gain_colors_vi        = project_config['gaincolors']['vi']


axis_height           = eval(project_config['plot']['axisheight'])
axis_width            = eval(project_config['plot']['axiswidth'])
line_width            = eval(project_config['plot']['linewidth'])
line_type             = project_config['plot']['linetype']
plot_fontsize         = eval(project_config['plot']['plotfontsize'])
marker_size           = eval(project_config['plot']['markersize'])
legend_loc            = project_config['plot']['legendloc']
default_colors        = project_config['plot']['defaultcolors'].split(',')
default_colors        = [col.strip() for col in default_colors]
default_markers       = project_config['plot']['defaultmarkers'].split(',')
default_markers       = [mark.strip() for mark in default_markers]
plot_file_type        = project_config['plot']['plotfiletype']
svg_margin            = eval(project_config['plot']['svgmargin'])

pair_ext              = project_config['balancing']['pair_ext'].split(',') 
pair_ext              = [ext.strip() for ext in pair_ext]
update_srcnames       = eval(project_config['balancing']['update_srcnames'])
remove_param_pair_ext = eval(project_config['balancing']['remove_param_pair_ext'])

notebook              = False

SLiCAPPARAMS          = {} # Entries will be generated during circuit check
