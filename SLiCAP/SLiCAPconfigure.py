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

TIMEOUT = 120
    
if platform.system() == 'Windows':
    import win32api
    import windows_tools.installed_software as wi

install_version = "3.0.1"

def _check_version():
    """
    Checks the version with the latest SLiCAP version from Git

    Returns
    -------
    None.
    """
    latest = _get_latest_version()
    if install_version != latest:
        print("A new version of SLiCAP is available, please get it from 'https://github.com/SLiCAP/SLiCAP_python.git'.")
    else:
        print("SLiCAP Version matches with the latest release of SLiCAP on github.")
    return latest
    
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
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        print("Could not access github to check the latest available version of SLiCAP.")
        version = None
    return version

def _find_installed_windows_software():
    """
    Searches for installed packages from the package list

    Returns
    -------
    Dictionary with key-value pairs: key = package name, value = command
    """
    package_list = ['LTspice', 'Inkscape', 'KiCad', 'gEDA', 'NGspice']
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
                            elif package == 'Inkscape':
                                if re.match('Inkscape', name, flags=0):
                                    file_name = os.path.join(root, name,'bin','inkscape.exe')
                                    if os.path.exists(file_name):
                                        found = True
                                        print("Inkscape command set as:", os.path.join(root,name,'inkscape.exe'))
                                        commands[p_name] = file_name
                                        found = True
                            elif package == 'KiCad':
                                if re.match('KiCad', name, flags=0):
                                    version=os.listdir(os.path.join(root, name))[0]
                                    file_name = os.path.join(root, name, version, 'bin','kicad-cli.exe')
                                    if os.path.exists(file_name):
                                        print("KiCad command set as:", os.path.join(root,name,'kicad-cli.exe'))
                                        commands[p_name] = file_name
                                        found = True
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
              "the main configuration file: 'SLiCAP.ini' in the ~/SLiCAP/ " +
              "folder. More information is available in the SLiCAP HTML help.")
    # Complete the commands dictionary
    if len(found_list) != len(package_list):
        for package in package_list:
            p_name = package.lower()
            if p_name not in found_list:
                commands[p_name] = ''
            if package not in search_list:
                print("-", package, ": not installed")      
    if len(search_list) != len(package_list):
        print("After installation of missing apps, delete the 'SLiCAP.ini' " +
              "file in the ~/SLiCAP/ folder. It will be recreated with the " +
              "next SLiCAP import.")
    commands['lepton-eda'] = ''
    return commands

def _find_LTspice_wine():
    """
    Searches for LTspice under Linux or MacOS

    Returns
    -------
    LTspice command
    """
    home = expanduser("~")
    drives = [os.path.join(home, '.wine', 'drive_c')]
    cmd = ''
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
    return cmd

def _find_installed_software():
    system = platform.system()
    commands = {}
    commands['ltspice']      =  _find_LTspice_wine()
    commands['inkscape']     = 'inkscape'
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
        print("After installation of missing apps, delete the 'SLiCAP.ini' " +
              "file in the ~/SLiCAP/ folder. It will be recreated with the " +
              "next SLiCAP import.")
    return commands

def _generate_project_config():
    os.path.abspath('.') + '/'
    project_path  = os.path.abspath('.').replace('\\', '/') + '/'
    project_paths = {"project"   : project_path,
                     "html"      : project_path + 'html/',
                     "cir"       : project_path + 'cir/',
                     "lib"       : project_path + 'lib/',
                     "csv"       : project_path + 'csv/',
                     "txt"       : project_path + 'txt/',
                     "img"       : project_path + 'img/',
                     "mathml"    : project_path + 'mathml/',
                     "sphinx"    : project_path + 'sphinx/',
                     "tex"       : project_path + 'tex/'
                    }
    SLiCAPconfig = configparser.ConfigParser()
    SLiCAPconfig['math']         = {"laplace"        : "s",
                                    "frequency"      : "f",
                                    "numer"          : "ME",
                                    "denom"          : "ME",
                                    "lambdify"       : "numpy",
                                    "stepfunction"   : True,
                                    "factor"         : True,
                                    "maxrecsubst"    : 15
                                    }
    SLiCAPconfig['plot']         = {"axisheight"     : 5,
                                    "axiswidth"      : 7,
                                    "defaultcolors"  : "r,b,g,c,m,y,k",
                                    "defaultmarkers" : "",
                                    "legendloc"      : "best",
                                    "plotfontsize"   : 12,
                                    "plotfiletype"   : "svg"
                                    }                            
    SLiCAPconfig['gaincolors']   = {"asymptotic"     : "r",
                                    "gain"           : "b",
                                    "loopgain"       : "k",
                                    "servo"          : "m",
                                    "direct"         : "g",
                                    "vi"             : "c"
                                    }
    SLiCAPconfig['display']      = {'Hz'             : True,
                                    'Digits'         : 4}
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
    _write_project_config(SLiCAPconfig)
    return SLiCAPconfig
     
