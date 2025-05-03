# -*- coding: utf-8 -*-
"""
SLiCAP scripts for configuration management.

#. Main configuration is stored in ~/SLiCAP/SLiCAP.ini
#. Project configuration is stored in <project folder>/SLiCAP.ini

Configuration settings are imported as global (ini.<setting>)
"""

import configparser
import os
import sys
import platform
import re
import inspect
import requests
from os.path import expanduser
from datetime import datetime
from sympy import Symbol
from time import time
from SLiCAP.__init__ import __version__ as INSTALLVERSION

if platform.system() == 'Windows':
    import win32api
    import windows_tools.installed_software as wi

TIMEOUT = 120
#INSTALLVERSION = "3.3.2"

def _check_version():
    """
    Checks the version with the latest SLiCAP version from Git

    Returns
    -------
    None.
    """
    latest = _get_latest_version()
    if latest == "Unknown":
        print("You are running SLiCAP version %s. Please check github for updates."%(INSTALLVERSION))
    elif INSTALLVERSION != latest:
        print("A new version of SLiCAP is available, please get it from 'https://github.com/SLiCAP/SLiCAP_python.git'.")
    else:
        print("SLiCAP Version matches with the latest release of SLiCAP on github.")
    return str(latest)
    
def _get_latest_version():
    """
    Gets the SLiCAP version from Github

    Returns
    -------
    String Version.
    """
    try:
        response = requests.get("https://api.github.com/repos/SLiCAP/SLiCAP_python/releases/latest")
        version = response.json()["tag_name"]
    except BaseException:
        print("Could not determine the latest available version of SLiCAP on github.")
        version = "Unknown"
    return version

