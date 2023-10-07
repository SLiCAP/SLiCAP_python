=====================
Generate HTML reports
=====================

Writing design documentation is often something that needs to be done after the design work has been finished. By then, all kinds of information needs to be collected and structured in a document, while in many cases new projects are already taking most of the time. This undesirable but almost always inevitable practice can be prevented if the design work goes hand in hand with generation of the design documents. SLiCAP supports this with the generation of web-based design documentation in which figures, tables, expressions and ASCII files can be updated while running SLiCAP-MATLAB scripts. In this way, presentations and documentation can be kept up-to-date with the actual state of the design.

SLiCAP distinguishes two types of html pages:

- index pages: used for displaying tables of contents with links to other pages

  The attribute *ini.htmlIndex* is the name of the active index page

- data pages: used for displaying all kinds of design data, such as, tables, equations, text, graphs, images, etc.

  The attribute *ini.htmlPage* is the name of the active data page. 

- A list with the names of all the html pages is stored in *ini.htmlPages*

Detailed information about all html functions can be found in the module reference `SLiCAPhtml.py <../reference/SLiCAPhtml.html>`_.

.. _html:

-------------------
HTML site structure
-------------------

The structure of the project web site that can be generated with SLiCAP will be discussed below.

Main Index.html
---------------

Initialization of a project generates an *index.html* file in the *html/* project subdirectory. This file will hold the main table of contents of your project. Each time you check a circuit netlist that resides in the project directory, a list entry will be generated in this index file. 

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>>                                          # and create main index page
    >>> print(ini.htmlIndex)                     # print the active index page

    index.html

Circuit index file
------------------

With the checking of a circuit, a circuit index page is generated:

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>>                                          # and create main index page
    >>> instr = instruction()                    # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    >>>                                          # and create circuit index page

    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> print(ini.htmlIndex)                     # print the active index page

    My-first-RC-network_index.html

---------------------
Start a new html page
---------------------

It is a good practice to start a new html (data) page after checking the circuit, this prevents output to be writen to index files which would mess up the table of contents.

A new html data page can be created by evoking the command *htmlPage(< pageTitle >)*, in which *pageTitle* is the title of the new page (without .html file extension). After creation this new page is automatically assigned as active html data page. With the creation of a data page, a link to this data page is placed on the active index page.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>>                                          # and create main index page
    >>> instr = instruction()                    # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    >>>                                          # and create circuit index page

    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> htmlPage('Circuit data')                 # Create a new html data page and make it the 
    >>>                                          # active data page and returns the HTML code:
    >>>                                          # <H1>Circuit data</H1>
    >>> print(ini.htmlPage)

    My-first-RC-network_Circuit-data.html

    >>> print(ini.htmlPages)

    ['My-first-RC-network_index.html', 'index.html', 'My-first-RC-network_Circuit-data.html']

A new html index page can be created by evoking the command *htmlPage(< pageTitle >, index=True)*, in which *pageTitle* is the title of the new index page (without .html file extension).

After the creation this new index page, a link to this page is placed on the active index page. Subsequently, the new index page is assigned as new index page.

------------------------------
Place a header on an HTML page
------------------------------

You can place headers (level 2 and level 3) on the active HTML page and (optionally) assign a label to a header.

.. code-block:: python

    >>> head2html("heading 2", label='my header 2 label')

    '<a id="my header 2 label"</a><h2>heading 2</h2>'

    >>> head3html("heading 3", label='my header 3 label')

    '<a id="my header 3 label"</a><h3>heading 3</h3>'

--------------------------
Place text on an HTML page
--------------------------

.. code-block:: python

    >>> text2html("This is some text including $\LaTeX$ code.") 

    '<p>This is some text including $\LaTeX$ code.</p>'


---------------------------------
Place a text file on an HTML page
---------------------------------

You can place the contents of a text file, including html code and :math:`\LaTeX` code on the active HTML file with the instruction:

.. code-block:: python

    >>> file2html("myIntroduction.txt")

By default, the text file should be located in the */txt* sub directory in your project folder. You can change the path to this file in the file *'SLiCAPconfig.py'* in the project folder. 

