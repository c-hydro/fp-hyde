Overview
================================

The **Hydrological Data Engines**, commonly named **HyDE**, is a python package part of **FloodPROOFS Modelling System**. The FloodPROODS framework is a modelling system designed to assist decision makers during the operational phases of flood forecasting, nowcasting, mitigation and monitoring in various-sized catchments. 

.. figure:: img/hyde_generic/CVA-200.jpg
    :height: 600px
    :width: 1000px
    :scale: 50 %
    :alt: example of lake and dam in Valle d'Aosta region.
    :align: center

The system is operational in real time in different basins on the whole Italian territory for the National Civil Protection Department and in some basins of Bolivia, Albania and Lebanon. It is also used for water management purposed by Italian hydro-power companies (Compagnia Valdostana delle Acque, CVA, ERG Power Generation). 

Components
**********

In the Flood-PROOFS forecasting chain, the data dynamic processing part is performed by using the HyDE package [1_]. Written in python3 language, HyDE manages all aspects concerning the production of the datasets suitable for the FloodPROOFS modelling system. This package is able to read data both from various types of information (weather stations, satellite, nwp ... ) and in different formats (such as GRIB, BUFR, hdf, hdf5, netcdf4 ...); once getting and reading the source data, HyDE converts them from their original struture to formats commonly used by FloodPROOFS modelling system (for instance netCDF4, JSON and so on) and by other freely available applications (such as cdo, panoply, ncview, MET …).

For adapting datasets to the requested format, HyDE provides a checking of names, units and physics limits of all variables used by the FloodPROOFS modelling system. The reprojection or the interpolation of datasets, where they are needed, are performed by HyDE package too.

Particularly, the HyDE library is organized in different parts, which are summarized as follows:
    • **Applications**: tools to configure procedures able to processing different type of data, usually written in python3 programming language and available in the apps folder;
    • **Executables**: tools and utilities to run procedures, to download datasets or to interface HyDE package with different environments, usually written in bash or python3 programming languages and available in the bin folder;
    • **Docs**: documents to describe HyDE package, applications and executables, usually written in reStructuredText (rst) and available in the docs folder;
    • **Codes**: generic and specific classes and methods used by the applications, to perform processing data and to save results in the formats commonly used in FloodPROOFs modelling system, are written in python3 and available in the src folder;
    • **Utilities**: common functionality required by the previous components.

The structure of the package is reported above:

::

    hyde-master
    ├── apps
    ├── bin
    ├── docs
    ├── src          
    │   ├── common
    │   └── hyde
    ├── test          
    ├── AUTHORS.rst
    ├── CHANGELOG.rst          
    ├── LICENSE.rst
    └── README.rst

All codes and datasets are freely available and users can be get them from our github repository [1_].

Prerequisites
*************

In order to use the HyDE, users are strongly raccomanted to control if the following characteristics, libraries and packages are available and correctly installed on their machine.

Usually, HyDE is installed on **Linux Debian/Ubuntu 64bit** environment and all dependencies must be installed in according with this operative system. 

All codes, subroutines and scripts are developed using both **Python** (version 3 and greater) [2_] and **GNU Bash** [3_]. QGIS geographic information system (version 2.18 and greater) [4_] is used to develop tools to organize, create and control static and dynamic datasets.

The libraries and the packages are mainly divided in three categories:

    • python3 packages and applications;
    • GNU Bash applications;
    • other software and applications (Jupyter Notebook, Panoply, cdo, nco, ncview ...)

Python3 libraries
-----------------

The python3 standard library is not sufficient to correctly install all HyDE applications; for this reason some extra libraries are needed to guarantee all functionalities. 
To install all python3 libraries a bash script named “setup_fp_env_python.sh” is provided [5_]; basically, the script calls a **miniconda** [6_] installation that allow to get all needed libraries and install them into “$HOME/user/fp_libs_python/” folder. During the installation, a virtual environment named “fp_env_python” is created too.

The users have to clone the github repository:

.. code-block:: bash
    
    >> git clone git@github.com:c-hydro/fp-envs.git
    
and run the following bash script:        

.. code-block:: bash
    
    >> ./setup_fp_env_python.sh
    |[take a moment ... ]

