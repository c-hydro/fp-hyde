Flood PROOFS Modelling System
=============================

Welcome to the **Flood-PROOFS Modelling System** GitHub repository. This is a Modelling System supported by the Italian Civil Department (DPC) and is used for preventing and reducing hydrogeological risk.

Background
**********

**Flood-PROOFS** (Flood PRObabilistic Operative Forecasting System) is a system designed by CIMA Research Foundation to support decision makers during the operational phases of flood forecasting and monitoring. The goal is to protect the population and infrastructure from damage caused by intense precipitation events.

The Flood-PROOFS system manages the data flow deriving from various modelling tools developed by the CIMA Research Foundation to return a quantitative assessment of the effects that precipitation can have on the territory in terms of flow and probability to overcome the critical thresholds in the different basins. 

The system has been operating since 2008 at various Functional Centers (Autonomous Region of Valle d'Aosta and Marche) where it is used for the issue of hydro-meteorological warnings for civil protection purposes. At the technical offices of the Valle d'Aosta Water Company (CVA) it is instead useful to study and implement strategies to mitigate flood events or to secure facilities in the event of flooding.

Components
**********

The Flood-PROOFS forecasting chain consists in the following different parts, which are summarized as follows:

    • **Processing**: tools to organize input and output datasets written in python3 language usually named **Hydrological Data Engines [hyde]** package;
    • **Simulation**: tools to set and run Hydrological Model Continuum (HMC) written both in python3 and fortran programming language usually named **Hydrological Model Continuum [hmc]** package;
    • **Publishing and Visualization**: tools to control, view and analyze results written both in python3 and R programming language usually named as **Hydrological Analysis tools [hat]** package;
    • **Labs**: laboratories for running components of the modelling system, for trainings and educational use;
    • **Utilities**: common functionality required by the previous components.

All codes and datasets are freely available and users can be get them from our github repository [1_].

Prerequisites
*************

In order to use the Flood-PROOFS forecasting chain, users are strongly raccomanted to control if the following characteristics, libraries and packages are available and correctly installed on their machine.

Usually, Flood-PROOFS libraries are installed on **Linux Debian/Ubuntu 64bit** environment and all libraries, packages and applications must be compilled and/or installed in according with this operative system.

All codes, subroutines and scripts are developed using both **Python** (version 3 and greater) [2_] and **Fortran** (version 2003 and greater) [3_]. QGIS geographic information system (version 2.18 and greater) [4_] is used to develop tools to organize, create and control static and dynamic datasets. R (version 3.4.4 and greater) [5_] is used to perform statistical analysis.

The libraries and the packages are mainly divided in four categories:

    • python3 packages and applications;
    • R packages and applications;
    • fortran libraries;
    • other software and applications (Jupyter Notebook, QGIS, Panoply, cdo, ncview ...).

The section for installing all needed libraries and environments is usually named **fp-envs** and the users can find it in Flood-PROOFS
modelling system repository hosted by GitHub [1_].

Python3 libraries
-----------------

The python3 standard library is not sufficient to correctly install all Flood-PROOFS applications; for this reason some extra libraries are needed to guarantee all functionalities. 
To install all python3 libraries a bash script named **setup_fp_env_python.sh** is provided [6_]; basically, the script calls a **miniconda** [7_] installation that allow to get all needed libraries and install them into “$HOME/user/fp_libs_python/” folder. During the installation, a virtual environment named “fp_env_python” is created too.
Once all libraries are correctly installed and configurated, to activate “fp_env_python” by command-line is necessary to execute the following:

.. code-block:: bash
    
   >> export PATH="$HOME/fp_libs_python/bin:$PATH"
   >> source activate fp_env_python

By default, the **fp_env_python** environment is shown in parentheses () or brackets [] at the beginning of your command prompt:

.. code-block:: bash

   (fp_env_python) >> 

Activating the virtual enviroment permits to use a correct configuration andall applications and scripts of Flood-PROOFS forecasting chain will work properly.

Fortran libraries
-----------------

Hydrological model Continuum needs netcdf4 library to read input provided by other preprocessing tools and to write output for external applications (such as Panoply, cdo, ncview ...).
To set and compile netcdf4 library a bash script named **setup_fp_env_system.sh** is provided. 
Script downloads **zlib** [8_], **hdf5** [9_] and **netcdf4** [10_] libraries from their repositories; after downloading source compressed archives, script creates a folder in “$HOME/user/fp_libs_system/” where all libraries will be compilled and installed. During the installation, a environment file named “fp_env_system” is created for saving LD_LIBRARY_PATH (for native code libraries) and PATH (for executables) references of installed libraries.

HMC libraries
-------------
After preparing all necessary libraries and environmental settings, source files of HMC must be compiled to run properly [11_]; usually, sources are compiled using **GNU compilers** (such as gcc and gfortran) that have to be installed on user’s machine. To compile and optimize HMC codes a bash file named **setup_fp_env_hmc.sh** is provided. Using this setup file, user will have to answer some questions about how to compile HMC codes.
Usually, to build Continuum for production use, options have to set as follows:

    • set compiler type [1] for using GNU/GFortran compiler;
    • set optimization option [2] for using production mode; 
    • set profiler option [2] for skipping profiling used to control model performances;
    • set NetCDF4 library [1] for using NetCDF4 input and output files format.


Potential Users
***************
The Flood-PROOFS Modelling System has been released to enable different applications (for example local/regional scenario assessment) and further development by external users.

Potential users are anticipated to predominately be interested in the ability to run the system with local data (including scenario modelling) and to modify the system with new capabilities. The potential collaborators have expressed a range of potential goals for their use of the modelling system, including performing comparisons with existing models, tailoring the hydrological performance to specific land uses and cropping types.

Broadly speaking, there are four potential user categories of the FloodPROOFS modelling system:

    • **Data user**: who accessing the model outputs for using them in their analysis.
    • **Case study user**: who work to evaluate his/her case using data over a selected time period.
    • **Applying users**: who would primarily be interested in applying the current model to a region of interest using localised and/or scenario data where available.
    • **Contributor users**: who will extend the capabilities of the model with new research and coding (modify the system with new capabilities)

It is expected that the majority of early adopters of the FloodPROOFS modelling system will be Applying users looking to apply the system with local data/scenarios, with more Contributor users adopting the system as it becomes well known and established.

Contribute and Guidelines
*************************

We are happy if you want to contribute. Please raise an issue explaining what is missing or if you find a bug. We will also gladly accept pull requests against our master branch for new features or bug fixes.

If you want to contribute please follow these steps:

    • fork the one of the Flood-PROOFS repositories to your account;
    • clone the repository, make sure you use "git clone --recursive" to also get the test data repository;
    • make a new feature branch from the repository master branch;
    • add your feature;
    • please include tests for your contributions in one of the test directories;
    • submit a pull request to our master branch.

Authors
*******

All authors involved in the library development for the Flood-PROOFS modelling system are reported in this authors_ file.

License
*******

By accessing or using the Flood-PROOFS modelling system, code, data or documentation, you agree to be bound by the FloodPROOFS license available. See the license_ for details. 

Changelog
*********

All notable changes and bugs fixing to this project will be documented in this changelog_ file.

References
**********
| [1_] CIMA Hydrology and Hydraulics GitHub Repository
| [2_] Python programming language
| [3_] Fortran programming language
| [4_] QGIS project
| [5_] R programming language
| [6_] FloodPROOFS virtual environment tools
| [7_] Conda environment manager
| [8_] ZLIB compression library
| [9_] HDF5 data software library 
| [10_] NetCDF4 data software library 
| [11_] Hydrological Model Continuum codes

.. _1: https://github.com/c-hydro
.. _2: https://www.python.org/
.. _3: https://en.wikipedia.org/wiki/Fortran
.. _4: https://qgis.org/en/site/
.. _5: https://www.r-project.org/
.. _6: https://github.com/c-hydro/fp-env
.. _7: https://conda.io/miniconda.html
.. _8: https://zlib.net/
.. _9: https://www.hdfgroup.org/solutions/hdf5/
.. _10: https://www.unidata.ucar.edu/
.. _11: https://github.com/c-hydro/hmc-dev
.. _license: LICENSE.rst
.. _changelog: CHANGELOG.rst
.. _authors: AUTHORS.rst
