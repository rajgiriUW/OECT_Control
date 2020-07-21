'''
July 2 2020

@author Linda Taing
'''
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow
from ScopeFoundry import BaseMicroscopeApp
import sys

class KeithleyApp(BaseMicroscopeApp):
    
    name = "keithley_app"
    
    def setup(self):
        from src.main.resources.base.keithley_sourcemeter.keithley2400_sourcemeter_hc import Keithley2400SourceMeterComponent
        
        self.k1 = self.add_hardware(Keithley2400SourceMeterComponent(self, name = 'keithley2400_sourcemeter1'))
        self.k1.settings['port'] = 'GPIB0::22'

        self.k2 = self.add_hardware(Keithley2400SourceMeterComponent(self, name = 'keithley2400_sourcemeter2'))
        self.k2.settings['port'] = 'GPIB0::24'

        from src.main.resources.base.python_measurements.output_curve_measure import OutputCurveMeasure
        self.add_measurement(OutputCurveMeasure(self))
        from src.main.resources.base.python_measurements.transfer_curve_measure import TransferCurveMeasure
        self.add_measurement(TransferCurveMeasure(self))

        from src.main.resources.base.python_measurements.test_device_measure import TestDeviceMeasure
        self.add_measurement(TestDeviceMeasure(self))
        from src.main.resources.base.python_measurements.transient_step_response_measure import TransientStepResponseMeasure
        self.add_measurement(TransientStepResponseMeasure(self))

if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    app = KeithleyApp(sys.argv)
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)