def _generate_main_config():
    install_path  = inspect.getfile(_find_installed_software).replace('\\', '/').split('/')
    install_path  = '/'.join(install_path[0:-2]) + '/'
    slicap_home   = expanduser("~").replace('\\', '/')
    home_path     = slicap_home + '/SLiCAP/'
    install_paths = {"install"   : install_path,
                     "user"      : home_path,
                     "docs"      : os.path.join(home_path, 'docs/'),
                     "libs"      : os.path.join(home_path, 'lib/'),
                     "examples"  : os.path.join(home_path, 'examples/')
                     }
    gain_types    = "gain,asymptotic,loopgain,servo,direct,vi"
    data_types    = "dc,dcvar,dcsolve,laplace,numer,denom,solve,noise,pz,poles,zeros,time,impulse,step"
    
    if platform.system() == 'Windows':
        commands = _find_installed_windows_software()
    else:
        commands =  _find_installed_software()
    SLiCAPconfig = configparser.ConfigParser()
    SLiCAPconfig['version']      = {"install_version" : install_version,
                                     "latest_version" : _check_version()}
    SLiCAPconfig['installpaths'] = install_paths
    SLiCAPconfig['commands']     = commands
    SLiCAPconfig['simulation']   = {'gain_types': gain_types,
                                    'data_types': data_types,
                                    'sim_types' : "symbolic, numeric"
                                    }
    _write_main_config(SLiCAPconfig)
    return SLiCAPconfig

def _get_home_path():
    slicap_home  = expanduser("~").replace('\\', '/')
    return slicap_home + '/SLiCAP/'
    
def _read_config():
    main_config_dict    = _read_main_config()
    project_config_dict = _read_project_config()
    config_dict         = configparser.ConfigParser()
    for key in main_config_dict.keys():
        config_dict[key] = main_config_dict[key]
    for key in project_config_dict.keys():
        config_dict[key] = project_config_dict[key]
    return config_dict
    
def _read_project_config():
    if  os.path.isfile("./SLiCAP.ini"):
        config_dict = configparser.ConfigParser()
        with open("SLiCAP.ini") as f:
            config_dict.read_file(f)
    else:
        print("Generating project configuration file: SLiCAP.ini,\n")
        config_dict = _generate_project_config()
    return config_dict

def _read_main_config():
    path = _get_home_path() + "SLiCAP.ini"
    if  os.path.isfile(path):
        config_dict = configparser.ConfigParser()
        with open(path) as f:
            config_dict.read_file(f)
    else:
        print("Generating main configuration file: ~/SLiCAP/SLiCAP.ini,\n")
        config_dict = _generate_main_config()
    return config_dict

def _write_project_config(config_dict):
    with open("SLiCAP.ini", "w") as f:
        config_dict.write(f)

def _write_main_config(config_dict):
    with open(_get_home_path() + "SLiCAP.ini", "w") as f:
        config_dict.write(f)

def _get_tf(key, subkey):
    tf = config[key][subkey].lower()
    if tf == "true":
        tf = True
    elif tf == "false":
        tf = False
    else:
        tf = None
    return tf

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
    

