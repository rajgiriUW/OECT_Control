from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import os.path

class GeneralCurveMeasure(Measurement):
    #class variables determining vhich device's voltage will go through a sweep and which will be constant
    #set these values in specific measurements
    SWEEP = ""
    CONSTANT = ""

    #class variable determining numbering of measurement output file. useful in auto_measure for multiple outputs and transfers 
    READ_NUMBER = 0

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
        if "SWEEP" == "DS": self.name = "output_curve_measure"
        elif "SWEEP" == "G": self.name = "transfer_curve_measure"
        self.ui_filename = sibling_path(__file__, "general_curve.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        self.create_settings()
        self.dimension_choice = {'4000 x 20': [4000, 20], '2000 x 20': [2000, 20], '1000 x 20': [1000, 20], '800 x 20': [800, 20], 
            '400 x 20': [400, 20], '200 x 20': [200, 20], '100 x 20': [100, 20]}
        self.settings.New('dimension', str, choices = self.dimension_choice.keys(), initial = '4000 x 20')
        self.settings.New('thickness', unit = "nm", initial = 50)

    def create_settings(self):
                # Measurement Specific Settings
      # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to   the Microscope user interface

        self.settings.New('V_%s_start' % self.SWEEP, unit = 'V', si = True, initial = -0.7)
        self.settings.New('V_%s_finish' % self.SWEEP, unit = 'V', si = True, initial = 3)
        self.settings.New('V_%s_step_size' % self.SWEEP, unit = 'V', si = True, initial = 0.1)
        self.settings.New('%s_sweep_preread_delay' % self.SWEEP, unit = 'ms', si = True, initial = 5000)
        self.settings.New('%s_sweep_delay_between_averages' % self.SWEEP, unit = 'ms', si = True, initial = 200)
        self.settings.New('%s_sweep_software_averages' % self.SWEEP, int, initial = 5, vmin = 1)
        self.settings.New('%s_sweep_first_bias_settle' % self.SWEEP, unit = 'ms', si = True, initial = 2000)
        
        self.settings.New('%s_sweep_return_sweep' % self.SWEEP, bool, initial = True)
        self.settings.New('V_%s' % self.CONSTANT, unit = 'V', si = True, initial = 0.1)

        # Define how often to update display during a run
        self.display_update_period = 0.1 
        
        # Convenient reference to the hardware used in the measurement
        self.g_hw = self.app.hardware['keithley2400_sourcemeter1']
        self.ds_hw = self.app.hardware['keithley2400_sourcemeter2']

        if self.SWEEP == 'DS':
            self.constant_hw = self.g_hw
            self.sweep_hw = self.ds_hw
        else:
            self.sweep_hw = self.g_hw
            self.constant_hw = self.ds_hw

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        #change labels to match setting
        self.ui.v_sweep_start_label.setText('V_' + self.SWEEP + ' ' + self.ui.v_sweep_start_label.text())
        self.ui.v_sweep_finish_label.setText('V_' + self.SWEEP + ' ' + self.ui.v_sweep_finish_label.text())
        self.ui.v_sweep_step_size_label.setText('V_' + self.SWEEP + ' ' + self.ui.v_sweep_step_size_label.text())
        self.ui.v_constant_label.setText(self.ui.v_constant_label.text() + self.CONSTANT)
        if (self.SWEEP == "DS"):
            self.ui.constant_groupBox.setTitle(self.ui.constant_groupBox.title() + ' 1 (G)')
            self.ui.sweep_groupBox.setTitle(self.ui.sweep_groupBox.title() + ' 2 (DS)')
        else:
            self.ui.constant_groupBox.setTitle(self.ui.constant_groupBox.title() + ' 2 (DS)')
            self.ui.sweep_groupBox.setTitle(self.ui.sweep_groupBox.title() + ' 1 (G)')


        self.constant_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_constant_doubleSpinBox)

        self.sweep_hw.settings.autozero.connect_to_widget(self.ui.autozero_sweep_comboBox)
        self.sweep_hw.settings.autorange.connect_to_widget(self.ui.autorange_sweep_checkBox)
        self.sweep_hw.settings.manual_range.connect_to_widget(self.ui.manual_range_sweep_comboBox)
        self.sweep_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_sweep_doubleSpinBox)
        self.sweep_hw.settings.NPLC.connect_to_widget(self.ui.nplc_sweep_doubleSpinBox)

        self.settings_dict = self.settings.as_dict()
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.settings_dict['V_%s_start' % self.SWEEP].connect_to_widget(self.ui.v_sweep_start_doubleSpinBox)
        self.settings_dict['V_%s_finish' % self.SWEEP].connect_to_widget(self.ui.v_sweep_finish_doubleSpinBox)
        self.settings_dict['V_%s_step_size' % self.SWEEP].connect_to_widget(self.ui.v_sweep_step_size_doubleSpinBox)
        self.settings_dict['%s_sweep_preread_delay' % self.SWEEP].connect_to_widget(self.ui.preread_delay_doubleSpinBox)
        self.settings_dict['%s_sweep_delay_between_averages' % self.SWEEP].connect_to_widget(self.ui.delay_between_averages_doubleSpinBox)
        self.settings_dict['%s_sweep_software_averages' % self.SWEEP].connect_to_widget(self.ui.software_averages_doubleSpinBox)
        self.settings_dict['%s_sweep_first_bias_settle' % self.SWEEP].connect_to_widget(self.ui.first_bias_settle_doubleSpinBox)
        self.settings_dict['dimension'].connect_to_widget(self.ui.dimension_comboBox)
        self.settings_dict['thickness'].connect_to_widget(self.ui.thickness_doubleSpinBox)
        self.settings_dict['%s_sweep_return_sweep' % self.SWEEP].connect_to_widget(self.ui.return_sweep_checkBox)
        self.settings_dict['V_%s' % self.CONSTANT].connect_to_widget(self.ui.v_constant_doubleSpinBox)

 
        # # Set up pyqtgraph graph_layout in the UI
        self.g_graph_layout = pg.GraphicsLayoutWidget()
        self.ui.g_graph_container.layout().addWidget(self.g_graph_layout)
        
        self.ds_graph_layout = pg.GraphicsLayoutWidget()
        self.ui.ds_graph_container.layout().addWidget(self.ds_graph_layout)

        # # # Create PlotItem object (a set of axes)  
        self.g_plot = self.g_graph_layout.addPlot(title="Keithley 2400 1")
        self.g_plot.setLabel('bottom', 'V_%s' % self.SWEEP)
        self.g_plot.setLabel('left', 'I_G')

        self.ds_plot = self.ds_graph_layout.addPlot(title='Keithley 2400 2')
        self.ds_plot.setLabel('bottom', 'V_%s' % self.SWEEP)
        self.ds_plot.setLabel('left', 'I_DS')
        
    def update_display(self):
        if hasattr(self, 'ds_reading') and hasattr(self, 'g_reading'):
            if self.doing_return_sweep: #plot only return sweep data
                self.g_plot.plot(self.voltages[self.num_steps:], self.save_array[self.num_steps:, 1], pen = 'r', clear = True)
                self.ds_plot.plot(self.voltages[self.num_steps:], self.save_array[self.num_steps:, 3], pen = 'b', clear = True)
            else: #plot only initial sweep
                self.g_plot.plot(self.voltages[:self.num_steps], self.save_array[:self.num_steps, 1], pen = 'r', clear = True)
                self.ds_plot.plot(self.voltages[:self.num_steps], self.save_array[:self.num_steps, 3], pen = 'b', clear = True)
            pg.QtGui.QApplication.processEvents()

    def read_settings(self):
        '''
        Pull values from settings.
        '''
        self.constant_current_compliance = self.constant_hw.settings['current_compliance']

        self.sweep_autorange = self.constant_hw.settings['autorange']
        self.sweep_autozero = self.constant_hw.settings['autozero']
        self.sweep_manual_range = self.constant_hw.settings['manual_range']
        self.sweep_current_compliance = self.constant_hw.settings['current_compliance']
        self.sweep_nplc = self.constant_hw.settings['NPLC']

        self.v_sweep_start = self.settings['V_%s_start' % self.SWEEP]
        self.v_sweep_finish = self.settings['V_%s_finish' % self.SWEEP]
        self.v_sweep_step_size = self.settings['V_%s_step_size' % self.SWEEP]
        self.v_constant = self.settings['V_%s' % self.CONSTANT]
        self.first_bias_settle = self.settings['%s_sweep_first_bias_settle' % self.SWEEP]
        self.preread_delay = self.settings['%s_sweep_preread_delay' % self.SWEEP]
        self.software_averages = self.settings['%s_sweep_software_averages' % self.SWEEP]
        self.delay_between_averages = self.settings['%s_sweep_delay_between_averages' % self.SWEEP]
        self.return_sweep = self.settings['%s_sweep_return_sweep' % self.SWEEP]
        self.dimension = self.settings['dimension']
        self.thickness = self.settings['thickness']

    
    def pre_run(self):
        self.check_filename(".txt")

        self.constant_device = self.constant_hw.keithley
        self.sweep_device = self.sweep_hw.keithley

        #these refer to the same devices as constant and sweep devices, but are convenient when we want to reference
        #to device by which terminals it corresponds to - makes things easier for measurement and saving
        self.g_device = self.g_hw.keithley
        self.ds_device = self.ds_hw.keithley
        self.g_device.reset()
        self.ds_device.reset()
        self.read_settings()

        #configure keithleys
        self.constant_device.write_current_compliance(self.constant_current_compliance)
        self.sweep_device.write_autozero(self.sweep_autozero)
        self.sweep_device.write_current_compliance(self.sweep_current_compliance)
        if not self.sweep_autorange:
            self.sweep_device.measure_current(nplc = self.sweep_nplc, current = self.sweep_manual_range, auto_range = False)
            self.constant_device.measure_current(nplc = self.sweep_nplc, current = self.sweep_manual_range, auto_range = False)
        else:
            self.sweep_device.measure_current(nplc = self.sweep_nplc)
            self.constant_device.measure_current(nplc = self.sweep_nplc)



        
        self.num_steps = np.abs(int(np.ceil(((self.v_sweep_finish - self.v_sweep_start)/self.v_sweep_step_size)))) + 1 #add 1 to account for start voltage
        self.voltages = np.arange(start = self.v_sweep_start, stop = self.v_sweep_finish + self.v_sweep_step_size, step = self.v_sweep_step_size) #add an extra step to stop since arange is exclusive
        if self.return_sweep:
            self.save_array = np.zeros(shape=(self.num_steps * 2 - 1, 5))
            self.reverse_voltages = np.arange(start = self.v_sweep_finish - self.v_sweep_step_size, stop = self.v_sweep_start - (self.v_sweep_step_size/2), step = -self.v_sweep_step_size) #step size divided by two then subtracted to ensure correct stop point

            self.voltages = np.concatenate((self.voltages, self.reverse_voltages))
        else:
            self.save_array = np.zeros(shape=(self.voltages.shape[0], 5))
        self.save_array[:,0] = self.voltages
        #prepare hardware for read
        self.sweep_device.write_output_on()
        self.constant_device.write_output_on()
        self.source_voltage = self.v_sweep_start - self.v_sweep_step_size
        self.constant_device.source_V(self.v_constant)

        time.sleep(self.first_bias_settle * .001)
        self.doing_return_sweep = False



    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.

        Runs until measurement is interrupted. Data is continuously saved if checkbox checked.
        """
        self.do_sweep()
        if self.return_sweep: #perform return sweep
            self.doing_return_sweep = True
            self.v_sweep_step_size *= -1
            self.do_sweep()


    def do_sweep(self):
        '''
        Perform sweep.
        '''
        num_steps = self.num_steps
        if self.doing_return_sweep: 
            num_steps -= 1
        for i in range(num_steps):
            self.source_voltage += self.v_sweep_step_size
            self.sweep_device.source_V(self.source_voltage)
            time.sleep(self.preread_delay * .001)
            current_readings = self.read_currents()
            self.g_reading = current_readings[0]
            g_std = current_readings[1]
            self.ds_reading = current_readings[2]
            ds_std = current_readings[3]
            save_row = i
            if self.doing_return_sweep: 
                save_row += self.num_steps #to ensure the right row is overwritten in return sweep 
            self.save_array[save_row, 1] = self.g_reading
            self.save_array[save_row, 2] = g_std
            self.save_array[save_row, 3] = self.ds_reading
            self.save_array[save_row, 4] = ds_std
            if self.interrupt_measurement_called:
                break


    def read_currents(self):
        '''
        Read both sourcemeters, taking software averages.
        '''
        g_current_read = np.zeros(int(self.software_averages))
        ds_current_read = np.zeros(int(self.software_averages))
        for i in range(int(self.software_averages)):
            g_current_read[i] = self.g_device.read_I()
            ds_current_read[i] = self.ds_device.read_I()
            time.sleep(self.delay_between_averages * .001)
        g_current_avg = np.mean(g_current_read)
        ds_current_avg = np.mean(ds_current_read)
        g_std = np.std(g_current_read, ddof = 1) #ddof - delta degrees of freedom. set to 1 for sample std
        ds_std = np.std(ds_current_read, ddof = 1)
        return [g_current_avg, g_std, ds_current_avg, ds_std]

    def post_run(self):
        '''
        Format and save measurement data.
        '''
        self.g_device.reset()
        self.ds_device.reset()
        if self.SWEEP == 'DS':
            append = '_output_curve%g.txt' % self.READ_NUMBER
        else:
            append = '_transfer_curve%g.txt' % self.READ_NUMBER
        self.check_filename(append)
        
        v_constant_info = 'V_%s =\t%g' % (self.CONSTANT, self.v_constant)
        avgs_info = 'Number of Averages =\t%g' % self.software_averages
        width_info = 'Width/um=\t%g' % self.dimension_choice[self.dimension][0]
        length_info = 'Length/um=\t%g' % self.dimension_choice[self.dimension][1]
        thickness_info = 'Thickness/nm=\t%g' % self.thickness
        info_footer = v_constant_info + "\n" + avgs_info + "\n" + width_info + "\n" + length_info + "\n" + thickness_info
        info_header = 'V_%s\tI_G (A)\tI_G Error (A)\tI_DS (A)\tI_DS Error (A)' % (self.CONSTANT)
        np.savetxt(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + append, self.save_array, fmt = '%.10f', 
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