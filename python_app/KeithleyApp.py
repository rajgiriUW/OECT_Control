from ScopeFoundry import BaseMicroscopeApp
import sys
sys.path.append("../")
class KeithleyTestApp(BaseMicroscopeApp):
    
    name = "keithley_test_app"
    
    def setup(self):
        from keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        hw = self.add_hardware(KeithleySourceMeterComponent(self))

        hw.settings['port'] = 'COM6'
        hw.settings['connected'] = True

        from keithley_sourcemeter.slow_iv import SlowIVMeasurement
        
        self.add_measurement(SlowIVMeasurement(self))
        
if __name__ == '__main__':
    import sys
    app = KeithleyTestApp(sys.argv)
    app.exec_()