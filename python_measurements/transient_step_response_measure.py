from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import os.path

class TransientStepResponseMeasure(Measurement):
   
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
        self.name = "TransientStepResponse"

        self.ui_filename = sibling_path(__file__, "new_current_vs_time.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)
        self.settings.New('drain_bias', unit = 'V', initial = -.6)
        self.settings.New('first_bias_settle', unit = 'ms', initial = 2000)
        self.settings.New('initial_gate_setting', unit = 'V', initial = 0)
        self.settings.New('delay_gate', unit = 's', initial = 30)
        self.settings.New('setpoint', unit = 'V', initial = .5)
        # self.settings.New('delay_gate_2', unit = 's', initial = 60)
        self.settings.New('software_averages', int, initial = 10)
        self.settings.New('delay_between_averages', unit = 'ms', initial = 300)
        self.settings.New('total_measurement_time', unit = 's', initial = 120)

        self.g_hw = self.app.hardware['keithley2400_sourcemeter1']
        self.ds_hw = self.app.hardware['keithley2400_sourcemeter2']

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        self.g_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_g_doubleSpinBox)
        self.g_hw.settings.voltage_compliance.connect_to_widget(self.ui.voltage_compliance_g_doubleSpinBox)
        self.ds_hw.settings.autorange.connect_to_widget(self.ui.autorange_checkBox)
        self.ds_hw.settings.autozero.connect_to_widget(self.ui.autozero_comboBox)
        self.ds_hw.settings.manual_range.connect_to_widget(self.ui.manual_range_comboBox)
        self.ds_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_ds_doubleSpinBox)
        self.ds_hw.settings.NPLC.connect_to_widget(self.ui.nplc_doubleSpinBox)

        self.settings.drain_bias.connect_to_widget(self.ui.drain_bias_doubleSpinBox)
        self.settings.first_bias_settle.connect_to_widget(self.ui.first_bias_settle_doubleSpinBox)
        self.settings.initial_gate_setting.connect_to_widget(self.ui.initial_gate_setting_doubleSpinBox)
        self.settings.delay_gate.connect_to_widget(self.ui.delay_gate_doubleSpinBox)
        self.settings.setpoint.connect_to_widget(self.ui.setpoint_doubleSpinBox)
        self.settings.software_averages.connect_to_widget(self.ui.software_averages_doubleSpinBox)
        self.settings.delay_between_averages.connect_to_widget(self.ui.delay_between_averages_doubleSpinBox)
        self.settings.total_measurement_time.connect_to_widget(self.ui.total_measurement_time_doubleSpinBox)
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        # # Set up pyqtgraph graph_layout in the UI
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.graph_container.layout().addWidget(self.graph_layout)

        # # # Create PlotItem object (a set of axes)  
        self.plot = self.graph_layout.addPlot(title="Current vs. Time")
        self.plot.setLabel('bottom', 'Time (ms)')
        self.plot.setLabel('left', 'I_DS')
        
    def update_display(self):
            self.plot.plot(self.time_array, self.save_array[:,2], pen = 'r', clear = True)

    def read_settings(self):
        self.g_source_mode = self.g_hw.settings['source_mode']
        self.g_current_compliance = self.g_hw.settings['current_compliance']
        self.g_voltage_compliance = self.g_hw.settings['voltage_compliance']

        self.ds_autorange = self.ds_hw.settings['autorange']
        self.ds_autozero = self.ds_hw.settings['autozero']
        self.ds_manual_range = self.ds_hw.settings['manual_range']
        self.ds_current_compliance = self.ds_hw.settings['current_compliance']
        self.ds_nplc = self.ds_hw.settings['NPLC']

        self.drain_bias = self.settings['drain_bias']
        self.first_bias_settle = self.settings['first_bias_settle']
        self.initial_gate_setting = self.settings['initial_gate_setting']
        self.delay_gate = self.settings['delay_gate']
        self.setpoint = self.settings['setpoint']
        self.software_averages = self.settings['software_averages']
        self.delay_between_averages = self.settings['delay_between_averages']
        self.total_measurement_time = self.settings['total_measurement_time']
    
    def pre_run(self):
        self.check_filename(".txt")


        #these refer to the same devices as constant and sweep devices, but are convenient when we want to reference
        #to device by which terminals it corresponds to - makes things easier for measurement and saving
        self.g_device = self.g_hw.keithley
        self.ds_device = self.ds_hw.keithley
        self.g_device.reset()
        self.ds_device.reset()
        self.read_settings()

        #configure keithleys
        if self.g_source_mode == 'VOLT':
            self.g_device.write_current_compliance(self.g_current_compliance)
        else:
            self.g_device.write_voltage_compliance(self.g_voltage_compliance)

        self.ds_device.write_autozero(self.ds_autozero)
        self.ds_device.write_current_compliance(self.ds_current_compliance)
        if not self.ds_autorange:
            self.ds_device.measure_current(nplc = self.ds_nplc, current = self.ds_manual_range, auto_range = False)
        else:
            self.ds_device.measure_current(nplc = self.ds_nplc)

        self.time_for_avg = self.software_averages * self.delay_between_averages
        self.time_array = np.arange(start = 0, stop = self.total_measurement_time * 1000 + self.time_for_avg, step = self.time_for_avg)
        self.num_initial = int((self.delay_gate * 1000)/self.time_for_avg)
        self.num_setpoint = int(((self.total_measurement_time - self.delay_gate) * 1000)/self.time_for_avg)


        self.save_array = np.zeros(shape=(self.time_array.shape[0], 4))
        self.save_array[:,0] = self.time_array
        self.save_array[:self.num_initial, 1] = self.initial_gate_setting
        self.save_array[self.num_initial:, 1] = self.setpoint
        #prepare hardware for read
        self.g_device.write_output_on()
        self.ds_device.write_output_on()

        self.ds_device.source_V(self.drain_bias)
        time.sleep(self.first_bias_settle * .001)

    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.

        Runs until measurement is interrupted. Data is continuously saved if checkbox checked.
        """
        for i in range(self.num_initial):
            ds_reading = self.read_currents()
            self.save_array[i, 2] = ds_reading[0]
            self.save_array[i, 3] = ds_reading[1]
        for i in range(self.num_setpoint + 1):
            ds_reading = self.read_currents()
            self.save_array[i + self.num_initial, 2] = ds_reading[0]
            self.save_array[i + self.num_initial, 3] = ds_reading[1]

    def read_currents(self):
        '''
        Read both sourcemeters, taking software averages.
        '''
        ds_current_read = np.zeros(int(self.software_averages))
        for i in range(int(self.software_averages)):
            ds_current_read[i] = self.ds_device.read_I()
            time.sleep(self.delay_between_averages * .001)
        ds_current_avg = np.mean(ds_current_read)
        ds_std = np.std(ds_current_read, ddof = 1)
        return [ds_current_avg, ds_std]

    def post_run(self):
        '''
        Format and save measurement data.
        '''
        self.g_device.reset()
        self.ds_device.reset()
        append = '_new_current_vs_time.txt'
        self.check_filename(append)
        
        v_ds_info = 'V_DS =\t%g' % self.drain_bias
        info_footer = v_ds_info
        info_header = 'Time (ms)\tV_G (V)\tI_DS(A)\tI_DS error (A)'
        np.savetxt(self.app.settings['save_dir'] + "/" + self.app.settings['sample'] + append, self.save_array, fmt = '%.10f',
            header = info_header, footer = info_footer)

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