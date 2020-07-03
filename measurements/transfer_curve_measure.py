from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import seabreeze.spectrometers as sb
import os.path

class OutputCurveMeasure(Measurement):
        
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        # self.name = "output_curve_measure"
        # self.ui_filename = sibling_path(__file__, "spec_plot.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        # self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.dimension_choice = ['4000 x 20', '2000 x 20', '1000 x 20', '800 x 20', '400 x 20', '200 x 20', '100 x 20']
        self.V_DS_start = self.settings.New('V_DS_start', unit = 'V', si = True, initial = -0.7)
        self.V_DS_finish = self.settings.New('V_DS__finish', unit = 'V', si = True, initial = 3)
        self.V_DS_step_size = self.settings.New('V_DS_step_size', unit = 'V', si = True, initial = 0.1)
        self.preread_delay = self.settings.New('preread_delay', unit = 'ms', si = True, initial = 5000)
        self.delay_between_averages = self.settings.New('delay_between_averages', unit = 'ms', si = True, initial = 200)
        self.software_averages = self.settings.New('software_averages', initial = 5)
        self.first_bias_settle = self.settings.New('first_bias_settle', unit = 'ms', si = True, initial = 2000)
        self.dimension = self.settings.New('dimension', choices = self.dimension_choice.keys(), initial = '4000 x 20')



        # Define how often to update display during a run
        self.display_update_period = 0.1 
        


        self.save_array = np.zeros(shape=(2048,2))
        self.point_counter = 0
        
        # Convenient reference to the hardware used in the measurement
        self.k1_hw = self.app.hardware['keithley2400_sourcemeter1']
        self.k2_hw = self.app.hardware['keithley2400_sourcemeter2']
        self.k1 = self.k1_hw.k1
        self.k2 = self.k2_hw.k2


    # def setup_figure(self):
    #     """
    #     Runs once during App initialization, after setup()
    #     This is the place to make all graphical interface initializations,
    #     build plots, etc.
    #     """
        
    #     # connect ui widgets to measurement/hardware settings or functions
    #     self.ui.start_pushButton.clicked.connect(self.start)
    #     self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
    #     self.ui.saveSingle_pushButton.clicked.connect(self.save_single_spec)
        
    #     self.settings.save_every_spec.connect_to_widget(self.ui.save_every_spec_checkBox)
    #     self.settings.scans_to_avg.connect_to_widget(self.ui.scans_to_avg_spinBox)
    #     self.spec_hw.settings.correct_dark_counts.connect_to_widget(self.ui.correct_dark_counts_checkBox)
    #     self.spec_hw.settings.intg_time.connect_to_widget(self.ui.intg_time_spinBox)

    #     # Set up pyqtgraph graph_layout in the UI
    #     self.graph_layout=pg.GraphicsLayoutWidget()
    #     self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

    #     # # Create PlotItem object (a set of axes)  
    #     self.plot = self.graph_layout.addPlot(title="Spectrometer Readout Plot")
    #     self.plot.setLabel('left', 'Intensity', unit='a.u.')
    #     self.plot.setLabel('bottom', 'Wavelength', unit='nm')
        
    #     # # Create PlotDataItem object ( a scatter plot on the axes )
    #     self.optimize_plot_line = self.plot.plot([0])

    # def update_display(self):
    #     """
    #     Displays (plots) the wavelengths on x and intensities on y.
    #     This function runs repeatedly and automatically during the measurement run.
    #     its update frequency is defined by self.display_update_period
    #     """
    #     if hasattr(self, 'spec') and hasattr(self, 'y'):
    #         self.plot.plot(self.spec.wavelengths(), self.y, pen='r', clear=True)
    #         pg.QtGui.QApplication.processEvents()

    def pre_run(self):
        self.num_steps = np.abs(int(np.ceil((self.V_DS_start - self.V_DS_finish)/self.V_DS_step_size)))
        self.k1.write_output_on()
        self.k1.measure_current()
        self.k2.measure_current()
        self.source_voltage_set_to = self.V_DS_start
        self.check_filename(".txt")
        time.sleep(self.first_bias_settle)

    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.

        Runs until measurement is interrupted. Data is continuously saved if checkbox checked.
        """
        for i in range(self.num_steps):
            while not self.interrupt_measurement_called:
                if i != 0:
                    self.source_voltage_set_to += self.V_DS_step_size
                self.k1.source_V(self.source_voltage_set_to)
                time.sleep(self.preread_delay)
                self.read_currents()
                if self.interrupt_measurement_called: break
            if self.interrupt_measurement_called: break


    def read_currents(self):
        '''
        Read spectrometer according to settings and update self.y (intensities array)
        '''
        if hasattr(self, 'k1') and hasattr(self, 'k2'):
            k1_current_read = np.zeros(self.software_averages)
            k2_current_read = np.zeros(self.software_averages)
            for i in range(self.software_averages):
                k1_current_read[i] = self.k1.read_I()
                k2_current_read[i] = self.k2.read_I()
                time.sleep(self.delay_between_averages)
            k1_current_avg = np.mean(k1_current_read)
            k2_current_avg = np.mean(k2_current_read)

    def check_filename(self, append):
        '''
        If no sample name given or duplicate sample name given, fix the problem by appending a unique number.
        append -- string to add to sample name (including file extension)
        '''
        samplename = self.app.settings['sample']
        filename = samplename + append
        directory = self.app.settings['save_dir']
        if samplename == "":
            self.app.settings['sample'] = int(time.time())
        if (os.path.exists(directory+"/"+filename)):
            self.app.settings['sample'] = samplename + str(int(time.time()))