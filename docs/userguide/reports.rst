==============
Create reports
==============
    
.. image:: /img/colorCode.svg

With SLiCAP you document your design while doing the design work:

- HMTL reporting tools let you create one-click updatable management presentations or detailed design websites
- LaTeX reporting tools let you create single-click updated publications and design reports.

SLiCAP is also compatible with Jupyter Notebooks.

Create SLiCAP-style websites
============================

SLiCAP-style websites are simple and have no width limitation. Style information is stored in the ``html/css/`` folder in the project driercory.

Use functions from the `SLiCAPhtml <../reference/SLiCAPhtml.html>`__ module to create a website with text, tables, typesetted equations, and figures. 

The example: `My First RC Network <https://github.com/SLiCAP/SLiCAPexamples/tree/main/Examples/myFirstRCnetwork>`_ shows you how to create a default SLiCAP-style project website.

Below a brief overview of related topics; examples are taken from ``myFirstRCnetwork.py``.

Project initialization
----------------------

.. literalinclude:: ../myFirstRCnetwork.py
    :linenos:
    :lines: 1-17
    :lineno-start: 1
    
After project initialization:

#. The ``index.html`` file is created in the html folder in the project directory
#. The project configuration is updated:

   .. code-block:: 
   
       >>> sl.ini.dump("html")
       
       HTML
       ----
       ini.html_prefix            = 
       ini.html_index             = index.html
       ini.html_page              = index.html
       ini.html_pages
	        index.html
       ini.html_labels

   #. html_prefix
   
      String added at the start of each new HTML page name
      
   #. html_index
   
      Acitve index page: if a new HTML page is created, a link to it is shown on the active index page.
      
   #. html_page
   
      Active HTML page: equations, tables, text, etc, will be written to this page.
      
   #. html_pages
   
      A list with HTML page names
      
   #. html_labels
   
      A list with HTML labels

Circuit data created with makeCircuit()
---------------------------------------

The instruction ``makeCircuit()`` creates a new circuit index page on the main index page and a page ``<circuit title>_Circuit-data.html``.

.. literalinclude:: ../myFirstRCnetwork.py
    :linenos:
    :lines: 19-34
    :lineno-start: 1
    
.. code-block::

    >>> sl.ini.dump("html")

    HTML
    ----
    ini.html_prefix            = myFirstRCnetwork_
    ini.html_index             = myFirstRCnetwork_index.html
    ini.html_page              = myFirstRCnetwork_Circuit-data.html
    ini.html_pages
	     index.html
	     myFirstRCnetwork_index.html
	     myFirstRCnetwork_Circuit-data.html
    ini.html_labels
    label : fig_myFirstRCnetwork.kicad_sch
	    type        : fig
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Circuit diagram of myFirstRCnetwork."
    label : netlist_myFirstRCnetwork
	    type        : data
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Netlist of myFirstRCnetwork.cir."
    label : elementdata_myFirstRCnetwork
	    type        : data
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Expanded netlist of myFirstRCnetwork.cir."
    label : params_myFirstRCnetwork
	    type        : data
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Parameter definitions of myFirstRCnetwork.cir."

Complete website
----------------

After running the complete example a complete website has been created and some page information is stored in the SLiCAP.ini file in the project directory:

