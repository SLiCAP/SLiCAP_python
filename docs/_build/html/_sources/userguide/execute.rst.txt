.. _Execute:

======================
Execute an instruction
======================

The method **SLiCAPinstruction.instruction.execute()** executes the instruction and returns a **SLiCAPprotos.allResults()** object with attributes comprising instruction data and instruction results. See `SLiCAPprotos.allResults() <../reference/SLiCAPprotos.html>`_.


-----------------
Execution results
-----------------

At the start of the execution, attributes from the instance of the **SLiCAPinstruction.instruction()** object are copied to corresponding attributes of the **SLiCAPprotos.allResults()** object. All copies, except that of the **SLiCAPinstruction.instruction.circuit** attribute are *deep* copies.

In the following sections we will describe the attributes that carry the execution results. We will do this for all data types.

Data type *dc*
--------------     

Calculates the DC value of the detector quantity; only for gain type 'vi'.

- If parameter stepping is enabled: 

  - A list with dc values (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.dc**

- If parameter stepping is disabled:

  - The dc value (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.dc**

Data type *dcsolve*
-------------------   

Calculates DC solution of the network; only for gain type 'vi'.

- If parameter stepping is enabled: 

  - A list with dc solutions (*symPy.Matrix*) is assigned to **SLiCAPprotos.allResults.dcSolve**

- If parameter stepping is disabled:

  - The dc solution (*symPy.Matrix*) is assigned to **SLiCAPprotos.allResults.dcSolve**

Data type *dcvar*
-----------------     

Calculates contribution of all dc variances (sources and resistors) to the detector-referred variance. Only for gain type 'vi'. If a signal source has been defined it also calculates the contibutions to the source-referred variance.

- If parameter stepping is enabled: 

  - A list with values of the total detector-referred variance (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.ovar**
  - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.ovarTerms**

    - key: Name of the source (*str*)
    - value: List with contributions of *source* to the detector-referred variance (*float, sympy.Symbol, symPy.Expr*)

  - If a signal source has been defined:

    - A list with values of the total source-referred variance (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.ivar**
    - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.ivarTerms**

      - key: Name of the source (*str*)
      - value: List with contributions of this source to the source-referred variance (*float, sympy.Symbol, symPy.Expr*)

- If parameter stepping is disabled:

  - The total detector-referred variance (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.ovar**
  - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.ovarTerms**

    - key: Name of the source (*str*)
    - value: Contributions of this source to the detector-referred variance (*float, sympy.Symbol, symPy.Expr*)

  - If a signal source has been defined:

    - The total source-referred variance (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.ivar**
    - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.ivarTerms**

      - key: Name of the source (*str*)
      - value: Contributions this source to the source-referred variance (*float, sympy.Symbol, symPy.Expr*)

Data type *denom*
-----------------     

Calculates the denominator of the Laplace Transform of the unit-impulse response or of a voltage or a current.

- If parameter stepping is enabled: 

  A list with results (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.denom**

- If parameter stepping is disabled: 

  The result (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.denom**

Data type *impulse*
-------------------     

Calculates the unit-impulse response (inverse Laplace Transform); may not work with symbolic values. Not for gain type 'vi'.

- If parameter stepping is enabled: 

  A list with results (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.impulse**

- If parameter stepping is disabled: 

  The result (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.impulse**

Data type *laplace*
-------------------    

Calculates the Laplace transfer function (Laplace transform of the unit-impulse response) or the Lapalce tarsnform of a voltage or a current.

- If parameter stepping is enabled: 

  A list with results (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.laplace**

- If parameter stepping is disabled: 

  The result (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.laplace**

Data type *matrix*
------------------     

Calculates the matrix equation of the circuit and applies the specified conversion. 

- If parameter stepping is disabled: 

  - The vector with independent variables (*sympy.Matrix*) is assigned to **SLiCAPprotos.allResults.Iv**
  - The vector with dependent variables (*sympy.Matrix*) is assigned to **SLiCAPprotos.allResults.Dv**
  - The MNA matrix (*sympy.Matrix*) is assigned to **SLiCAPprotos.allResults.M**

- Parameter stepping with data type 'matrix' is not supported.

Data type *noise*
-----------------     

Calculates contributions to the detector-referred noise of all noise sources. Only for gain type 'vi'. If a signal source has been defined it also calculates the contibutions to the source-referred noise.

- If parameter stepping is enabled: 

  - A list with values of the total detector-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.onoise**
  - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.onoiseTerms**

    - key: Name of the source (*str*)
    - value: List with contributions of this source to the detector-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*)

  - If a signal source has been defined:

    - A list with values of the total source-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.inoise**
    - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.inoiseTerms**

      - key: Name of the source (*str*)
      - value: List with contributions of this source to the source-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*)

- If parameter stepping is disabled:

  - The total detector-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.onoise**
  - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.onoiseTerms**

    - key: Name of the source (*str*)
    - value: Contributions of this source to the detector-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*)

  - If a signal source has been defined:

    - The total source-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*) is assigned to **SLiCAPprotos.allResults.noise**
    - A dict with key-value pairs is assigned to **SLiCAPprotos.allResults.inoiseTerms**

      - key: Name of the source (*str*)
      - value: Contributions of this source to the source-referred noise spectral density in :math:`\left[\mathrm{\frac{V^2}{Hz}}\right]` or :math:`\left[\mathrm{\frac{A^2}{Hz}}\right]` (*float, sympy.Symbol, symPy.Expr*)

Data type *numer*
-----------------    

Calculates the numerator of the Laplace Transform of the unit-impulse response or of a voltage or a current.

- If parameter stepping is enabled: 

  A list with results (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.numer**

- If parameter stepping is disabled: 

  The result (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.numer**


Data type *params*
------------------    

Calculates the values of parameters, while sweeping or stepping other parameters. This data type should be used when plotting parameters against each other. Only the copied instruction data is returned.

Data type *poles*
-----------------     

Calculates the complex solutions of the denominator of the Laplace transfer function. It may not work with symbolic parameters and it not implemented for dataType *vi*.

- If parameter stepping is enabled: 

  A list of lists with solutions (*complex*) is assigned to **SLiCAPprotos.allResults.poles**

- If parameter stepping is disabled:

  A list with solutions (*complex*) is assigned to **SLiCAPprotos.allResults.poles**

Data type *pz*
--------------    

Calculates the complex solutions of the numerator and of the denominator of the Laplace Transform of the unit-impulse response and the zero-frequency value of the transfer. Poles and zeros with the same frequency cancel each other out. It may not work with symbolic parameters and it not implemented for dataType *vi*.

.. admonition:: note

   pole-zero pairs with equal complex frequencies (tolerance = :math:`10^{\mathrm{-ini.disp}}`) are removed from the results.

- If parameter stepping is enabled: 

  - A list of lists with solutions (*complex*) of the denominator is assigned to **SLiCAPprotos.allResults.poles**
  - A list of lists with solutions (*complex*) of the numerator is assigned to **SLiCAPprotos.allResults.zeros**
  - A list with zero-frequency values (*float*) of the transfer is assigned to **SLiCAPprotos.allResults.DCvalue**

- If parameter stepping is disabled:

  - A list with solutions (*complex*) of the denominator is assigned to **SLiCAPprotos.allResults.poles**
  - A list with solutions (*complex*) of the numerator is assigned to **SLiCAPprotos.allResults.zeros**
  - The zero-frequency values (*float*) of the transfer is assigned to **SLiCAPprotos.allResults.DCvalue**

Data type *solve*
-----------------    

Calculates the network solution; only for gain type 'vi'.

- If parameter stepping is enabled: 

  - A list with solutions (*symPy.Matrix*) is assigned to **SLiCAPprotos.allResults.solve**

- If parameter stepping is disabled:

  - The solution (*symPy.Matrix*) is assigned to **SLiCAPprotos.allResults.solve**

Data type *step*
----------------     

Calculates inverse Laplace transform of (1/s) times the transfer function. It may not work with symbolic values.

- If parameter stepping is enabled: 

  A list with results (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.stepResp**

- If parameter stepping is disabled: 

  The result (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.stepResp**

Data type *time*
----------------    

Calculates inverse Laplace transform of a detector voltage or current. Only for gain type 'vi'. It may not work with symbolic values.

- If parameter stepping is enabled: 

  A list with results (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.time**

- If parameter stepping is disabled: 

  The result (*float, sympy.Expr*) is assigned to **SLiCAPprotos.allResults.time**

Data type *zeros*
-----------------    

Calculates the complex solutions of the numerator of the Laplace transfer function. It may not work with symbolic parameters and it not implemented for dataType *vi*.

- If parameter stepping is enabled: 

  A list of lists with solutions (*complex*) is assigned to **SLiCAPprotos.allResults.poles**

- If parameter stepping is disabled:

  A list with solutions (*complex*) is assigned to **SLiCAPprotos.allResults.poles**