def _find_installed_windows_software():
    """
    Searches for installed packages from the package list

    Returns
    -------
    Dictionary with key-value pairs: key = package name, value = command
    """
    package_list = ['LTspice', 'KiCad', 'gEDA', 'NGspice']
    commands = {}
    search_list = []
    # get list with installed apps
    software_list = wi.get_installed_software()
    # make a list of apps that we want to search for
    for dct in software_list:
        name = dct["name"]
        if len(name) > 1:
            name = name.split()[0]
            if name in package_list:
                search_list.append(name)
    y_n = input("\nDo you have NGspice installed? [y/n] >>> ").lower()[0]
    while y_n != 'y' and y_n != 'n':
        y_n = input("\nPlease enter 'y' for 'yes' or 'n' for 'no' >>> ").lower()[0]
    if y_n == 'y':
        search_list.append('NGspice')
    else:
        commands['ngspice'] = ''
        """
    for package in search_list:
        y_n = input("\nDo you want SLiCAP to search for the {} command? [y/n] >>> ".format(package)).lower()[0]
        while y_n != 'y' and y_n != 'n':
            y_n = input("\nPlease enter 'y' for 'yes' or 'n' for 'no' >>> ").lower()[0]
        if y_n == 'y':
            pass
        else:
            commands[package.lower()] = ''
        """
    # search for the command to start each app
    if len(search_list) > 0:
        found_all = False
        t_start = time()
        time_out = False
        print("\nSearching installed software, this will time-out after {} seconds!\n".format(str(TIMEOUT)))
        for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
            for root, dirs, files in os.walk(drive):
                t_now = time()
                if t_now - t_start >TIMEOUT:
                    time_out = True
                for name in dirs:
                    for package in search_list: # Only search for installed software
                        p_name = package.lower()
                        if p_name not in commands.keys():
                            #print("Searching for installation of:", package)
                            found = False
                            if package == 'LTspice':
                                if re.match('LT(S|s)pice*', name, flags=0):
                                    if os.path.exists(os.path.join(root,name,'XVIIx64.exe')):
                                        print("LTSpice command set as:", os.path.join(root,name,'XVIIx64.exe'))
                                        commands[p_name] = os.path.join(root,name,'XVIIx64.exe')
                                        found = True
                                    elif  os.path.exists(os.path.join(root,name,'LTspice.exe')):
                                        print("LTSpice command set as:", os.path.join(root,name,'LTspice.exe'))
                                        commands[p_name] = os.path.join(root,name,'LTspice.exe')
                                        found = True
                                    elif  os.path.exists(os.path.join(root,name,'ltspice.exe')):
                                        print("LTSpice command set as:", os.path.join(root,name,'ltspice.exe'))
                                        commands[p_name] = os.path.join(root,name,'ltspice.exe')
                                        found = True
                            elif package == 'KiCad':
                                try:
                                    if re.match('KiCad', name, flags=0):
                                        version=os.listdir(os.path.join(root, name))[0]
                                        file_name = os.path.join(root, name, version, 'bin','kicad-cli.exe')
                                        if os.path.exists(file_name):
                                            print("KiCad command set as:", os.path.join(root,name,'kicad-cli.exe'))
                                            commands[p_name] = file_name
                                            found = True
                                except:
                                    print("Could not find the KiCad command 'kicad-cli.exe'. " +
                                          "Please add this command manually to the ~/SLiCAP.ini file!")
                            elif package == 'gEDA':
                                if re.match('gEDA', name, flags=0):
                                    file_name = os.path.join(root, name, 'gEDA', 'bin' ,'gnetlist.exe')
                                    if os.path.exists(file_name):
                                        print("gnetlist command set as:", os.path.join(root,name,'gnetlist.exe'))
                                        commands[p_name] = file_name
                                        found = True
                            elif package == 'NGspice':
                                if re.match('Spice64', name, flags=0):
                                    file_name = os.path.join(root, name, 'bin' ,'ngspice.exe')
                                    if os.path.exists(file_name):
                                        print("NGspice command set as:", os.path.join(root,name,'ngspice.exe'))
                                        commands[p_name] = file_name
                                        found = True
                            if found:
                                # Stop walking is all packages are found
                                found_all = True
                                for item in search_list:
                                    if item.lower() not in list(commands.keys()):
                                        found_all = False
                                        break
                                if found_all == True or time_out:
                                    break
                if found_all or time_out:
                    break
            if found_all or time_out:
                break
    found_list = list(commands.keys())    
    if found_all:
        print("SLiCAP found all installed apps!")
    elif time_out:
        print("\nSearching time for apps aborted due to time-out!\n")
        for app in search_list:
            if app.lower() not in found_list:
                print("-", app, ": installed but not found")
        print("\nIf you want SLiCAP to make calls to these apps, please edit " + 
              "the main configuration file: '~/SLiCAP.ini'. More information " +
              "is available in the SLiCAP HTML help.")
    # Complete the commands dictionary
    if len(found_list) != len(package_list):
        for package in package_list:
            p_name = package.lower()
            if p_name not in found_list:
                commands[p_name] = ''
            if package not in search_list:
                print("-", package, ": not installed")      
    if len(search_list) != len(package_list):
        print("After installation of missing apps, delete the '~/SLiCAP.ini' " +
              "file. It will be recreated with the next SLiCAP import.")
    commands['lepton-eda'] = ''
    return commands

def _find_LTspice_wine():
    """
    Searches for LTspice under Linux or MacOS

    Returns
    -------
    LTspice command
    """
    cmd = ''
    try:
        home = expanduser("~")
        drives = [os.path.join(home, '.wine', 'drive_c')]
        for drive in drives:
            drive = os.path.join(drive, 'Program Files')
            for root, dirs, files in os.walk(drive, topdown=True):
                for name in dirs:
                    if re.match('LT(S|s)pice*', name, flags=0):
                        if os.path.exists(os.path.join(root,name,'XVIIx64.exe')):
                            cmd = os.path.join(root,name,'XVIIx64.exe')
                        elif  os.path.exists(os.path.join(root,name,'LTspice.exe')):
                            cmd = os.path.join(root,name,'LTspice.exe')
                        elif  os.path.exists(os.path.join(root,name,'ltspice.exe')):
                            cmd = os.path.join(root,name,'ltspice.exe')
                        return cmd
    except:
        pass
    return cmd

def _find_installed_software():
    system = platform.system()
    commands = {}
    commands['ltspice']      =  _find_LTspice_wine()
    commands['kicad']        = 'kicad-cli'
    commands['geda']         = 'gnetlist'
    commands['lepton-eda']   = 'lepton-cli'
    commands['ngspice']      = 'ngspice'
    if system               != "Linux":
        commands['kicad']    = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    for key in commands.keys():
        if key != "ltspice":
            cmd = "which " + commands[key]
            found = os.system(cmd)
            if found == 256:
                commands[key] = ""
    if system != 'Windows' and commands['lepton-eda'] != '':
        commands['geda'] = 'lepton-netlist'
    # print not installed packages
    not_installed = []
    for key in commands.keys():
        if commands[key] == '':
            not_installed.append(key)
    if len(not_installed) > 0:
        print("The following apps have not been installed:")
        for app in not_installed:
            print("-", app)
        print("After installation of missing apps, delete the '~/SLiCAP.ini' " +
              "file. It will be recreated with the next SLiCAP import.")
    return commands

