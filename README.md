Python scripts for displaying EEG data.

vizEEG run instructions

In order to run vizEEG it is necessary to install following packages:
PyQt 4.8 and higher
numpy
scipy
pyqtgraph (developer version from github, or newer than 0.9.8 version)
h5py

Only argument that is mandatory while running the application is
a path to the file, if the file does not contain data-sets according
to the standard structure, it is possible to define them in marked
parameters, see python vizEEG.py -h.

Please, do not run minmax creation on testing data provided when prompted,
they are too small for minmax to have a meaning. 