def dump():
    """
    Prints the global SLiCAP settings.
    
    :return None:
    :rtype NoneType:
        
    :example:
        
    >>> import SLiCAP as sl
    >>> sl.ini.dump()
    """
    config        = _read_config()
    # Global variables from configuration files
    print('ini.install_version =', config['version']['install_version'])
    print('ini.latest_version  =', config['version']['latest_version'])
    print('ini.install_path    =', config['installpaths']['install'])
    print('ini.home_path       =', config['installpaths']['user'])
    print('ini.main_lib_path   =', config['installpaths']['libs'])
    print('ini.example_path    =', config['installpaths']['examples'])
    print('ini.doc_path        =', config['installpaths']['docs'])
    print('ini.ltspice         =', config['commands']['ltspice'])
    print('ini.inkscape        =', config['commands']['inkscape'])
    print('ini.gnetlist        =', config['commands']['geda'])
    print('ini.kicad           =', config['commands']['kicad'])
    print('ini.ngspice         =', config['commands']['ngspice'])
    print('ini.lepton_eda      =', config['commands']['lepton-eda'])
    print('ini.project_path    =', config['projectpaths']['project'])
    print('ini.html_path       =', config['projectpaths']['html'])
    print('ini.cir_path        =', config['projectpaths']['cir'])
    print('ini.img_path        =', config['projectpaths']['img'])
    print('ini.csv_path        =', config['projectpaths']['csv'])
    print('ini.txt_path        =', config['projectpaths']['txt'])
    print('ini.tex_path        =', config['projectpaths']['tex'])
    print('ini.user_lib_path   =', config['projectpaths']['lib'])
    print('ini.mathml_path     =', config['projectpaths']['mathml'])
    print('ini.sphinx_path     =', config['projectpaths']['sphinx'])
    print('ini.html_prefix     =', config['html']['prefix'])
    print('ini.html_index      =', config['html']['current_index'])
    print('ini.html_page       =', config['html']['current_page'])
    print('ini.html_pages      =', config['html']['pages'].split(','))
    print('ini.html_labels     =', config['labels'])
    print('ini.disp            =', eval(config['display']['digits']))
    print('ini.last_updated    =', config['project']['last_updated'])
    print('ini.project_title   =', config['project']['title'])
    print('ini.created         =', config['project']['created'])
    print('ini.author          =', config['project']['author'])
    print('ini.laplace         =', Symbol(config['math']['laplace']))
    print('ini.frequency       =', Symbol(config['math']['frequency']))
    print('ini.numer           =', config['math']['numer'])
    print('ini.denom           =', config['math']['denom'])
    print('ini.lambdify        =', config['math']['lambdify'])
    print('ini.step_function   =', _get_tf('math', 'stepfunction'))
    print('ini.factor          =', _get_tf('math', 'factor'))
    print('ini.max_rec_subst   =', eval(config['math']['maxrecsubst']))
    print('ini.hz              =', _get_tf('display', 'Hz'))
    print('ini.gain_colors     =', dict(config['gaincolors']))
    print('ini.plot_fontsize   =', eval(config['plot']['plotfontsize']))
    print('ini.axis_height     =', eval(config['plot']['axisheight']))
    print('ini.axis_width      =', eval(config['plot']['axiswidth']))
    print('ini.legend_loc      =', config['plot']['legendloc'])
    print('ini.default_colors  =', config['plot']['defaultcolors'].split(','))
    print('ini.default_markers =', config['plot']['defaultmarkers'].split(','))
    print('ini.plot_fontsize   =', config['plot']['plotfontsize'])
    print('ini.plot_file_type  =', config['plot']['plotfiletype'])
    print('ini.gain_types      =', config['simulation']['gain_types'].split(','))
    print('ini.data_types      =', config['simulation']['data_types'].split(','))
    print('ini.sim_types       =', config['simulation']['sim_types'].split(','))
    print('ini.notebook        = ',False)
    
config        = _read_config()

# Global variables from configuration files
install_version = config['version']['install_version']
latest_version  = config['version']['latest_version']
install_path    = config['installpaths']['install']
home_path       = config['installpaths']['user']
main_lib_path   = config['installpaths']['libs']
example_path    = config['installpaths']['examples']
doc_path        = config['installpaths']['docs']
ltspice         = config['commands']['ltspice']
inkscape        = config['commands']['inkscape']
gnetlist        = config['commands']['geda']
kicad           = config['commands']['kicad']
ngspice         = config['commands']['ngspice']
lepton_eda      = config['commands']['lepton-eda']
project_path    = config['projectpaths']['project']
html_path       = config['projectpaths']['html']
cir_path        = config['projectpaths']['cir']
img_path        = config['projectpaths']['img']
csv_path        = config['projectpaths']['csv']
txt_path        = config['projectpaths']['txt']
tex_path        = config['projectpaths']['tex']
user_lib_path   = config['projectpaths']['lib']
mathml_path     = config['projectpaths']['mathml']
sphinx_path     = config['projectpaths']['sphinx']
html_prefix     = config['html']['prefix']
html_index      = config['html']['current_index']
html_page       = config['html']['current_page']
html_pages      = config['html']['pages'].split(',')
html_labels     = config['labels']
disp            = eval(config['display']['digits'])
last_updated    = config['project']['last_updated']
project_title   = config['project']['title']
created         = config['project']['created']
author          = config['project']['author']
laplace         = Symbol(config['math']['laplace'])
frequency       = Symbol(config['math']['frequency'])
numer           = config['math']['numer']
denom           = config['math']['denom']
lambdify        = config['math']['lambdify']
step_function   = _get_tf('math', 'stepfunction')
factor          = _get_tf('math', 'factor')
max_rec_subst   = eval(config['math']['maxrecsubst'])
hz              = _get_tf('display', 'Hz')
gain_colors     = config['gaincolors']
plot_fontsize   = eval(config['plot']['plotfontsize'])
axis_height     = eval(config['plot']['axisheight'])
axis_width      = eval(config['plot']['axiswidth'])
legend_loc      = config['plot']['legendloc']
default_colors  = config['plot']['defaultcolors'].split(',')
default_markers = config['plot']['defaultmarkers'].split(',')
plot_file_type  = config['plot']['plotfiletype']
gain_types      = config['simulation']['gain_types'].split(',')
data_types      = config['simulation']['data_types'].split(',')
sim_types       = config['simulation']['sim_types'].split(',')
notebook        = False

SLiCAPPARAMS    = {}
"""
if __name__ == "__main__":
    for mainkey in config.keys():
        print("\n", mainkey)
        for subkey in config[mainkey].keys():
            print('\t', subkey, ":", config[mainkey][subkey])"""