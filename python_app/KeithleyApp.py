'''
July 2 2020

@author Linda Taing
'''

from ScopeFoundry import BaseMicroscopeApp
import sys
sys.path.append("../")
class KeithleyTestApp(BaseMicroscopeApp):
    
    name = "keithley_test_app"
    
    def setup(self):
        from keithley_sourcemeter.keithley2400_sourcemeter_hc import Keithley2400SourceMeterComponent
        
        self.k1 = self.add_hardware(Keithley2400SourceMeterComponent(self, name = 'keithley2400_sourcemeter1'))
        self.k1.settings['port'] = 'GPIB0::22'

        
        self.k2 = self.add_hardware(Keithley2400SourceMeterComponent(self, name = 'keithley2400_sourcemeter2'))
        self.k2.settings['port'] = 'GPIB0::24'

        from python_measurements.output_curve_measure import OutputCurveMeasure
        self.add_measurement(OutputCurveMeasure(self))

        from python_measurements.transfer_curve_measure import TransferCurveMeasure
        self.add_measurement(TransferCurveMeasure(self))
        from python_measurements.auto_measure import AutoMeasure
        self.add_measurement(AutoMeasure(self))

        
if __name__ == '__main__':
    import sys
    app = KeithleyTestApp(sys.argv)
    app.exec_()