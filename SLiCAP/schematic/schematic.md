#. Bug fixes, modifications and additions

##. Bugs

On the canvas, the distance between a parameter name and a LaTeX rendered value is too large, the spacing should not be more than 1 non-latex-rendered character.

##. Additions

1. Missing .model declaration in the netlist.

   On the place menu add "Model definition", clicking it opens the "Add / Edit Model definition" dialog window:
   
   - Text box "Model name" enter the model name
   - Select box "SLiCAP" or "SPICE" (defaults to "SLiCAP")
   - Drop-down menu "Model Type", items must be taken from SLiCAP.SLiCAPprotos.py
   - Lines for entering model parameter definitions
   
   The netlister generates for each model definition a netlist line:
   
   .model <model name> <model type> (par1=value1 (par2=value2 ... ))
   
   This line is displayed on the canvas
   
2. Missing .lib .inc definition

   On the place menu add "Library link", clicking it opens the "Add / Edit library link" dialog window:
   
   - Select box ".inc" or ".lib"
   - Select box "SLiCAP" or "SPICE" (defaults to "SLiCAP")
   - File select box for entering library file
   - If "SPICE" and ".lib" then a text input box for "Corner", can be left empty
   
   The netlister generates for each library definition a netlist line:
   
   .lib | .inc "<file name>" <Corner>
   
   This line is displayed on the canvas

