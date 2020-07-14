from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import os.path

class NewCurrentMeasure(Measurement):
   
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
        self.name = "new_current_vs_time_measure"

        self.ui_filename = sibling_path(__file__, "new_current_vs_time.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)
        self.settings.New('initial_gate_setting', unit = 'V', initial = 0)
        # self.settings.New('delay_gate_1', unit = 's', initial = 30)
        # self.settings.New('delay_gate_2', unit = 's', initial = 60)
        self.settings.New('time_between_readings', unit = 'ms', initial = 30)
        self.settings.New('approx_time_step', unit = 'ms', initial = 300)
        self.settings.New('total_measurement_time', unit = 's', initial = 120)
        self.settings.New('current_offset', unit = 'A', initial = 0)
        self.settings.New('software_averages', int, initial = 0)

        self.g_hw = self.app.hardware['keithley2400_sourcemeter1']
        self.ds_hw = self.app.hardware['keithley2400_sourcemeter2']

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        self.g_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_g_doubleSpinBox)
        self.ds_hw.settings.drain_bias.connect_to_widget(self.ui.drain_bias_doubleSpinBox)
        self.ds_hw.settings.autorange.connect_to_widget(self.ui.autorange_checkBox)
        self.ds_hw.settings.autozero.connect_to_widget(self.ui.autozero_comboBox)
        self.ds_hw.settings.manual_range.connect_to_widget(self.ui.manual_range_comboBox)
        self.ds_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_ds_doubleSpinBox)
        self.ds_hw.settings.NPLC.connect_to_widget(self.ui.nplc_doubleSpinBox)

        self.settings.initial_gate_setting.connect_to_widget(self.ui.initial_gate_setting_doubleSpinBox)
        self.settings.time_between_readings.connect_to_widget(self.ui.time_between_readings_doubleSpinBox)
        self.settings.approx_time_step.connect_to_widget(self.ui.approx_time_step_doubleSpinBox)
        self.settings.total_measurement_time.connect_to_widget(self.ui.total_measurement_time_doubleSpinBox)
        self.settings.current_offset.connect_to_widget(self.ui.current_offset_doubleSpinBox)
        
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


        
    # def update_display(self):
    #     if hasattr(self, 'ds_reading') and hasattr(self, 'g_reading'):
    #         if self.doing_return_sweep: #plot only return sweep data
    #             self.g_plot.plot(self.voltages[self.num_steps:], self.save_array[self.num_steps:, 1], pen = 'r', clear = True)
    #             self.ds_plot.plot(self.voltages[self.num_steps:], self.save_array[self.num_steps:, 3], pen = 'b', clear = True)


    def read_settings(self):
        self.g_source_mode = self.g_hw.settings['source_mode']
        self.g_current_compliance = self.g_hw.settings['current_compliance']
        self.g_voltage_compliance = self.g_hw.settings['voltage_compliance']

        self.ds_drain_bias = self.ds_hw.settings['drain_bias']
        self.ds_autorange = self.ds_hw.settings['autorange']
        self.ds_autozero = self.ds_hw.settings['autozero']
        self.ds_manual_range = self.ds_hw.settings['manual_range']
        self.ds_current_compliance = self.ds_hw.settings['current_compliance']
        self.ds_nplc = self.ds_hw.settings['NPLC']

        self.initial_gate_setting = self.settings['initial_gate_setting']
        # self.delay_gate1 = self.settings['delay_gate_1']
        # self.delay_gate2 = self.settings['delay_gate_2']
        self.time_between_readings = self.settings['time_between_readings']
        self.approx_time_step = self.settings['approx_time_step']
        self.total_measurement_time = self.settings['total_measurement_time']
        self.current_offset = self.settings['current_offset']
        # self.software_averages = self.settings['software_averages']
    
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
            self.g_device.measure_current()
        else:
            self.ds_device.measure_current(nplc = self.sweep_nplc)
            self.g_device.measure_current()


        self.num_measure = int(np.ceil(self.approx_time_step/self.time_between_readings))
        self.time_array = np.arange(start = 0, stop = self.approx_time_step *3, step = self.time_between_readings) #hardcoded
        self.save_array = np.zeros(shape=(self.time_array.shape[0], 3))
        self.save_array[:,0] = self.time_array
        #prepare hardware for read
        self.g_device.write_output_on()
        self.ds_device.write_output_on()

        self.ds_device.source_V(self.ds_drain_bias)
        self.v_g_array = [self.initial_gate_setting, 0, 0] #hardcoded
        time.sleep(self.first_bias_settle * .001)
        self.point_counter = 0



    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.

        Runs until measurement is interrupted. Data is continuously saved if checkbox checked.
        """
        for v_g in self.v_g_array:
            self.do_v_sweep(v_g)
        


    def do_sweep(self, v_g):
        '''
        Perform sweep.
        '''
        for i in self.num_measure:
            self.g_device.source_V(v_g)
            ds_current = self.read_currents()
            save_row = self.point_counter
            self.save_array[save_row, 1] = v_g
            self.save_array[save_row, 2] = self.ds_current
            self.point_counter += 1
            if self.interrupt_measurement_called:
                break


    def read_currents(self):
        '''
        Read both sourcemeters, taking software averages.
        '''
        # g_current_read = np.zeros(int(self.software_averages))
        # ds_current_read = np.zeros(int(self.software_averages))
        # for i in range(int(self.software_averages)):
        #     g_current_read[i] = self.g_device.read_I()
        #     ds_current_read[i] = self.ds_device.read_I()
        #     time.sleep(self.delay_between_averages * .001)
        # g_current_avg = np.mean(g_current_read)
        # ds_current_avg = np.mean(ds_current_read)
        # g_std = np.std(g_current_read, ddof = 1) #ddof - delta degrees of freedom. set to 1 for sample std
        # ds_std = np.std(ds_current_read, ddof = 1)
        # return [g_current_avg, g_std, ds_current_avg, ds_std]
        return self.ds_device.read_I()

    def post_run(self):
        '''
        Format and save measurement data.
        '''
        self.g_device.reset()
        self.ds_device.reset()

        self.check_filename('new_current_vs_time.txt')
        
        v_ds_info = 'V_DS =\t%g' % self.ds_drain_bias
        v_g_info = 'V_G = ' + str(self.v_g_array) 
        # avgs_info = 'Number of Averages =\t%g' % self.software_averages
        # width_info = 'Width/um=\t%g' % self.dimension_choice[self.dimension][0]
        # length_info = 'Length/um=\t%g' % self.dimension_choice[self.dimension][1]
        # thickness_info = 'Thickness/nm=\t%g' % self.thickness
        # info_footer = v_constant_info + "\n" + avgs_info + "\n" + width_info + "\n" + length_info + "\n" + thickness_info
        # info_header = 'V_%s\tI_G (A)\tI_G Error (A)\tI_DS (A)\tI_DS Error (A)' % (self.CONSTANT)
        info_footer = v_ds_info + '\n' + v_g_info
        info_header = 'Time (ms) \tV_G (V)\tI_DS(A)'
        # np.savetxt(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + append, self.save_array, fmt = '%.10f', 
            # header = info_header, footer = info_footer)
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