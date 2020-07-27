'''
July 2 2020

@author Linda Taing
'''
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import load_qt_ui_file
import sys

class KeithleyApp(BaseMicroscopeApp):
    
    name = "OECT_Control"
    appctxt = ApplicationContext()
    ui_filename = appctxt.get_resource('base_microscope_app_mdi.ui')
    
    
    def setup(self):
        # self.appctxt = ApplicationContext()

        from keithley2400_sourcemeter_hc import Keithley2400SourceMeterComponent
        
        self.k1 = self.add_hardware(Keithley2400SourceMeterComponent(self, name = 'keithley2400_sourcemeter1'))
        self.k1.settings['port'] = 'GPIB0::22'

        self.k2 = self.add_hardware(Keithley2400SourceMeterComponent(self, name = 'keithley2400_sourcemeter2'))
        self.k2.settings['port'] = 'GPIB0::24'

        from output_curve_measure import OutputCurveMeasure
        self.add_measurement(OutputCurveMeasure(self))
        from transfer_curve_measure import TransferCurveMeasure
        self.add_measurement(TransferCurveMeasure(self))

        from test_device_measure import TestDeviceMeasure
        self.add_measurement(TestDeviceMeasure(self))
        from transient_step_response_measure import TransientStepResponseMeasure
        self.add_measurement(TransientStepResponseMeasure(self))

       

if __name__ == '__main__':
    app = KeithleyApp(sys.argv)
    exit_code = app.appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)