def _generate_project_config():
    project_paths = {"html"          : 'html/',
                     "cir"           : 'cir/',
                     "lib"           : 'lib/',
                     "csv"           : 'csv/',
                     "txt"           : 'txt/',
                     "img"           : 'img/',
                     "mathml"        : 'mathml/',
                     "sphinx"        : 'sphinx/',
                     "tex"           : 'tex/',
                     "tex_snippets"  : 'tex/SLiCAPdata/',
                     "rst_snippets"  : 'sphinx/SLiCAPdata/',
                     "html_snippets" : 'sphinx/SLiCAPdata/',
                     "myst_snippets" : 'sphinx/SLiCAPdata/',
                     "md_snippets"   : 'sphinx/SLiCAPdata/',
                     "project"       : os.path.abspath('.') + '/'
                    }
    SLiCAPconfig = configparser.ConfigParser()
    SLiCAPconfig['math']         = {"laplace"        : "s",
                                    "frequency"      : "f",
                                    "numer"          : "ME",
                                    "denom"          : "ME",
                                    "lambdify"       : "numpy",
                                    "stepfunction"   : True,
                                    "factor"         : True,
                                    "maxrecsubst"    : 15,
                                    "reducematrix"   : True,
                                    "reducecircuit"  : True
                                    }
    SLiCAPconfig['plot']         = {"axisheight"     : 5,
                                    "axiswidth"      : 7,
                                    "defaultcolors"  : "r,b,g,c,m,y,k",
                                    "defaultmarkers" : "",
                                    "legendloc"      : "best",
                                    "plotfontsize"   : 12,
                                    "plotfiletype"   : "svg",
                                    "linewidth"      : 2,
                                    "markersize"     : 7,
                                    "linetype"       : "-",
                                    "svgmargin"      : 1
                                    }                            
    SLiCAPconfig['gaincolors']   = {"asymptotic"     : "r",
                                    "gain"           : "b",
                                    "loopgain"       : "k",
                                    "servo"          : "m",
                                    "direct"         : "g",
                                    "vi"             : "c"
                                    }
    SLiCAPconfig['display']      = {'Hz'             : True,
                                    'Digits'         : 4,
                                    'notebook'       : False,
                                    'scalefactors'   : False,
                                    'engnotation'    : True}
    try: 
        _author = os.getlogin()
    except:
        _author = 'default'
        
    SLiCAPconfig['project']      = {'author'         : _author,
                                    'created'        : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'last_updated'   : '',
                                    'title'          : ''
                                    }
    SLiCAPconfig['projectpaths'] = project_paths
    SLiCAPconfig['html']         = {'current_index'  : 'index.html',
                                    'current_page'   : 'index.html',
                                    'pages'          : '',
                                    'prefix'         : ''
                                    }
    SLiCAPconfig['labels']        = {
                                    }
    return SLiCAPconfig
     
def _generate_main_config():
    install_path  = inspect.getfile(_find_installed_software).replace('\\', '/').split('/')
    install_path  = '/'.join(install_path[0:-2]) + '/'
    slicap_home   = expanduser("~").replace('\\', '/')
    home_path     = slicap_home + '/'
    install_paths = {"install"     : install_path,
                     "user"        : home_path,
                     "docs"        : os.path.join(install_path, 'SLiCAP/docs/html/'),
                     "libs"        : os.path.join(install_path, 'SLiCAP/files/lib/'),
                     "kicadsyms"   : os.path.join(install_path, 'SLiCAP/files/kicad/SLiCAP.kicad_sym'),
                     "gedasyms"    : os.path.join(install_path, 'SLiCAP/files/gSchem/'),
                     "leptonsyms"  : os.path.join(install_path, 'SLiCAP/files/lepton-eda/'),
                     "ltspicesyms" : os.path.join(install_path, 'SLiCAP/files/LTspice/'),
                     "latexfiles"  : os.path.join(install_path, 'SLiCAP/files/tex/'),
                     "sphinxfiles" : os.path.join(install_path, 'SLiCAP/files/sphinx/'),
                     }
    
    if platform.system() == 'Windows':
        commands = _find_installed_windows_software()
    else:
        commands =  _find_installed_software()
    SLiCAPconfig = configparser.ConfigParser()
    SLiCAPconfig['version']      = {"install_version" : INSTALLVERSION,
                                     "latest_version" : _check_version()}
    SLiCAPconfig['installpaths'] = install_paths
    SLiCAPconfig['commands']     = commands
    return SLiCAPconfig

