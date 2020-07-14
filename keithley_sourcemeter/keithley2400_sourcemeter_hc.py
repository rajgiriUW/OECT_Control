'''
July 2 2020
@author: Linda Taing
'''
from ScopeFoundry import HardwareComponent

try:
    from .keithley2400_sourcemeter_interface import Keithley2400SourceMeter
except Exception as err:
    print("Cannot load required modules for Keithley SourceMeter:", err)


class Keithley2400SourceMeterComponent(HardwareComponent): #object-->HardwareComponent
    
    # name = 'keithley2400_sourcemeter'
    debug = False
    
    AUTOZERO_DEFAULT = 'on'
    SOURCE_MODE_DEFAULT = 'VOLT'
    MANUAL_RANGE_DEFAULT = '1 A'
    AUTORANGE_DEFAULT = True
    CURRENT_COMPLIANCE_DEFAULT = .1
    VOLTAGE_COMPLIANCE_DEFAULT = -.95
    DRAIN_BIAS_DEFAULT = -.6
    NPLC_DEFAULT = 1

    def setup(self):
        self.debug = True
        
        self.port = self.settings.New('port', dtype=str)
        

        self.i_ranges = {'1 uA':1.05e-6, '10 uA':1.05e-5, '100 uA':1.05e-4, 
                         '1 mA':1.05e-3, '10 mA':1.05e-2, '100 mA':1.05e-1,
                         '1 A':1.05}
        self.i_ranges_inv = {v:k for k,v in self.i_ranges.items()}
        
        #set up settings in hardware panel
        self.autozero = self.settings.New('autozero', str, choices = {'on', 'off', 'once'}, initial = self.AUTOZERO_DEFAULT)
        self.autorange = self.settings.New('autorange', bool, initial = self.AUTORANGE_DEFAULT)
        self.source_mode = self.settings.New('source_mode', str, choices = {'VOLT', 'CURR'}, initial = self.SOURCE_MODE_DEFAULT)
        self.manual_range = self.settings.New('manual_range', str, choices = self.i_ranges.keys(), initial = self.MANUAL_RANGE_DEFAULT)
        self.current_compliance = self.settings.New('current_compliance', unit='A', initial = self.CURRENT_COMPLIANCE_DEFAULT)
        self.voltage_compliance = self.settings.New('voltage_compliance', unit='V', initial = self.VOLTAGE_COMPLIANCE_DEFAULT)
        self.drain_bias = self.settings.New('drain_bias', unit = 'V', initial = self.DRAIN_BIAS_DEFAULT)
        self.NPLC = self.settings.New('NPLC', initial = self.NPLC_DEFAULT)
        
    def connect(self):
        if self.debug: print("connecting to keithley sourcemeter")
        
        # Open connection to hardware
        self.keithley = Keithley2400SourceMeter(port=self.port.val, debug=self.debug_mode.val)
        print('connected to ',self.name)
        
    
    def disconnect(self):
        #disconnect hardware
        if hasattr(self, 'keithley'):
            self.keithley.write_output_on(False)
            self.keithley.close()
        
            # clean up hardware object
            del self.keithley
        
        print('disconnected ',self.name)
        
    def write_range(self, _range, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):
        '''
        Writes value from combobox to the instrument.
        '''
        if volt_or_curr == 'VOLT':
            _range = self.v_ranges[_range]
        elif volt_or_curr == 'CURR':
            _range = self.i_ranges[_range]
        self.keithley.write_range(_range, sour_or_sens, volt_or_curr)
        
    def read_range(self, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):
        '''
        Reads range and changes combobox to match.
        '''
        _range = self.keithley.read_range(sour_or_sens, volt_or_curr)
        if volt_or_curr == 'VOLT':
            return self.v_ranges_inv[_range]
        elif volt_or_curr == 'CURR':
            return self.i_ranges_inv[_range]      
    
    def reset(self):
        self.keithley.reset()