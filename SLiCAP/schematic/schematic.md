#. Bug fixes, modifications and additions

##. Bugs

(none open)

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

##. Completed (2026-06-24)

1. Properties dialog: the "model" field is now a free text input instead of a
   single-item drop-down, so any model / subcircuit name can be typed.

2. A "?" placeholder model (the symbol's `data-model` SVG meta field) is shown on
   the canvas by default, as a reminder that a `.model` definition is still required.

3. Parameter values/expressions no longer require curly brackets to be typed. The
   user enters the bare expression; the program adds `{ }` only for the netlist and
   for LaTeX rendering (rendering is the default). Braces are stripped in the
   Properties dialog, and a bare "?" is never braced.

4. File -> Export defaults the save-dialog filename to `<schematic>.cir`,
   `<schematic>.svg` and `<schematic>.pdf` respectively.

5. Tools -> "Load selected symbols from library": replaces the cached definition of
   the selected symbol(s) — and every instance on the canvas — with the most recent
   version from the symbol library. Pin positions may change, so connections may
   break; restoring them is left to the user.

6. IEEE-compatible LaTeX formatting: subscripts that are plain alphanumeric labels
   are set upright (`\mathrm`) rather than italic, applied at the single SLiCAP->LaTeX
   boundary so component value labels and the parameter & model tables are all
   consistent. Manually entered LaTeX fragments are kept user-defined. A bare "?"
   reminder is rendered literally and never sent to the SLiCAP expression parser
   (no more Sympify errors).

7. Netlist generation (GUI export, CLI, and subcircuit creation) aborts with an
   error and writes nothing when an unresolved "?" remains: missing value, missing
   model, missing reference, or missing connection. All problems are reported
   together so the netlist never contains "?".

8. Fixed: on the canvas the gap between a parameter name and its LaTeX-rendered
   value is no longer too large (now at most one non-LaTeX character wide).

