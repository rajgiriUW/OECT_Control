from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import os.path
from relay_ft245r import FT245R

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
        if self.SWEEP == "DS": self.name = "Output Curve"
        elif self.SWEEP == "G": self.name = "Transfer Curve"
        # self.ui_filename = sibling_path(__file__, "general_curve.ui")
        self.ui_filename = self.app.appctxt.get_resource("general_curve.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        self.create_settings()
        self.dimension_choice = {'4000 x 10': [4000, 10], '2000 x 10': [2000, 10], '1000 x 10': [1000, 10], '800 x 10': [800, 10], 
            '400 x 10': [400, 10], '200 x 10': [200, 10], '100 x 10': [100, 10]}
        self.settings.New('dimension', str, choices = self.dimension_choice.keys(), initial = '4000 x 10')
        self.settings.New('thickness', unit = "nm", initial = 50)
        self.settings.New('num_cycles', int, initial=1)
        
        self.ui.setRelaysGenCurveButton.clicked.connect(self.set_relay)
        self.ui.resetRelaysGenCurveButton.clicked.connect(self.reset_relay)
        
        self.pixels = {'800 x 10': 2,
                       '2000 x 10': 3,
                       '200 x 10': 4,
                       '100 x 10': 5,
                       '400 x 10': 6,
                       '1000 x 10': 7,
                       '4000 x 10': 8}

        self.setup_relay()

    def setup_relay(self):
        
        # Connect the relay
        try:
            self.relay_d = FT245R()
            self.relay_s = FT245R()
            drain = self.relay_d.list_dev()[0]
            source = self.relay_s.list_dev()[1]
            
            self.relay_d.connect(drain)
            self.relay_s.connect(source)
            self.relay_exists = True
            
        except:
            print('No relay board connected!')
            self.relay_exists = False
        

    def set_relay(self):
        """Mostly a copy of the Test_device_measure function to set the relays
        You should set them manually if you want to be sure"""
        _dimension = self.pixels[self.settings['dimension']]
        print(_dimension)
        for k, v in self.pixels.items():
            if k == _dimension:
                self.relay_d.switchon(v)
                self.relay_s.switchon(v)
            else:
                self.relay_d.switchoff(v)
                self.relay_s.switchoff(v)
        

    def reset_relay(self):
        """Sets the relays to all be off"""
        
        
        for k, v in self.pixels.items():
            
            self.relay_d.switchoff(v)
            self.relay_s.switchoff(v)
            
        # To error check for EIS relay accidentally open
        self.relay_d.switchoff(1)
        self.relay_s.switchoff(1)

    def create_settings(self):
                # Measurement Specific Settings
      # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to   the Microscope user interface

        self.settings.New('V_%s_start' % self.SWEEP, unit = 'V', si = True, initial = -0.7, spinbox_decimals = 3, spinbox_step=0.025)
        self.settings.New('V_%s_finish' % self.SWEEP, unit = 'V', si = True, initial = 0.0, spinbox_decimals = 3, spinbox_step=0.025)
        self.settings.New('V_%s_step_size' % self.SWEEP, unit = 'V', si = True, initial = 0.025, spinbox_decimals = 3, spinbox_step=0.025)
        self.settings.New('%s_sweep_preread_delay' % self.SWEEP, unit = 'ms', si = True, initial = 5000)
        self.settings.New('%s_sweep_delay_between_averages' % self.SWEEP, unit = 'ms', si = True, initial = 200)
        self.settings.New('%s_sweep_software_averages' % self.SWEEP, int, initial = 5, vmin = 1)
        self.settings.New('%s_sweep_first_bias_settle' % self.SWEEP, unit = 'ms', si = True, initial = 2000)
        
        self.settings.New('%s_sweep_return_sweep' % self.SWEEP, bool, initial = True)
        self.settings.New('V_%s' % self.CONSTANT, unit = 'V', si = True, initial = -0.6, spinbox_decimals = 3, spinbox_step=0.025)

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
        self.settings_dict['num_cycles'].connect_to_widget(self.ui.num_cycles_doubleSpinBox)

 
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
                self.g_plot.plot(self.voltages[:], self.save_array[:, 1], pen = 'b', clear = True)
                self.ds_plot.plot(self.voltages[:], self.save_array[:, 3], pen = 'r', clear = True)
#                self.g_plot.plot(self.voltages[:self.num_steps], self.save_array[:self.num_steps, 1], pen = 'r', clear = False)
#                self.ds_plot.plot(self.voltages[:self.num_steps], self.save_array[:self.num_steps, 3], pen = 'b', clear = False)

            else: #plot only initial sweep
                self.g_plot.plot(self.voltages[:self.num_steps], self.save_array[:self.num_steps, 1], pen = 'r', clear = True)
                self.ds_plot.plot(self.voltages[:self.num_steps], self.save_array[:self.num_steps, 3], pen = 'b', clear = True)
            pg.QtGui.QApplication.processEvents()

    def read_settings(self):
        '''
        Pull values from settings.
        '''
        self.constant_current_compliance = self.constant_hw.settings['current_compliance']

        self.sweep_autorange = self.sweep_hw.settings['autorange']
        self.sweep_autozero = self.sweep_hw.settings['autozero']
        self.sweep_manual_range = self.sweep_hw.settings['manual_range']
        self.sweep_current_compliance = self.sweep_hw.settings['current_compliance']
        self.sweep_nplc = self.sweep_hw.settings['NPLC']

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
        self.num_cycles = self.settings['num_cycles']
        self.is_test_wrapper = False # checks if test GUI calling this or not
    
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

        # Check the relay
#        if TestDeviceMeasure.relay_exists and self.use_relay:
#            
#            #self.relay_d.switchon(self.pixels[self.settings['pixel']])
#            #self.relay_s.switchon(self.pixels[self.settings['pixel']])
#            
#            self.reset_relay()
#            
#            self.drain_boxes[self.pixels[self.settings['pixel']] - 1].setChecked(True)
#            self.source_boxes[self.pixels[self.settings['pixel']] - 1].setChecked(True)
#            
#            self.set_relay()


        #configure keithleys
        self.constant_device.write_current_compliance(self.constant_current_compliance)
        self.sweep_device.write_autozero(self.sweep_autozero)
        self.sweep_device.write_current_compliance(self.sweep_current_compliance)
        if not self.sweep_autorange:
            self.sweep_device.measure_current(nplc = self.sweep_nplc, current = self.sweep_manual_range, auto_range = False)
            # self.constant_device.measure_current(nplc = self.sweep_nplc, current = self.sweep_manual_range, auto_range = False)
            self.constant_device.measure_current()
        else:
            self.sweep_device.measure_current(nplc = self.sweep_nplc)
            # self.constant_device.measure_current(nplc = self.sweep_nplc)
            self.constant_device.measure_current()
        
        self.num_steps = np.abs(int(np.ceil(((self.v_sweep_finish - self.v_sweep_start)/self.v_sweep_step_size)))) + 1 #add 1 to account for start voltage
        
        # Logic for voltages is that the start and end determine the range and step size polarity is corrected
        # for that range. e.g. a step size of 0.1 V will flip automatically to -0.1 V if start_v < stop_v
        
        if np.sign(self.v_sweep_start - self.v_sweep_finish) ==  np.sign(self.v_sweep_step_size):
            
            self.settings['V_%s_step_size' % self.SWEEP] *= -1
            self.v_sweep_step_size = self.settings['V_%s_step_size' % self.SWEEP]
        
        self.voltages = np.arange(start = self.v_sweep_start, 
                                  stop = self.v_sweep_finish + self.v_sweep_step_size, 
                                  step = self.v_sweep_step_size) #add an extra step to stop since arange is exclusive
        if self.return_sweep:
            
            self.reverse_voltages = np.arange(start = self.v_sweep_finish - self.v_sweep_step_size, stop = self.v_sweep_start - (self.v_sweep_step_size/2), step = -self.v_sweep_step_size) #step size divided by two then subtracted to ensure correct stop point
            self.voltages = np.concatenate((self.voltages, self.reverse_voltages))
            self.save_array = np.zeros(shape=(self.voltages.shape[0], 5))
            
        else:
            self.save_array = np.zeros(shape=(self.voltages.shape[0], 5))
            
        self.save_array[:,0] = self.voltages
        #prepare hardware for read
        self.sweep_device.write_output_on()
        self.constant_device.write_output_on()
        self.source_voltage = self.v_sweep_start
        self.sweep_device.source_V(self.source_voltage)
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

        self.finished = False # flag for post-run
        
        if self.is_test_wrapper:
            # Avoids the cycles parameter
            self.do_sweep()
            if self.return_sweep: 
                self.doing_return_sweep = True

        else:
            self.num_cycles = self.settings['num_cycles']        
            
            for cycle in range(self.num_cycles):
                self.do_sweep()
                if self.return_sweep: 
                    self.doing_return_sweep = True
                if cycle < self.num_cycles-1: # avoid duplicate final run
                    self.post_run()
                self.READ_NUMBER += 1
            self.READ_NUMBER -= 1 
            
        self.finished = True

    def do_sweep(self):
        '''
        Perform sweep.
        '''
        num_steps = self.num_steps
        if self.doing_return_sweep: 
            num_steps -= 1

        for i, v in enumerate(self.voltages):
            
            self.sweep_device.source_V(v)
            time.sleep(self.preread_delay * .001)
            current_readings = self.read_currents()
            self.g_reading = current_readings[0]
            g_std = current_readings[1]
            self.ds_reading = current_readings[2]
            ds_std = current_readings[3]
            save_row = i
            #if self.doing_return_sweep: 
            #    save_row += self.num_steps #to ensure the right row is overwritten in return sweep 
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
        if self.finished:
        
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
        info_header = 'V_%s\tI_G (A)\tI_G Error (A)\tI_DS (A)\tI_DS Error (A)' % (self.SWEEP)
        np.savetxt(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + append, 
                   self.save_array, fmt = '%.10f', delimiter='\t',comments='',
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
            
            for i in range(100): #hard limit of 100 checks
                
                if not (os.path.exists(directory+"/"+samplename + '_' + str(i) + '_' + append)):
                    self.app.settings['sample'] = samplename + '_' + str(i) + '_'
                    break