def _generate_default_config():
    default_config = {'version':{'install_version'   : '',
                                 'latest_version'    : ''},
                      'installpaths':{"install"      : '',
                                       "user"        : '',
                                       "docs"        : '',
                                       "libs"        : '',
                                       "kicadsyms"   : '',
                                       "gedasyms"    : '',
                                       "leptonsyms"  : '',
                                       "ltspicesyms" : '',
                                       "latexfiles"  : '',
                                       "sphinxfiles" : ''},
                      'commands':{'ltspice'          : '',
                                  'kicad'            : '',
                                  'geda'             : '',
                                  'lepton-eda'       : '',
                                  'ngspice'          : ''}
                      }
    return default_config

def _get_home_path():
    slicap_home  = expanduser("~").replace('\\', '/') + '/'
    return slicap_home
    
def _read_project_config():
    try:
        if  os.path.isfile("./SLiCAP.ini"):
            config_dict = configparser.ConfigParser()
            with open("SLiCAP.ini") as f:
                config_dict.read_file(f)
        else:
            print("Generating project configuration file: SLiCAP.ini.\n")
            config_dict = _generate_project_config()
            _write_project_config(config_dict)
    except:
        config_dict = configparser.ConfigParser()
    return config_dict

def _read_main_config():
    try:
        path = _get_home_path() + "SLiCAP.ini"
        if  os.path.isfile(path):
            config_dict = configparser.ConfigParser()
            with open(path) as f:
                config_dict.read_file(f)
        else:
            print("Generating main configuration file: ~/SLiCAP.ini.\n")
            config_dict = _generate_main_config()
            _write_main_config(config_dict)
    except:
        config_dict = configparser.ConfigParser()
    return config_dict

def _write_project_config(config_dict):
    with open("SLiCAP.ini", "w") as f:
        config_dict.write(f)

def _write_main_config(config_dict):
    with open(_get_home_path() + "SLiCAP.ini", "w") as f:
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
        else:
            sub_keys      = default_config[default_key].keys()
            main_sub_keys = main_config[default_key].keys()
            for sub_key in sub_keys:
                if sub_key not in main_sub_keys:
                    generate is True
    if generate:
        print("Updating main configuration file; this may take a while.")
        main_config = _generate_main_config()
        _write_main_config(main_config)
    
    # Update the project data from the project configuration file
    project_config = _read_project_config()
    proj_keys = project_config.keys()
    default_config = _generate_project_config()
    main_keys = default_config.keys()
    for main_key in main_keys:
        if main_key not in proj_keys:
            project_config[main_key] = default_config[main_key]
        sub_keys     = default_config[main_key].keys()
        prj_sub_keys = project_config[main_key].keys()
        for sub_key in sub_keys:
            if sub_key not in prj_sub_keys:
                project_config[main_key][sub_key] = default_config[main_key][sub_key]
    _write_project_config(project_config)
    
    return main_config, project_config
         