.. code-block::

    >>> sl.ini.dump("html")

    HTML
    ----
    ini.html_prefix            = myFirstRCnetwork_
    ini.html_index             = myFirstRCnetwork_index.html
    ini.html_page              = myFirstRCnetwork_Links.html
    ini.html_pages
	     index.html
	     myFirstRCnetwork_index.html
	     myFirstRCnetwork_Circuit-data.html
	     myFirstRCnetwork_Matrix-equations.html
	     myFirstRCnetwork_Plots.html
	     myFirstRCnetwork_Poles-and-zeros.html
	     myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	     myFirstRCnetwork_Links.html
    ini.html_labels
    label : fig_myFirstRCnetwork.kicad_sch
	    type        : fig
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Circuit diagram of myFirstRCnetwork."
    label : netlist_myFirstRCnetwork
	    type        : data
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Netlist of myFirstRCnetwork.cir."
    label : elementdata_myFirstRCnetwork
	    type        : data
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Expanded netlist of myFirstRCnetwork.cir."
    label : params_myFirstRCnetwork
	    type        : data
	    href        : myFirstRCnetwork_Circuit-data.html
	    description : "Parameter definitions of myFirstRCnetwork.cir."
    label : MNA
	    type        : eqn
	    href        : myFirstRCnetwork_Matrix-equations.html
	    description : "MNA equation of the network"
    label : Iv
	    type        : eqn
	    href        : myFirstRCnetwork_Matrix-equations.html
	    description : "Vector with independent variables"
    label : M
	    type        : eqn
	    href        : myFirstRCnetwork_Matrix-equations.html
	    description : "MNA matrix"
    label : Dv
	    type        : eqn
	    href        : myFirstRCnetwork_Matrix-equations.html
	    description : "Vector with dependent variables"
    label : gainLaplace
	    type        : eqn
	    href        : myFirstRCnetwork_Matrix-equations.html
	    description : "Laplace transfer function"
    label : figMag
	    type        : fig
	    href        : myFirstRCnetwork_Plots.html
	    description : "Magnitude characteristic of the RC network."
    label : figPolar
	    type        : fig
	    href        : myFirstRCnetwork_Plots.html
	    description : "Polar plot of the transfer of the RC network."
    label : figdBmag
	    type        : fig
	    href        : myFirstRCnetwork_Plots.html
	    description : "dB Magnitude characteristic of the RC network."
    label : figPhase
	    type        : fig
	    href        : myFirstRCnetwork_Plots.html
	    description : "Phase characteristic of the RC network."
    label : figDelay
	    type        : fig
	    href        : myFirstRCnetwork_Plots.html
	    description : "Group delay characteristic of the RC network."
    label : PZlistSym
	    type        : data
	    href        : myFirstRCnetwork_Poles-and-zeros.html
	    description : "Symbolic values of the poles and zeros of the network"
    label : PZlist
	    type        : data
	    href        : myFirstRCnetwork_Poles-and-zeros.html
	    description : "Poles and zeros of the network"
    label : figPZ
	    type        : fig
	    href        : myFirstRCnetwork_Poles-and-zeros.html
	    description : "Poles and zeros of the RC network."
    label : figStep
	    type        : fig
	    href        : myFirstRCnetwork_Poles-and-zeros.html
	    description : "Unit step response of the RC network."
    label : desEq
	    type        : heading
	    href        : myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	    description : "Design equations for $R$ and $C$"
    label : mu_t
	    type        : eqn
	    href        : myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	    description : "Symbolic expression of the unit step response"
    label : epsilon_t
	    type        : eqn
	    href        : myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	    description : "Symbolic expression of the settling error versus time"
    label : tau_s
	    type        : eqn
	    href        : myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	    description : "Symbolic expression of the settling time"
    label : RR1
	    type        : eqn
	    href        : myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	    description : "Design equation for $R$"
    label : CC1
	    type        : eqn
	    href        : myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	    description : "Design equation for $C$"
    label : Rvalue
	    type        : eqn
	    href        : myFirstRCnetwork_Design-equations-for-$R$-and-$C$.html
	    description : "Numeric value of $R$"
			    
Create Sphinx-style websites
============================

#. Write your report in ReStructured Text and use functions from the `SLiCAPrst <../reference/SLiCAPrst.html>`__ module for creating and updating design data.
#. Compile your website with `Sphinx <https://www.sphinx-doc.org/en/master/>`_

The example: `SLiCAP Sphinx report example <https://github.com/SLiCAP/SLiCAPexamples/tree/main/Examples/Reports>`_ is completely devoted to this topic. It uses a the `Sphinx Book Theme <https://sphinx-book-theme.readthedocs.io/en/stable/contributing/style.html>`_ as output format.
    
Create LaTeX-style PDF reports
==============================

#. Write your report in LaTeX and use functions from the `SLiCAPlatex <../reference/SLiCAPlatex.html>`__ module for creating and updating design data.
#. Compile your report with `LaTeX <https://www.latex-project.org/>`_

The example: `SLiCAP LaTeX report example <https://github.com/SLiCAP/SLiCAPexamples/tree/main/Examples/Reports>`_. is completely devoted to this topic. 

Create Jupyter Notebooks
========================

The example: `My First RC Network <https://github.com/SLiCAP/SLiCAPexamples/tree/main/Examples/myFirstRCnetwork>`_ (``myFirstRCnetwork.ipynb``) shows you how to work with `Jupyter Notebooks <https://jupyter.org/>`_.

.. image:: /img/colorCode.svg
