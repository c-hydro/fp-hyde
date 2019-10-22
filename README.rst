============
Hydrological Data Engines (HyDE)
============

summary ...

Citation
========

If you use the software in a publication then please cite it using the DOI:


Supported Products
==================

This gives a short overview over the supported products. 


Model Run
---------

General example usage: 
python HMC_Model_RUN_Manager.py -settingfile settingsfile.config -logfile logfile.config -time yyyymmddHHMM

Example:
python HMC_Model_RUN_Manager.py
-settingfile /home/fabio/Desktop/PyCharm_Workspace_Python2/HMC-2.0.6/config/config_algorithms/hmc_model_run-manager_algorithm_local_history_ws-db.config
-logfile /home/fabio/Desktop/PyCharm_Workspace_Python2/HMC-2.0.6/config/config_logs/hmc_model_run-manager_logging_local_history_ws-db.config
-time 201610200000

Libraries
~~~~~~~~~

References external libraries:
numpy-scipy:        <http://www.scipy.org/SciPy>
python-netcdf:      <http://netcdf4-python.googlecode.com/svn/trunk/docs/netCDF4-module.html>
python-gdal:        <https://pypi.python.org/pypi/GDAL/>



Installation
============

The packages you have to install depend on the features you want to use....


Contribute
==========

We are happy if you want to contribute. Please raise an issue explaining what is missing or if you find a bug. We will also gladly accept pull requests against our master branch for new features or bug fixes.

Development setup
-----------------



Guidelines
----------

If you want to contribute please follow these steps:

- Fork the HyDE repository to your account
- Clone the repository, make sure you use ``git clone --recursive`` to also get the test data repository.
- make a new feature branch from the ascat master branch
- Add your feature
- Please include tests for your contributions in one of the test directories. We use py.test so a simple function called test_my_feature is enough
- submit a pull request to our master branch

Note
====

This project has been set up using PyScaffold 2.5.6. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