Once all libraries are correctly installed and configurated, to activate “fp_env_python” by command-line is necessary to execute the following:

.. code-block:: bash

    >> export PATH="$HOME/fp_libs_python/bin:$PATH"
    >> source activate fp_env_python

By default, the “fp_env_python” environment is shown in parentheses () or brackets [] at the beginning of your command prompt:

.. code-block:: bash

   (fp_env_python) >> 

Activating the virtual enviroment permits to use a correct configuration and all applications of HyDE package will work properly.

Other software and applications
-------------------------------

As previously said, to perform analysis or check results, users can use some external and freely available softwares and applications. 

Some of these are reported in the following list:

 * PanoplyJ Data Viewer [7_]
 * CDO - Climate Data Operators [8_]
 * NCO - NetCDF Operators [9_]
 * NCView: a netCDF visual browser [10_]
 * Jupyter notebook web application [11_] 

More information is available on the homepage of the different software. 

Potential Users
***************

The HyDE package has been released to enable different applications (for example local/regional scenario assessment) and further development by external users.

Potential users are anticipated to predominately be interested in the ability to run the system with local data (including scenario modelling) and to modify the system with new capabilities. The potential collaborators have expressed a range of potential goals for their use of the modelling system, including performing comparisons with existing models, tailoring the hydrological performance to specific land uses and cropping types.

Broadly speaking, there are four potential user categories of the FloodPROOFS modelling system:

    • **Data user**: who accessing the model outputs through the Bureau's website.
    • **Case study user**: who work to evaluate his/her case using data over a selected time period.
    • **Applying users**: who would primarily be interested in applying the current model to a region of interest using localised and/or scenario data where available.
    • **Contributor users**: who will extend the capabilities of the model with new research and coding (modify the system with new capabilities)

It is expected that the majority of early adopters of the HyDE package will be Applying users looking to apply the system with local data/scenarios, with more Contributor users adopting the system as it becomes well known and established.

Contribute
**********

We are happy if you want to contribute. Please raise an issue explaining what is missing or if you find a bug. We will also gladly accept pull requests against our master branch for new features or bug fixes.

Development setup
-----------------

For Development we also recommend a "conda" environment. You can create one including test dependencies and debugger by running 

.. code-block:: bash

   >> conda env create -n fp_env_dev -c <list_of_packages>

or alternatively using a file:

.. code-block:: bash

   >> "conda env create -n fp_env_dev  -f <file_of_packages.yml> 

This will create a new "fp_env_dev" environment which you can activate by using "source activate fp_env_dev".

Guidelines
----------

If you want to contribute please follow these steps:
    • Fork the HyDE package to your account
    • Clone the repository, make sure you use "git clone --recursive" to also get the test data repository.
    • make a new feature branch from the repository master branch
    • Add your feature
    • Please include tests for your contributions in one of the test directories. We use py.test so a simple function called "test_my_feature" is enough
    • submit a pull request to our master branch


Reference
*********

| [1_] CIMA Hydrology and Hydraulics GitHub Repository
| [2_] Python programming language
| [3_] GNU Bash
| [4_] QGIS project
| [5_] FloodPROOFS virtual environment tools
| [6_] Conda environment manager
| [7_] Panoply netCDF, HDF and GRIB Data Viewer
| [8_] CDO - Climate Data Operators
| [9_] NCO - NetCDF Operators
| [10_] NCView: a netCDF visual browser
| [11_] Jupyter notebook web application
| [12_] Cron jobs scheduler

.. _1: https://github.com/c-hydro
.. _2: https://www.python.org/
.. _3: https://www.gnu.org/software/bash/
.. _4: https://qgis.org/en/site/
.. _5: https://github.com/c-hydro/fp-env
.. _6: https://conda.io/miniconda.html
.. _7: https://www.giss.nasa.gov/tools/panoply/
.. _8: https://code.mpimet.mpg.de/projects/cdo
.. _9: http://nco.sourceforge.net/
.. _10: http://meteora.ucsd.edu/~pierce/ncview_home_page.html
.. _11: https://jupyter.org/
.. _12: https://en.wikipedia.org/wiki/Cron


