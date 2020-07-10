from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from PyQt5 import *
import numpy as np
import time
import os.path

from .general_curve_measure import GeneralCurveMeasure
from .output_curve_measure import OutputCurveMeasure
from .transfer_curve_measure import TransferCurveMeasure

class AutoMeasure(GeneralCurveMeasure):
    SWEEP = "G"
    CONSTANT = "DS"

    READ_NUMBER = 1

    def switch_setting(self):
        sweep_temp = self.SWEEP
        constant_temp = self.CONSTANT
        self.SWEEP = constant_temp
        self.CONSTANT = sweep_temp
        if (hasattr(self, 'constant_hw') and hasattr(self, 'sweep_hw')):
            sweep_hw_temp = self.sweep_hw
            constant_hw_temp = self.constant_hw
            self.sweep_hw = constant_hw_temp
            self.constant_hw = sweep_hw_temp

    def setup(self):
        self.name = "auto_measure"
        self.ui_filename = sibling_path(__file__, "auto_measure.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)
        TransferCurveMeasure.create_settings(self)
        self.switch_setting()
        OutputCurveMeasure.create_settings(self)
        self.switch_setting()

        self.dimension_choice = {'4000 x 20': [4000, 20], '2000 x 20': [2000, 20], '1000 x 20': [1000, 20], '800 x 20': [800, 20], 
            '400 x 20': [400, 20], '200 x 20': [200, 20], '100 x 20': [100, 20]}
        self.settings.New('number_of_transfer_curves', initial = 1, vmin = 1)        
        self.settings.New('number_of_output_curves', initial = 1, vmin = 1, vmax = 5)
        self.settings.New('dimension', str, choices = self.dimension_choice.keys(), initial = '4000 x 20')
        self.settings.New('thickness', unit = "nm", initial = 50)
        self.v_g_spinboxes = self.ui.v_g_groupBox.findChildren(QtGui.QDoubleSpinBox)

    def setup_figure(self):
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.ui.num_output_curves_doubleSpinBox.valueChanged.connect(self.on_output_curves_changed)

    def on_output_curves_changed(self):
        num_curves = int(self.ui.num_output_curves_doubleSpinBox.value())
        # print(num_curves)
        for i in range(num_curves):
            self.v_g_spinboxes[i].setEnabled(True)
        for i in range(num_curves, 5):
            self.v_g_spinboxes[i].setEnabled(False)
        
    def update_display(self):
        pass

    def pre_run(self):
        pass
        
    def run(self):
        self.read_settings = self.transfer_read_from_settings
        self.dimension = self.settings['dimension'] = self.ui.dimension_comboBox.currentText()
        self.thickness = self.settings['thickness'] = self.ui.thickness_doubleSpinBox.value()
        print([self.dimension, self.thickness])
        GeneralCurveMeasure.pre_run(self)
        for i in range(self.num_transfer_curves):
            GeneralCurveMeasure.run(self)
            GeneralCurveMeasure.post_run(self)
            self.sweep_device.source_V(self.v_sweep_start)
            self.READ_NUMBER += 1
        self.switch_setting()
        self.READ_NUMBER = 1
        self.read_settings = self.output_read_from_settings
        GeneralCurveMeasure.pre_run(self)
        for v_g_value in self.output_v_g_values:
            self.v_constant = self.settings['V_G'] = v_g_value
            self.constant_device.source_V(self.v_constant)
            GeneralCurveMeasure.run(self)
            GeneralCurveMeasure.post_run(self)
            self.sweep_device.source_V(self.v_sweep_start)
            self.READ_NUMBER += 1
        self.READ_NUMBER = 1
        self.switch_setting()

    def post_run(self):
        if self.SWEEP == "DS": self.switch_setting()
        self.READ_NUMBER = 1


    def transfer_read_from_settings(self):
        self.constant_current_compliance = self.constant_hw.settings['current_compliance'] = self.ui.current_compliance_ds_output_doubleSpinBox.value()

        self.sweep_autozero = self.sweep_hw.settings['autozero'] = self.ui.autozero_g_comboBox.currentText()
        self.sweep_autorange = self.sweep_hw.settings['autorange'] = self.ui.autorange_g_checkBox.isChecked()
        self.sweep_source_mode = self.sweep_hw.settings['source_mode'] = self.ui.source_mode_g_comboBox.currentText()
        self.sweep_manual_range = self.sweep_hw.settings['manual_range'] = self.ui.manual_range_g_comboBox.currentText()
        self.sweep_current_compliance = self.sweep_hw.settings['current_compliance'] = self.ui.current_compliance_g_output_doubleSpinBox.value()
        self.sweep_nplc = self.sweep_hw.settings['NPLC_a'] = self.ui.nplc_g_doubleSpinBox.value()
        
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

    def output_read_from_settings(self):
        self.constant_current_compliance = self.constant_hw.settings['current_compliance'] = self.ui.current_compliance_g_output_doubleSpinBox.value()

        self.sweep_autozero = self.sweep_hw.settings['autozero'] = self.ui.autozero_ds_comboBox.currentText()
        self.sweep_autorange = self.sweep_hw.settings['autorange'] = self.ui.autorange_ds_checkBox.isChecked()
        self.sweep_source_mode = self.sweep_hw.settings['source_mode'] = self.ui.source_mode_ds_comboBox.currentText()
        self.sweep_manual_range = self.sweep_hw.settings['manual_range'] = self.ui.manual_range_ds_comboBox.currentText()
        self.sweep_current_compliance = self.sweep_hw.settings['current_compliance'] = self.ui.current_compliance_ds_output_doubleSpinBox.value()
        self.sweep_nplc = self.sweep_hw.settings['NPLC_a'] = self.ui.nplc_ds_doubleSpinBox.value()
        
        self.v_sweep_start = self.settings['V_DS_start'] = self.ui.v_ds_start_doubleSpinBox.value()
        self.v_sweep_finish = self.settings['V_DS_finish'] = self.ui.v_ds_finish_doubleSpinBox.value()
        self.v_sweep_step_size = self.settings['V_DS_step_size'] = self.ui.v_ds_step_size_doubleSpinBox.value()
        self.preread_delay = self.settings['DS_sweep_preread_delay'] = self.ui.preread_delay_output_doubleSpinBox.value()
        self.delay_between_averages = self.settings['DS_sweep_delay_between_averages'] = self.ui.delay_between_averages_output_doubleSpinBox.value()
        self.software_averages = self.settings['DS_sweep_software_averages'] = self.ui.software_averages_output_doubleSpinBox.value()
        self.first_bias_settle = self.settings['DS_sweep_first_bias_settle'] = self.ui.first_bias_settle_output_doubleSpinBox.value()
        self.return_sweep = self.settings['DS_sweep_return_sweep'] = self.ui.return_sweep_output_checkBox.isChecked()
        self.v_constant = self.settings['V_G'] = self.ui.v_g1_doubleSpinBox.value()
        self.num_output_curves = self.settings['number_of_output_curves'] = int(self.ui.num_output_curves_doubleSpinBox.value())
        self.output_v_g_values = self.read_output_v_g_spinboxes()

    def read_output_v_g_spinboxes(self):
        output_v_g_values = np.zeros(self.num_output_curves)
        for i in range(self.num_output_curves):
            output_v_g_values[i] = self.v_g_spinboxes[i].value()
        return output_v_g_values

    # def transfer_connect_to_hardware(self):
    #     self.constant_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_ds_output_doubleSpinBox)

    #     self.sweep_hw.settings.autozero.connect_to_widget(self.ui.autozero_g_comboBox)
    #     self.sweep_hw.settings.autorange.connect_to_widget(self.ui.autorange_g_checkBox)
    #     self.sweep_hw.settings.source_mode.connect_to_widget(self.ui.source_mode_g_comboBox)
    #     self.sweep_hw.settings.manual_range.connect_to_widget(self.ui.manual_range_g_comboBox)
    #     self.sweep_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_g_output_doubleSpinBox)
    #     self.sweep_hw.settings.NPLC_a.connect_to_widget(self.ui.nplc_g_doubleSpinBox)
    #     self.settings.V_DS_start.connect_to_widget(self.ui.v_g_start_doubleSpinBox)
    #     self.settings.V_DS_finish.connect_to_widget(self.ui.v_g_finish_doubleSpinBox)
    #     self.settings.V_DS_step_size.connect_to_widget(self.ui.v_g_step_size_doubleSpinBox)
    #     self.settings.DS_sweep_preread_delay.connect_to_widget(self.ui.preread_delay_transfer_doubleSpinBox)
    #     self.settings.DS_sweep_delay_between_averages.connect_to_widget(self.ui.delay_between_averages_transfer_doubleSpinBox)
    #     self.settings.DS_sweep_software_averages.connect_to_widget(self.ui.software_averages_transfer_doubleSpinBox)
    #     self.settings.DS_sweep_first_bias_settle.connect_to_widget(self.ui.first_bias_settle_transfer_doubleSpinBox)
    #     self.settings.DS_sweep_return_sweep.connect_to_widget(self.ui.return_sweep_transfer_checkBox)
    #     self.settings.V_DS.connect_to_widget(self.ui.v_ds_doubleSpinBox)
    #     self.settings.number_of_transfer_curves.connect_to_widget(self.ui.num_transfer_curves_doubleSpinBox)

    # def output_connect_to_hardware(self):
    #     self.constant_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_g_output_doubleSpinBox)

    #     self.sweep_hw.settings.autozero.connect_to_widget(self.ui.autozero_ds_comboBox)
    #     self.sweep_hw.settings.autorange.connect_to_widget(self.ui.autorange_ds_checkBox)
    #     self.sweep_hw.settings.source_mode.connect_to_widget(self.ui.source_mode_ds_comboBox)
    #     self.sweep_hw.settings.manual_range.connect_to_widget(self.ui.manual_range_ds_comboBox)
    #     self.sweep_hw.settings.current_compliance.connect_to_widget(self.ui.current_compliance_ds_output_doubleSpinBox)
    #     self.sweep_hw.settings.NPLC_a.connect_to_widget(self.ui.nplc_ds_doubleSpinBox)
    #     self.settings.V_DS_start.connect_to_widget(self.ui.v_ds_start_doubleSpinBox)
    #     self.settings.V_DS_finish.connect_to_widget(self.ui.v_ds_finish_doubleSpinBox)
    #     self.settings.V_DS_step_size.connect_to_widget(self.ui.v_ds_step_size_doubleSpinBox)
    #     self.settings.DS_sweep_preread_delay.connect_to_widget(self.ui.preread_delay_output_doubleSpinBox)
    #     self.settings.DS_sweep_delay_between_averages.connect_to_widget(self.ui.delay_between_averages_output_doubleSpinBox)
    #     self.settings.DS_sweep_software_averages.connect_to_widget(self.ui.software_averages_output_doubleSpinBox)
    #     self.settings.DS_sweep_first_bias_settle.connect_to_widget(self.ui.first_bias_settle_output_doubleSpinBox)
    #     self.settings.DS_sweep_return_sweep.connect_to_widget(self.ui.return_sweep_output_checkBox)
    #     self.settings.V_G.connect_to_widget(self.ui.v_g1_doubleSpinBox)
    #     self.settings.number_of_output_curves.connect_to_widget(self.ui.num_output_curves_doubleSpinBox)
