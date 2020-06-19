from ScopeFoundry import BaseMicroscopeApp

class KeithleyTestApp(BaseMicroscopeApp):
    
    name = "keithley_test_app"
    
    def setup(self):
        
        from ScopeFoundryHW.keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        
        hw = self.add_hardware(KeithleySourceMeterComponent(self))

        hw.settings['port'] = 'COM6'
        hw.settings['connected'] = True

        from ScopeFoundryHW.keithley_sourcemeter.slow_iv import SlowIVMeasurement
        
        self.add_measurement(SlowIVMeasurement(self))
        
if __name__ == '__main__':
    import sys
    app = KeithleyTestApp(sys.argv)
    app.exec_()