#!/bin/bash
declare -A test_cirs
# test_cirs is a dictionary with the directory as a key and the value as the run file
test_cirs["balancedCircuits"]="balancedCircuitsProject.py"
#test_cirs["CSstage"]="CSresnoise.py"
#test_cirs["FilterDesign"]="LR4project.py"
#test_cirs["myFirstRCnetwork"]="myFirstRCnetwork.py"
#test_cirs["noiseFigure"]="noiseFigures.py"
#This will make sure no plots are shown:
mkdir allhtml
cp Template.rst ExampleCirs.rst

for key in "${!test_cirs[@]}"; do
    cd $key
    python ${test_cirs[$key]}
    mkdir ../allhtml/$key
    mv  -v html/* ../allhtml/$key
    cd ..
    echo "   - \`${key} <../../examples/${key}>\`_" >> ExampleCirs.rst
done

mv  ExampleCirs.rst ../../docs/tutorials/ExampleCirs.rst
