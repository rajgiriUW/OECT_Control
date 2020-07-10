from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import os.path

from .general_curve_measure import GeneralCurveMeasure

class TransferCurveMeasure(GeneralCurveMeasure):
    SWEEP = "G"
    CONSTANT = "DS"