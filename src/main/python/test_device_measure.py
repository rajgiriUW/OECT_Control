from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import os.path
import configparser

from general_curve_measure import GeneralCurveMeasure
from output_curve_measure import OutputCurveMeasure
from transfer_curve_measure import TransferCurveMeasure

class TestDeviceMeasure(GeneralCurveMeasure):
    #class variables determining vhich device's voltage will go through a sweep and which will be constant
    #these are the initial values since transfer curve will be set up first
    SWEEP = "G"
    CONSTANT = "DS"

    #class variable determining numbering of measurement output file. useful in auto_measure for multiple transfers and outputs
    READ_NUMBER = 1

    def switch_setting(self):
        '''
        Switch class variables and sweep/constant hardware references. Used for going between handling transfer and output measurements.
        '''
        self.SWEEP, self.CONSTANT = self.CONSTANT, self.SWEEP
        if (hasattr(self, 'constant_hw') and hasattr(self, 'sweep_hw')):
            self.sweep_hw, self.constant_hw = self.constant_hw, self.sweep_hw 

    def setup(self):
        self.name = "TestDevice"
        self.ui_filename = self.app.appctxt.get_resource("test_device.ui")

        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)
        TransferCurveMeasure.create_settings(self)
        self.switch_setting() #configure variables for output curve
        OutputCurveMeasure.create_settings(self)
        self.switch_setting() #configure variables for transfer curve

        #create automeasure specific settings
        self.dimension_choice = {'4000 x 20': [4000, 20], '2000 x 20': [2000, 20], '1000 x 20': [1000, 20], '800 x 20': [800, 20],
            '400 x 20': [400, 20], '200 x 20': [200, 20], '100 x 20': [100, 20]}
        self.settings.New('number_of_transfer_curves', int, initial = 1, vmin = 1)
        self.settings.New('number_of_output_curves', int, initial = 1, vmin = 1, vmax = 5)
        self.settings.New('dimension', str, choices = self.dimension_choice.keys(), initial = '4000 x 20')
        self.settings.New('thickness', unit = "nm", initial = 50)
        self.v_g_spinboxes = self.ui.v_g_groupBox.findChildren(QtGui.QDoubleSpinBox) #array of v_g spinboxes

    def setup_figure(self):
        '''
        UI event handling.
        Connects only sidebar measurement settings to ui.
        ***for automeasure, exclusively change hardware settings for each measurement using the ui.
        '''
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.ui.num_output_curves_doubleSpinBox.valueChanged.connect(self.on_output_curves_changed)
        self.connect_transfer_ui_to_settings()
        self.connect_output_ui_to_settings()
        self.settings.dimension.connect_to_widget(self.ui.dimension_comboBox)
        self.settings.thickness.connect_to_widget(self.ui.thickness_doubleSpinBox)

        # # Set up pyqtgraph graph_layout in the UI
        self.graph_layout = pg.GraphicsLayoutWidget(title = 'Test Device graphs', show = True)

        # # # Create PlotItem object (a set of axes)
        self.g_plot = self.graph_layout.addPlot(title = 'Keithley 2400 1')
        self.g_plot.setLabel('left', 'I_G')

        self.ds_plot = self.graph_layout.addPlot(title='Keithley 2400 2')
        self.ds_plot.setLabel('left', 'I_DS')

        self.graph_layout.window().setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

    def on_output_curves_changed(self):
        '''
        Enable/disable correct number of V_G spinboxes depending on how many output curves specified.
        '''
        num_curves = int(self.ui.num_output_curves_doubleSpinBox.value())
        for i in range(num_curves):
            self.v_g_spinboxes[i].setEnabled(True)
        for i in range(num_curves, 5):
            self.v_g_spinboxes[i].setEnabled(False)

    def update_display(self):
        GeneralCurveMeasure.update_display(self)
        if (self.switched):
            self.g_plot.setLabel('bottom', 'V_DS')
            self.ds_plot.setLabel('bottom', 'V_DS')
            self.switched = False #to make sure this only happens once

    def pre_run(self):
        '''
        Other pre_run steps are taken care of in run(), since Transfer and Output
        have their own procedures.
        '''
        self.graph_layout.show()
        self.switched = False
        self.dimension = self.settings['dimension'] = self.ui.dimension_comboBox.currentText()
        self.thickness = self.settings['thickness'] = self.ui.thickness_doubleSpinBox.value()
        self.ds_plot.setLabel('bottom', 'V_G')
        self.g_plot.setLabel('bottom', 'V_G')

    def run(self):
        self.read_settings = self.transfer_read_from_settings #overrides general_curve read_settings
        self.num_transfer_curves = int(self.ui.num_transfer_curves_doubleSpinBox.value())
        for i in range(self.num_transfer_curves):
            GeneralCurveMeasure.pre_run(self)
            GeneralCurveMeasure.run(self)
            GeneralCurveMeasure.post_run(self)
            self.sweep_device.source_V(self.v_sweep_start) #reset to sweep start voltage before running another curve
            self.READ_NUMBER += 1
        self.switch_setting() #configure variables for output curve
        self.switched = True
        self.READ_NUMBER = 1 #reset file numbering for output curves

        self.read_settings = self.output_read_from_settings
        self.num_output_curves = self.settings['number_of_output_curves'] = int(self.ui.num_output_curves_doubleSpinBox.value())
        self.output_v_g_values = self.read_output_v_g_spinboxes()
        
        if self.interrupt_measurement_called:
            self.interrupt_measurement_called  = False
        
        print(self.output_v_g_values)
        for v_g_value in self.output_v_g_values:
            
            GeneralCurveMeasure.pre_run(self)
            self.ui.v_g_doubleSpinBox.setValue(v_g_value)
            self.v_constant = self.settings['V_G'] = v_g_value
            self.constant_device.source_V(self.v_constant)
            GeneralCurveMeasure.run(self)
            GeneralCurveMeasure.post_run(self)
            self.sweep_device.source_V(self.v_sweep_start)
            time.sleep(self.preread_delay * .001)
            self.source_voltage = self.v_sweep_start
            self.READ_NUMBER += 1
        self.READ_NUMBER = 1 #reset file numbering
        self.switch_setting() #configure variables for transfer curve again

    def post_run(self):
        if self.SWEEP == "DS": self.switch_setting() #
        self.READ_NUMBER = 1
        self.make_config()

    def transfer_read_from_settings(self):
        self.constant_current_compliance = self.constant_hw.settings['current_compliance'] = self.ui.current_compliance_ds_output_doubleSpinBox.value()

        self.sweep_autozero = self.sweep_hw.settings['autozero'] = self.ui.autozero_g_comboBox.currentText()
        self.sweep_autorange = self.sweep_hw.settings['autorange'] = self.ui.autorange_g_checkBox.isChecked()
        self.sweep_manual_range = self.sweep_hw.settings['manual_range'] = self.ui.manual_range_g_comboBox.currentText()
        self.sweep_current_compliance = self.sweep_hw.settings['current_compliance'] = self.ui.current_compliance_g_output_doubleSpinBox.value()
        self.sweep_nplc = self.sweep_hw.settings['NPLC'] = self.ui.nplc_g_doubleSpinBox.value()

        self.v_sweep_start = self.settings['V_G_start'] = self.ui.v_g_start_doubleSpinBox.value()
        self.v_sweep_finish = self.settings['V_G_finish'] = self.ui.v_g_finish_doubleSpinBox.value()
        self.v_sweep_step_size = self.settings['V_G_step_size'] = self.ui.v_g_step_size_doubleSpinBox.value()
        self.preread_delay = self.settings['%s_sweep_preread_delay' % self.SWEEP] = self.ui.preread_delay_transfer_doubleSpinBox.value()
        self.delay_between_averages = self.settings['G_sweep_delay_between_averages'] = self.ui.delay_between_averages_transfer_doubleSpinBox.value()
        self.software_averages = self.settings['G_sweep_software_averages'] = self.ui.software_averages_transfer_doubleSpinBox.value()
        self.first_bias_settle = self.settings['G_sweep_first_bias_settle'] = self.ui.first_bias_settle_transfer_doubleSpinBox.value()
        self.return_sweep = self.settings['G_sweep_return_sweep'] = self.ui.return_sweep_transfer_checkBox.isChecked()
        self.v_constant = self.settings['V_DS'] = self.ui.v_ds_doubleSpinBox.value()
        self.num_transfer_curves = self.settings['number_of_transfer_curves'] = int(self.ui.num_transfer_curves_doubleSpinBox.value())
        self.is_test_wrapper = True

        self.transfer_preread = self.preread_delay # for config file
        self.transfer_first_bias_settle = self.first_bias_settle
        self.transfer_vds = self.v_constant

    def output_read_from_settings(self):
        self.constant_current_compliance = self.constant_hw.settings['current_compliance'] = self.ui.current_compliance_g_output_doubleSpinBox.value()

        self.sweep_autozero = self.sweep_hw.settings['autozero'] = self.ui.autozero_ds_comboBox.currentText()
        self.sweep_autorange = self.sweep_hw.settings['autorange'] = self.ui.autorange_ds_checkBox.isChecked()
        self.sweep_manual_range = self.sweep_hw.settings['manual_range'] = self.ui.manual_range_ds_comboBox.currentText()
        self.sweep_current_compliance = self.sweep_hw.settings['current_compliance'] = self.ui.current_compliance_ds_output_doubleSpinBox.value()
        self.sweep_nplc = self.sweep_hw.settings['NPLC'] = self.ui.nplc_ds_doubleSpinBox.value()

        self.v_sweep_start = self.settings['V_DS_start'] = self.ui.v_ds_start_doubleSpinBox.value()
        self.v_sweep_finish = self.settings['V_DS_finish'] = self.ui.v_ds_finish_doubleSpinBox.value()
        self.v_sweep_step_size = self.settings['V_DS_step_size'] = self.ui.v_ds_step_size_doubleSpinBox.value()
        self.preread_delay = self.settings['DS_sweep_preread_delay'] = self.ui.preread_delay_output_doubleSpinBox.value()
        self.delay_between_averages = self.settings['DS_sweep_delay_between_averages'] = self.ui.delay_between_averages_output_doubleSpinBox.value()
        self.software_averages = self.settings['DS_sweep_software_averages'] = self.ui.software_averages_output_doubleSpinBox.value()
        self.first_bias_settle = self.settings['DS_sweep_first_bias_settle'] = self.ui.first_bias_settle_output_doubleSpinBox.value()
        self.return_sweep = self.settings['DS_sweep_return_sweep'] = self.ui.return_sweep_output_checkBox.isChecked()
        self.v_constant = self.settings['V_G'] = self.ui.v_g1_doubleSpinBox.value()

        self.output_preread = self.preread_delay # for config file
        self.output_first_bias_settle = self.first_bias_settle


    def read_output_v_g_spinboxes(self):
        output_v_g_values = np.zeros(self.num_output_curves)
        for i in range(self.num_output_curves):
            output_v_g_values[i] = self.v_g_spinboxes[i].value()
        return output_v_g_values

    def connect_transfer_ui_to_settings(self):
        self.settings.V_G_start.connect_to_widget(self.ui.v_g_start_doubleSpinBox)
        self.settings.V_G_finish.connect_to_widget(self.ui.v_g_finish_doubleSpinBox)
        self.settings.V_G_step_size.connect_to_widget(self.ui.v_g_step_size_doubleSpinBox)
        self.settings.G_sweep_preread_delay.connect_to_widget(self.ui.preread_delay_transfer_doubleSpinBox)
        self.settings.G_sweep_delay_between_averages.connect_to_widget(self.ui.delay_between_averages_transfer_doubleSpinBox)
        self.settings.G_sweep_software_averages.connect_to_widget(self.ui.software_averages_transfer_doubleSpinBox)
        self.settings.G_sweep_first_bias_settle.connect_to_widget(self.ui.first_bias_settle_transfer_doubleSpinBox)
        self.settings.G_sweep_return_sweep.connect_to_widget(self.ui.return_sweep_transfer_checkBox)
        self.settings.V_DS.connect_to_widget(self.ui.v_ds_doubleSpinBox)
        self.settings.number_of_transfer_curves.connect_to_widget(self.ui.num_transfer_curves_doubleSpinBox)

    def connect_output_ui_to_settings(self):
        self.settings.V_DS_start.connect_to_widget(self.ui.v_ds_start_doubleSpinBox)
        self.settings.V_DS_finish.connect_to_widget(self.ui.v_ds_finish_doubleSpinBox)
        self.settings.V_DS_step_size.connect_to_widget(self.ui.v_ds_step_size_doubleSpinBox)
        self.settings.DS_sweep_preread_delay.connect_to_widget(self.ui.preread_delay_output_doubleSpinBox)
        self.settings.DS_sweep_delay_between_averages.connect_to_widget(self.ui.delay_between_averages_output_doubleSpinBox)
        self.settings.DS_sweep_software_averages.connect_to_widget(self.ui.software_averages_output_doubleSpinBox)
        self.settings.DS_sweep_first_bias_settle.connect_to_widget(self.ui.first_bias_settle_output_doubleSpinBox)
        self.settings.DS_sweep_return_sweep.connect_to_widget(self.ui.return_sweep_output_checkBox)
        self.settings.V_G.connect_to_widget(self.ui.v_g1_doubleSpinBox)
        self.settings.number_of_output_curves.connect_to_widget(self.ui.num_output_curves_doubleSpinBox)


    def make_config(self):
        '''
        If a config file does not exist, this will generate one automatically.
        
        '''
        config = configparser.ConfigParser()
        config.optionxform = str
    
        config['Dimensions'] = {'Width (um)': self.dimension_choice[self.dimension][0], 
                                'Length (um)': self.dimension_choice[self.dimension][1]}
        config['Transfer'] = {'Preread (ms)': self.transfer_preread,
                              'First Bias (ms)': self.transfer_first_bias_settle,
                              'Vds (V)': self.transfer_vds}
    
        config['Output'] = {'Preread (ms)': self.output_preread,
                            'First Bias (ms)': self.output_first_bias_settle,
                            'Output Vgs': len(self.output_v_g_values)}
        
        for n, o in enumerate(self.output_v_g_values):
            key = 'Vgs (V) ' + str(n)
            config['Output'][key] = str(o)
            
        path = self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + r'_config.cfg'
        with open(path, 'w') as configfile:
            config.write(configfile)
    
        return path + r'\config.cfg'