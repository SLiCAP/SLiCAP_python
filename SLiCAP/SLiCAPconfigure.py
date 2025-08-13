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
    SLiCAPconfig['math']         = {"laplace"               : "s",
                                    "frequency"             : "f",
                                    "numer"                 : "ME",
                                    "denom"                 : "ME",
                                    "lambdify"              : "numpy",
                                    "stepfunction"          : True,
                                    "factor"                : True,
                                    "maxrecsubst"           : 15,
                                    "reducematrix"          : True,
                                    "reducecircuit"         : True
                                    }
    SLiCAPconfig['balancing']    = {"update_srcnames"       : True,
                                    "pair_ext"              : "P,N",
                                    "remove_param_pair_ext" : True}
    SLiCAPconfig['plot']         = {"axisheight"            : 5,
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
    SLiCAPconfig['gaincolors']   = {"asymptotic"            : "r",
                                    "gain"                  : "b",
                                    "loopgain"              : "k",
                                    "servo"                 : "m",
                                    "direct"                : "g",
                                    "ideal"                 : "c",
                                    "vi"                    : "c"
                                    }
    SLiCAPconfig['display']      = {'Hz'                    : True,
                                    'Digits'                : 4,
                                    'notebook'              : False,
                                    'scalefactors'          : False,
                                    'engnotation'           : True}
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
                     "mainlibs"    : os.path.join(install_path, 'SLiCAP/files/lib/'),
                     "kicadsyms"   : os.path.join(install_path, 'SLiCAP/files/kicad/SLiCAP.kicad_sym'),
                     "ngspicesyms" : os.path.join(install_path, 'SLiCAP/files/kicad/SPICE.kicad_sym'),
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
                                  'ngspice'          : ''}
                      }
    return default_config

def _get_home_path():
    slicap_home  = expanduser("~").replace('\\', '/') + '/'
    return slicap_home
    
def _read_project_config():
    try:
        if os.path.isfile("./SLiCAP.ini"):
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
        _write_main_config(main_config)
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
        print('ini.reduce_circuit         =', reduce_circuit)
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
lambdify              = project_config['math']['lambdify']
step_function         = eval(project_config['math']['stepfunction'])
factor                = eval(project_config['math']['factor'])
max_rec_subst         = eval(project_config['math']['maxrecsubst'])
reduce_matrix         = eval(project_config['math']['reducematrix'])
reduce_circuit        = eval(project_config['math']['reducecircuit'])

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