def dump():
    """
    Prints the global SLiCAP settings.
    
    :return None:
    :rtype NoneType:
        
    :example:
        
    >>> import SLiCAP as sl
    >>> sl.ini.dump()
    """
    main_config     = _read_main_config()
    # Global variables from main configuration file
    print('ini.install_version =', main_config['version']['install_version'])
    print('ini.latest_version  =', main_config['version']['latest_version'])
    print('ini.install_path    =', main_config['installpaths']['install'])
    print('ini.home_path       =', main_config['installpaths']['user'])
    print('ini.main_lib_path   =', main_config['installpaths']['libs'])
    print('ini.doc_path        =', main_config['installpaths']['docs'])
    print('ini.ltspice         =', main_config['commands']['ltspice'])
    print('ini.gnetlist        =', main_config['commands']['geda'])
    print('ini.kicad           =', main_config['commands']['kicad'])
    print('ini.ngspice         =', main_config['commands']['ngspice'])
    print('ini.lepton_eda      =', main_config['commands']['lepton-eda'])
    print('ini.ltspice_syms    =', main_config['installpaths']['ltspicesyms'])
    print('ini.gnetlist_syms   =', main_config['installpaths']['gedasyms'])
    print('ini.kicad_syms      =', main_config['installpaths']['kicadsyms'])
    print('ini.lepton_eda_syms =', main_config['installpaths']['leptonsyms'])
    print('ini.latex_files     =', main_config['installpaths']['latexfiles'])
    print('ini.sphinx_files    =', main_config['installpaths']['sphinxfiles'])
    
    project_config = _read_project_config()
    # Global variables from main configuration file
    print('ini.html_path       =', project_config['projectpaths']['html'])
    print('ini.cir_path        =', project_config['projectpaths']['cir'])
    print('ini.img_path        =', project_config['projectpaths']['img'])
    print('ini.csv_path        =', project_config['projectpaths']['csv'])
    print('ini.txt_path        =', project_config['projectpaths']['txt'])
    print('ini.tex_path        =', project_config['projectpaths']['tex'])
    print('ini.user_lib_path   =', project_config['projectpaths']['lib'])
    print('ini.project_path    =', project_config['projectpaths']['project'])
    print('ini.mathml_path     =', project_config['projectpaths']['mathml'])
    print('ini.sphinx_path     =', project_config['projectpaths']['sphinx'])
    print('ini.tex_snippets    =', project_config['projectpaths']['tex_snippets'])
    print('ini.html_snippets   =', project_config['projectpaths']['html_snippets'])
    print('ini.rst_snippets    =', project_config['projectpaths']['rst_snippets'])
    print('ini.myst_snippets   =', project_config['projectpaths']['myst_snippets'])
    print('ini.md_snippets     =', project_config['projectpaths']['md_snippets'])
    print('ini.html_prefix     =', project_config['html']['prefix'])
    print('ini.html_index      =', project_config['html']['current_index'])
    print('ini.html_page       =', project_config['html']['current_page'])
    print('ini.html_pages      =', project_config['html']['pages'].split(','))
    print('ini.html_labels     =', project_config['labels'])
    print('ini.disp            =', eval(project_config['display']['digits']))
    print('ini.hz              =', eval(project_config['display']['Hz']))
    print('ini.notebook        =', eval(project_config['display']['notebook']))
    print('ini.scalefactors    =', eval(project_config['display']['scalefactors']))
    print('ini.eng_notation    =', eval(project_config['display']['engnotation']))
    print('ini.last_updated    =', project_config['project']['last_updated'])
    print('ini.project_title   =', project_config['project']['title'])
    print('ini.created         =', project_config['project']['created'])
    print('ini.author          =', project_config['project']['author'])
    print('ini.laplace         =', Symbol(project_config['math']['laplace']))
    print('ini.frequency       =', Symbol(project_config['math']['frequency']))
    print('ini.numer           =', project_config['math']['numer'])
    print('ini.denom           =', project_config['math']['denom'])
    print('ini.lambdify        =', project_config['math']['lambdify'])
    print('ini.step_function   =', eval(project_config['math']['stepfunction']))
    print('ini.factor          =', eval(project_config['math']['factor']))
    print('ini.max_rec_subst   =', eval(project_config['math']['maxrecsubst']))
    print('ini.reduce_matrix   =', eval(project_config['math']['reducematrix']))
    print('ini.reduce_circuit  =', eval(project_config['math']['reducecircuit']))
    print('ini.gain_colors     =', dict(project_config['gaincolors']))
    print('ini.plot_fontsize   =', eval(project_config['plot']['plotfontsize']))
    print('ini.axis_height     =', eval(project_config['plot']['axisheight']))
    print('ini.axis_width      =', eval(project_config['plot']['axiswidth']))
    print('ini.line_width      =', eval(project_config['plot']['linewidth']))
    print('ini.marker_size     =', eval(project_config['plot']['markersize']))
    print('ini.line_type       =', project_config['plot']['linetype'])
    print('ini.legend_loc      =', project_config['plot']['legendloc'])
    print('ini.default_colors  =', project_config['plot']['defaultcolors'].split(','))
    print('ini.default_markers =', project_config['plot']['defaultmarkers'].split(','))
    print('ini.plot_fontsize   =', project_config['plot']['plotfontsize'])
    print('ini.plot_file_type  =', project_config['plot']['plotfiletype'])
    print('ini.svg_margin      =', eval(project_config['plot']['svgmargin']))
    

