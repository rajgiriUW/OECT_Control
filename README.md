# OECT_Control
Python Implementation for Organic Electrochemical Transistor Measurement

## Requirements
- scopefoundry
- numpy
- pyqt5
- qtpy
- h5py
- pyqtgraph
- pyvisa 
- qtconsole
- ipython
- fbs

## How to Use
From releases: download the .zip file and run "OECT_Control.exe", or download the .exe installer. 
If you used the installer to install the application, the application must be run as administrator. Otherwise, a Permission Error will occur.

## Directly running the app with FBS and making changes
Refer to https://build-system.fman.io/manual/ for more info. 

### Setting up FBS and its dependencies in a new environment
1. Create a new virtual environment and activate it by running the following commands, replacing "envname" with what you want to name the new environment.
```
conda create -n envname python=3.6 anaconda
conda activate envname
```
The specified Python version should be 3.5 or 3.6. Newer versions of Python are not yet supported by FBS.

2. Install FBS and PyQt with
```
pip install fbs PyQt5==5.9.2
```

3. Install NSIS from https://nsis.sourceforge.io/Download and add the NSIS path to your Windows PATH environment variable, if it is not already set. (Search "environment variable" in the Windows start menu)

### Getting the OECT Control application running

1. Install OECT dependencies with
```
pip install -r requirements/base.txt
```

2. Navigate to the directory containing the "src" folder for the app.

3. To test the app, run
```
fbs run
```

### Important notes about making changes to the application
- The build.json file, located in src/build/settings, is crucial for getting the FBS application to compile and build correctly.
  -  ```"hidden_imports": ["ipykernel.datapub", "ipython", "qtconsole", "pyvisa"]``` MUST be present in the build.json file to ensure it is properly packaged.
  - The application file's main method needs to create an ApplicationContext for FBS to run.
  - The main application file is usually located in the src/main/python directory. However, if you need the file in another directory, you may specify it in the build.json file's "main_module" property.
- The rest of the modules and files needed to run the main app MUST be in the src/main/resources/base directory.
  - The ScopeFoundry folder in this directory is needed for FBS to pull the base app UI file.

### Packaging the application
```
fbs freeze
```
Add the --debug flag to the command to get more details on the build process as it happens.
You can create an installer for the app with
```
fbs installer
```
