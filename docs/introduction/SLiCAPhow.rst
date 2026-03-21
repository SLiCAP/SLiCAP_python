=================
How to use SLiCAP
=================

.. image:: /img/colorCode.svg


SLiCAP is a tool designed to help you create and solve design equations for analog circuits. It supports both analog design automation and education

A **design equation** expresses the value of a specific circuit parameter, such as the value of a component, the operating current of a transistor, or the size of a transistor in terms of the circuit's requirements like low noise, power consumption, and bandwidth. It is the inverse of an analysis result that writes the performance in terms of circuit parameters.

To set up design equations, you need to perform (symbolic) circuit analysis with the parameter(s) of interest and find valid ranges for the parameter(s) by solving the analysis results with given specifications. However, solving equations symbolically can be challenging and is sometimes not feasible. Therefore, it's important to use **circuit models that are both simple and effective**. During each step of the design process, aim to use as few symbolic variables as possible and have clear objectives for performance and cost. This methodology aligns with a systems engineering design approach, as outlined in `Structured Electronic Design <https://analog-electronics.tudelft.nl/>`_.

Workflow
========

#. **Initialize a SLiCAP Project:** Begin by setting up a new project in SLiCAP: `Create a SLiCAP project <../userguide/install.html#create-a-slicap-project>`__.
#. **Create a Circuit Model:** Develop a model that links performance and cost factors to the relevant design parameter(s). Then, create a SLiCAP circuit object from this model: `Create a SLiCAP circuit object <../userguide/circuit.html>`__.
#. **Import Budgets and Parameters:** Import budgets for performance and cost factors from the design database, along with circuit parameters that were assigned values in earlier design stages: `Work with specifications. See: <../userguide/specifications.html>`__, and `Work with parameters <../userguide/parameters.html>`__.
#. **Performance/Cost Analysis:** Conduct a mixed symbolic/numeric analysis for the performance or cost factors of interest: `Perform analysis <../userguide/analysis.html>`__.
#. **Determine Valid Ranges:** Obtain valid ranges for the design parameters of interest as solutions derived from the analysis results, taking into account all relevant specifications. More details can be found here: `Work with analysis results <../userguide/math.html>`__.
#. **Assign Parameter Values:** Assign values to the circuit parameters within the valid ranges that you’ve determined. For guidance, refer to: `Work with parameters <../userguide/parameters.html>`__.
#. **Verify performance:** Check if the performance meets the desired criteria: `Perform analysis <../userguide/analysis.html>`__.
#. **Adjust Budgets if Necessary:** If the performance or costs do not align with your targets, adjust the budgets and then revisit the process starting from step 4. For adjusting budgets see: `Work with specifications <../userguide/specifications.html>`__, and `Work with parameters <../userguide/parameters.html>`__.
#. **Store Values:** If the performance and costs are satisfactory, store the parameter values in the design database. Refer to: `Work with specifications <../userguide/specifications.html>`__.
#. **Generate Documentation:** Create snippets for design documents in formats such as LaTeX, ReStructuredText, or HTML. See: `Create Reports <../userguide/reports.html>`__.
#. **Proceed:** Repeat the process for the next performance aspect(s), cost factor(s), and circuit parameter(s) of interest.

This structured approach helps streamline the design process and ensures that all performance and cost factors are systematically addressed. For more detailed information, check out `Structured Electronic Design <https://analog-electronics.tudelft.nl/>`_.

Design and documentation
========================

As described above, the primary focus of SLiCAP is to emphasize the motivations behind each design step, relating them to target specifications such as performance, costs, and operating environment. However, the development of SLiCAP is also based upon the idea of concurrent design and documentation. Throughout the design process, information is stored in a database, while documents present various perspectives on this data. These perspectives may include design motivations, production information, and other relevant aspects. 

.. image:: /img/colorCode.svg