# Define global variables from ini files

main_config, project_config = _update_ini_files()

install_version = main_config['version']['install_version']
latest_version  = main_config['version']['latest_version']
install_path    = main_config['installpaths']['install']
home_path       = main_config['installpaths']['user']
main_lib_path   = main_config['installpaths']['libs']
doc_path        = main_config['installpaths']['docs']
ltspice_syms    = main_config['installpaths']['ltspicesyms']
netlist_syms    = main_config['installpaths']['gedasyms']
kicad_syms      = main_config['installpaths']['kicadsyms']
lepton_eda_syms = main_config['installpaths']['leptonsyms']
latex_files     = main_config['installpaths']['latexfiles']
sphinx_files    = main_config['installpaths']['sphinxfiles']
ltspice         = main_config['commands']['ltspice']
gnetlist        = main_config['commands']['geda']
kicad           = main_config['commands']['kicad']
ngspice         = main_config['commands']['ngspice']
lepton_eda      = main_config['commands']['lepton-eda']
project_path    = project_config['projectpaths']['project']
html_path       = project_config['projectpaths']['html']
cir_path        = project_config['projectpaths']['cir']
img_path        = project_config['projectpaths']['img']
csv_path        = project_config['projectpaths']['csv']
txt_path        = project_config['projectpaths']['txt']
tex_path        = project_config['projectpaths']['tex']
user_lib_path   = project_config['projectpaths']['lib']
mathml_path     = project_config['projectpaths']['mathml']
sphinx_path     = project_config['projectpaths']['sphinx']
tex_snippets    = project_config['projectpaths']['tex_snippets']
html_snippets   = project_config['projectpaths']['html_snippets']
rst_snippets    = project_config['projectpaths']['rst_snippets']
myst_snippets   = project_config['projectpaths']['myst_snippets']
md_snippets     = project_config['projectpaths']['md_snippets']
html_prefix     = project_config['html']['prefix']
html_index      = project_config['html']['current_index']
html_page       = project_config['html']['current_page']
html_pages      = project_config['html']['pages'].split(',')
html_labels     = project_config['labels']
disp            = eval(project_config['display']['digits'])
scalefactors    = eval(project_config['display']['scalefactors'])
eng_notation    = eval(project_config['display']['engnotation'])
last_updated    = project_config['project']['last_updated']
project_title   = project_config['project']['title']
created         = project_config['project']['created']
author          = project_config['project']['author']
laplace         = Symbol(project_config['math']['laplace'])
frequency       = Symbol(project_config['math']['frequency'])
numer           = project_config['math']['numer']
denom           = project_config['math']['denom']
lambdify        = project_config['math']['lambdify']
step_function   = eval(project_config['math']['stepfunction'])
factor          = eval(project_config['math']['factor'])
max_rec_subst   = eval(project_config['math']['maxrecsubst'])
reduce_matrix   = eval(project_config['math']['reducematrix'])
reduce_circuit  = eval(project_config['math']['reducecircuit'])
hz              = eval(project_config['display']['Hz'])
gain_colors     = project_config['gaincolors']
plot_fontsize   = eval(project_config['plot']['plotfontsize'])
axis_height     = eval(project_config['plot']['axisheight'])
axis_width      = eval(project_config['plot']['axiswidth'])
line_width      = eval(project_config['plot']['linewidth'])
marker_size     = eval(project_config['plot']['markersize'])
svg_margin      = eval(project_config['plot']['svgmargin'])
line_type       = project_config['plot']['linetype']
legend_loc      = project_config['plot']['legendloc']
default_colors  = project_config['plot']['defaultcolors'].split(',')
default_markers = project_config['plot']['defaultmarkers'].split(',')
plot_file_type  = project_config['plot']['plotfiletype']
notebook        = False

SLiCAPPARAMS    = {} # Entries will be generated during circuit check
