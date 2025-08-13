==================
SLiCAP Version 4.0
==================

.. image:: /img/colorCode.svg

- SLiCAP is an acronym for: **S** ymbolic **Li** near **C** ircuit **A** nalysis **P** rogram
- SliCAP is a tool for **algorithmic analog design automation**
- SLiCAP is intended for setting up and solving **design equations** of electronic circuits and **integrating design and documentation**
- SLiCAP is a an **open source** application written in Python, originally created by `Anton J.M. Montagne <https://montagne.nl>`_
- SLiCAP is part of the tool set for teaching `Structured Electronic Design <https://analog-electronics.tudelft.nl>`_ at the Delft University of Technology

SLiCAP Version 4.0 is distributed under the `MIT license <https://opensource.org/license/mit>`_

.. image:: /img/colorCode.svg

**Analog design** often starts with an application description comprising target requirements for the functionality, the physical appearance, the performance quality, and the cost factors of the desired product. The analog circuit designer somehow has to convert this into a chip or a PCA (printed Circuit board Assembly) with a test plan that makes it possible to verify performance to requirements.

**Circuit simulators** and PCB or chip layout software are commonly at the disposal of analog design engineers to help them fullfill their tasks. Circuit simulators (such as SPICE), however, can only perform numeric design verification. Hence, the topology and the devices with their geometries and operating conditions need to be designed before simulation. 

**The question** pops up how these design decisions have been made and in which way the selected topology, component values, geometries and operating conditions link to the original requirements. Moreover, can we be sure that the requirements can be met with the selected topology and with the components and their assigned geometries and operating conditions? 

**Experienced designers** find their way intuitively, often resorting to familiar topologies and manual calculations with overly simplified models. The use of a straightforward design method with a supporting design tool and adequate models, however, will largely improve the motivation, the quality, and the tracebility of design decisions. As a matter of fact, such a tool is indispensible for first-time-right design. In addition, it will speed up knowledge building quickly turning novices into analog design experts.

**Structured Electronics Design**, as taught at the `TU Delft <https://analog-electronics.tudelft.nl>`_, presents a design method based on systems engineering, device physics, signal processing, control theory and last but not least: on network theory. It presents a top-down hierarchical design method that accounts for bottom-up show-stoppers.

**SLiCAP**, is a mixed symbolic/numeric network simulator that interfaces with a design database, integrates with a documentation system, and supports the advocated design method. It fills the gap between the initial specification and numeric circuit verification. With SLiCAP, designers easily find valid ranges for component values, geometry and operating conditions of devices, with a clear relation to the performance and/or cost budgets from the initial specifications.

.. toctree::
    :maxdepth: 2

    SLiCAPreleaseNotes
    SLiCAPwhy
    SLiCAPhow
    SLiCAPcontributions
    
.. image:: /img/colorCode.svg
   
   