This function returns the contents of the file in string format.
    
------------------------------
Place an image on an HTML page
------------------------------

You can place an image on the active HTML page and assign a caption and a label to it.

.. code-block:: python

    >>> img2html("myCircuit.svg", 800, caption="Schematic diagram of my circuit", "label="myCircuitLabel") 

    'html/img/myCircuit.svg'

This places: *'<figure><a>"myCircuitLabel"</a><img src="img/myCircuit.svg" alt="Schematic diagram of my circuit" style="width:800px"><figcaption>Figure: myCircuit.svg<br>Schematic diagram of my circuit</figcaption></figure>'* on the active html page.

It also copies the image file to the */img* subdirectory of the */html* directory in the project folder.

By default, the image file should be located in the */img* sub directory in your project folder. You can change the path to this file in the file *'SLiCAPconfig.py'* in the project folder. 

This function returns the path to the image file in string format.

----------------------------------------------
Place the netlist of a circuit on an HTML page
----------------------------------------------

You can place the netlist of the circuit as pre formatted text (fixed width font) on the active HTML page and add a label to it.

.. code-block:: python

    >>> netlist2html("myFirstRCnetwork.cir", label="netlistLabel") 

    '<h2><a id="netlistLabel"></a>Netlist: myFirstRCnetwork.cir</h2>
    <pre>
    "My First RC network"
    V1 N001 0 V value=1 dc=0 dcvar=0 noise=0
    R1 N001 out {R}
    C1 out 0 {C}
    .param R=1k C={1/(2*pi*R*f_c)} f_c=1k
    .end</pre>'

By default, the netlist file (*.cir* file extension) file should be located in the */cir* sub directory in your project folder. You can change the path to this file in the file *'SLiCAPconfig.py'* in the project folder. 

This function returns the code placed on the active HTML page.

------------------------------------------------
Place the flattened circuit data on an HTML page
------------------------------------------------

SLiCAP uses an expanded circuit for analysis. In this circuit, elements of built-in sub circuit models, such as, operational amplifiers and semiconductor devices, as well as elements of user-defined sub circuits are added and connected to the main circuit. All elements of the expanded (flattened) circuit with their nodes, references and parameters can be displayed on the active HTML page using one command:

.. code-block:: python

    >>> instr = instruction()
    >>> instr.setCircuit("myFirstRCnetwork.cir")
    >>> htmlPage("Circuit data")
    >>> elementData2html(instr.circuit, label="circuitElements", caption="Expanded circuit")

This function returns the code placed on the active HTML page.

------------------------------------
Place all parameters on an HTML page
------------------------------------

You can list all parameters used in expressions of circuit elements and in parameter definitions on the active HTML page. The instruction *params2html(<instruction.circuit>)* will list all parameters with their definition and their value after recursive substitution of all parameters, including the global parameters that are used. It will also list the undefined parameters.

.. code-block:: python

    >>> instr = instruction()
    >>> instr.setCircuit("myFirstRCnetwork.cir")
    >>> htmlPage("Circuit data")

    >>> params2html(instr.circuit, label="circuitElements", caption="Circuit parameters)

This function returns the code placed on the active HTML page.

-----------------------------------
Place an expression on an HTML page
-----------------------------------

.. code-block:: python

    >>> expr = sp.sympify("R_DC/(1+s*tau)")

    >>> expr2html(expr, units = '\\Omega')

    '$\frac{R_{DC}}{1+s \tau} \left[\mathrm{\Omega}\right]$'

This function returns the code placed on the active HTML page.

---------------------------------
Place an equation on an HTML page
---------------------------------

.. code-block:: python

    >>> lhs = sp.Symbol("Z_t")
    >>> rhs = sp.sympify("R_DC/(1+s*tau)")

    >>> eqn2html(lhs, rhs, units = '\\Omega', label = 'eq_trimp', labeltext = 'transimpedance')

    '<a id="eq_trimp"></a>
    \begin{equation}
    Z_t=\frac{R_{DC}}{1+s\tau}\left[\mathrm{\Omega}\right]
    \end{equation}'

This function returns the code placed on the active HTML page.

---------------------------------------------------
Place the circuit's matrix equation on an HTML page
---------------------------------------------------

.. code-block:: python

    >>> instr = instruction()
    >>> instr.setCircuit('myFirstRCnetwork')
    >>> instr.setSimType("symbolic")
    >>> instr.setGainType("vi")
    >>> instr.setDataType("matrix")
    >>> result = instr.execute()

    >>> matrices2html(result, label = 'eq_MNA', labeltext = 'MNA matrix equation')

This function returns the code placed on the active HTML page.

----------------------------
Place a plot on an HTML page
----------------------------

See `plots.html <plots.html>`_ for details on plotting.

.. code-block:: python

    >>> fig2html(myFigure, 800, label='myLabel', caption='Caption of this figure')

This function returns the path to the image file in string format.

---------------------------------
Place a csv table on an HTML page
---------------------------------

The following code displays a csv file *'specifications.csv'* in table format on the active HTML page. 

By default, the csv file should be located in the */csv* sub directory in your project folder. You can change the path to this file in the file *'SLiCAPconfig.py'* in the project folder. 

:math:`\LaTeX` code in the cells of this csv file will be rendered properly.

.. code-block:: python

    >>> csv2html('specifications.csv', label = 'specs', separator = ',' , caption = 'Performance requirements')

This function returns the code placed on the active HTML page.

-----------------------------------------------------
Place the results of a noise analysis on an HTML page
-----------------------------------------------------

See `noise.html <noise.html>`_ for details on noise analysis.

.. code-block:: python

    >>> instr = instruction()
    >>> # Define all required attributes for noise analysis
    >>> # execute the instruction
    >>> result = instr.execute()

    >>> noise2html(result, label = 'noise_results', labeltext = 'Noise analysis results')

This function returns the code placed on the active HTML page.

-----------------------------------------------------
Place the results of a dcvar analysis on an HTML page
-----------------------------------------------------

See `dcvar.html <dcvar.html>`_ for details on dcvar analysis.

.. code-block:: python

    >>> instr = instruction()
    >>> # Define all required attributes for dcvar analysis
    >>> # execute the instruction
    >>> result = instr.execute()

    >>> dcvar2html(result, label = 'dcvar_results', labeltext = 'DC variance analysis results')

This function returns the code placed on the active HTML page.

---------------------------------------------------------
Place the results of a pole-zero analysis on an HTML page
---------------------------------------------------------

See `pz.html <pz.html>`_ for details on pole-zero analysis.

.. code-block:: python

    >>> pz2html(result, label = '', labeltext = '')

This function returns the code placed on the active HTML page.

---------------------------------------------------------------------
Place the coefficients of a Laplace transfer function on an HTML page
---------------------------------------------------------------------

.. code-block:: python

    >>> coeffsTransfer2html(transferCoeffs, label = '', labelText = '')

This function returns the code placed on the active HTML page.

----------------------------------------------
Place a link to an HTML object on an HTML page
----------------------------------------------

.. code-block:: python

    >>> href('myLink', 'index.html')

This function returns the code placed on the active HTML page.

-----------------------------------------------
Place all links to HTML objects on an HTML page
-----------------------------------------------

.. code-block:: python

    >>> links2html()

This function returns the code placed on the active HTML page.

------------------------------------------------------
Place the step data for array stepping on an HTML page
------------------------------------------------------


.. code-block:: python

    >>> stepArray2html(instr.stepVars, instr.stepArray)

This function returns the code placed on the active HTML page.

