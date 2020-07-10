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
    NPLC_DEFAULT = 1

    def setup(self):
        self.debug = True
        
        self.port = self.settings.New('port', dtype=str)
        
        # Ranges for Models 2611B/2612B/2614B
        # self.v_ranges = {'200 mV':0.2,'2 V':2, '20 V':20, '200 V':200}
        # self.i_ranges = {'100 nA':100e-9, 
        #                  '1 uA':1e-6, '10 uA':10e-6, '100 uA':100e-6, 
        #                  '1 mA':1e-3, '10 mA':10e-3, '100 mA':100e-3,
        #                  '1 A':1, '1.5 A':1.5, '10 A':10}

        
        # self.v_ranges = {'210 mV':0.21,'2 V':2.1, '20 V':21, '200 V':210}

        self.i_ranges = {'1 uA':1.05e-6, '10 uA':1.05e-5, '100 uA':1.05e-4, 
                         '1 mA':1.05e-3, '10 mA':1.05e-2, '100 mA':1.05e-1,
                         '1 A':1.05}
        # self.v_ranges_inv = {v:k for k,v in self.v_ranges.items()} 
        self.i_ranges_inv = {v:k for k,v in self.i_ranges.items()}
        
        #set up settings in hardware panel
        # self.voltage = self.V_a = self.settings.New('V_a', unit='V', ro=True, si=True)
        # self.current = self.I_a = self.settings.New('I_a', unit='A', ro=True, si=True)
        
        # self.source_V_a = self.settings.New('source_V_a', unit='V', spinbox_decimals = 6)
        # self.source_I_a = self.settings.New('source_I_a', unit='A', spinbox_decimals = 6)
                
        # self.source_V_a_range = self.settings.New('source_V_a_range', str, choices = self.v_ranges.keys())
        # self.measure_V_a_range = self.settings.New('measure_V_a_range', str, choices = self.v_ranges.keys())
        # self.source_I_a_range = self.settings.New('source_I_a_range', str, choices = self.i_ranges.keys())
        # self.measure_I_a_range = self.settings.New('measure_I_a_range', str, choices = self.i_ranges.keys())
            
            
        # self.output_a_on = self.settings.New('output_a_on', bool, initial=False)
        # self.NPLC_a = self.settings.New('NPLC_a', int)
        # self.measure_delay_time_a = self.settings.New('measure_delay_time_a', float, spinbox_decimals = 3, unit='sec')
        
        # self.is_a_measuring = self.settings.New('is_measuring', bool, initial = False, ro=True)
        self.autozero = self.settings.New('autozero', str, choices = {'on', 'off', 'once'}, initial = self.AUTOZERO_DEFAULT)
        self.autorange = self.settings.New('autorange', bool, initial = self.AUTORANGE_DEFAULT)
        self.source_mode = self.settings.New('source_mode', str, choices = {'VOLT', 'CURR'}, initial = self.SOURCE_MODE_DEFAULT)
        self.manual_range = self.settings.New('manual_range', str, choices = self.i_ranges.keys(), initial = self.MANUAL_RANGE_DEFAULT)
        self.current_compliance = self.settings.New('current_compliance', unit='A', initial = self.CURRENT_COMPLIANCE_DEFAULT)
        self.NPLC_a = self.settings.New('NPLC_a', initial = self.NPLC_DEFAULT)
        self.is_a_measuring = self.settings.New('is_measuring', bool, initial = False, ro=True)
        
    def connect(self):
        if self.debug: print("connecting to keithley sourcemeter")
        
        # Open connection to hardware and write default values
        K = self.keithley = Keithley2400SourceMeter(port=self.port.val, debug=self.debug_mode.val)
        K.write_autozero(self.AUTOZERO_DEFAULT)
        K.write_source_mode(self.SOURCE_MODE_DEFAULT)
        #write current range at measurement setup - depends on if autorange is selected
        K.write_current_compliance(self.CURRENT_COMPLIANCE_DEFAULT)
        K.write_NPLC(self.NPLC_DEFAULT)

        #


        # connect logged quantities - connects read, then write functions to settings
        # self.V_a.connect_to_hardware(lambda:K.read_V(),None)
        # self.I_a.connect_to_hardware(lambda:K.read_I(),None)
        
        # self.source_I_a.connect_to_hardware(None,lambda I:K.source_I(I))
        # self.source_V_a.connect_to_hardware(None,lambda V:K.source_V(V))
 
        # self.source_V_a_range.connect_to_hardware(lambda:self.read_range('SOUR', 'VOLT'), 
        #             lambda _range:self.write_range(_range,'SOUR', 'VOLT'))
        # self.measure_V_a_range.connect_to_hardware(lambda:self.read_range('SENS', 'VOLT'), 
        #             lambda _range:self.write_range(_range,'SENS','VOLT'))
        # self.source_I_a_range.connect_to_hardware(lambda:self.read_range('SOUR', 'CURR'), 
        #             lambda _range:self.write_range(_range,'SOUR','CURR'))
        # self.measure_I_a_range.connect_to_hardware(lambda:self.read_range('SENS', 'CURR'), 
        #             lambda _range:self.write_range(_range,'SENS','CURR'))
        
        # self.output_a_on.connect_to_hardware(K.read_output_on, 
        #             lambda on:K.write_output_on(on))
        
        # self.NPLC_a.connect_to_hardware(lambda: K.read_NPLC(),
        #             lambda time:K.write_NPLC(time))
        # self.measure_delay_time_a.connect_to_hardware(lambda: K.read_measure_delay(),
        #             lambda delay:K.write_measure_delay(delay))
        
        self.is_a_measuring.connect_to_hardware(read_func=K.read_is_measuring)        
        
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