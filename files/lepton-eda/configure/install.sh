#!/bin/sh
found=$(locate gnet-spice.scm)
if [ -z $found ] ; then
    echo Coud not find installation path.
else
    dir=$(dirname $found)
    sudo cp gnet-spice-noqsi.scm $dir
    echo Successfully copied: gnet-spice-noqsi.scm to: $dir
fi
lepton-cli config --user "netlist" "default-net-name" ""
lepton-cli config --user "schematics.gui" "default-titleblock" ""
cp gafrc ~/.config/lepton-eda/
cp gschemrc ~/.config/lepton-eda/
echo Configured lepton-eda.
