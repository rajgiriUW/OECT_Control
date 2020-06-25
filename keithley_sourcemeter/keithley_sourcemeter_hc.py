'''
Created on 31.08.2014

@author: Benedikt
'''
from ScopeFoundry import HardwareComponent

try:
    from .keithley_sourcemeter_gpib_interface import KeithleySourceMeter
except Exception as err:
    print("Cannot load required modules for Keithley SourceMeter:", err)


class KeithleySourceMeterComponent(HardwareComponent): #object-->HardwareComponent
    
    name = 'keithley_sourcemeter'
    debug = False
    
    def setup(self):
        self.debug = True
        
        self.port = self.settings.New('port', dtype=str, initial='COM21')
        
        # Ranges for Models 2611B/2612B/2614B
        self.v_ranges = {'200 mV':0.2,'2 V':2, '20 V':20, '200 V':200}
        self.i_ranges = {'100 nA':100e-9, 
                         '1 uA':1e-6, '10 uA':10e-6, '100 uA':100e-6, 
                         '1 mA':1e-3, '10 mA':10e-3, '100 mA':100e-3,
                         '1 A':1, '1.5 A':1.5, '10 A':10}
        self.v_ranges_inv = {v:k for k,v in self.v_ranges.items()} 
        self.i_ranges_inv = {v:k for k,v in self.i_ranges.items()}
        
        self.voltage = self.V_a = self.settings.New('V_a', unit='V', ro=True, si=True)
        self.current = self.I_a = self.settings.New('I_a', unit='A', ro=True, si=True)
        
        self.source_V_a = self.settings.New('source_V_a', unit='V', spinbox_decimals = 6)
        self.source_I_a = self.settings.New('source_I_a', unit='A', spinbox_decimals = 6)
                
        self.source_V_a_range = self.settings.New('source_V_a_range')#, str, choices = self.v_ranges.keys())
        self.measure_V_a_range = self.settings.New('measure_V_a_range')#, str, choices = self.v_ranges.keys())
        self.source_I_a_range = self.settings.New('source_I_a_range')#, str, choices = self.i_ranges.keys())
        self.measure_I_a_range = self.settings.New('measure_I_a_range')#, str, choices = self.i_ranges.keys())
            
            
        self.output_a_on = self.settings.New('output_a_on', bool, initial=False)
        self.NPLC_a = self.settings.New('NPLC_a', int)
        self.delay_time_a = self.settings.New('delay_time_a', float, spinbox_decimals = 3, unit='sec')
        
        self.is_a_measuring = self.settings.New('is_measuring', bool, initial = False, ro=True)
        
        
        
    def connect(self):
        if self.debug: print("connecting to keithley sourcemeter")
        
        # Open connection to hardware
        K = self.keithley = KeithleySourceMeter(port=self.port.val, debug=self.debug_mode.val)
        print(K.ask(":SOUR:VOLT:RANG?")) #test reading

        # connect logged quantities
        self.V_a.connect_to_hardware(lambda:K.read_V(),None)
        self.I_a.connect_to_hardware(lambda:K.read_I(),None)
        
        self.source_I_a.connect_to_hardware(None,lambda I:K.source_I(I))
        self.source_V_a.connect_to_hardware(None,lambda V:K.source_V(V))

            
        #testing code - pressing "read from hardware" should update source_V_a_range setting in the panel
        self.source_V_a_range.connect_to_hardware(lambda:K.read_source_volt_range(), None)

        #uncomment 71-88 after fixing hardware-setting connection 
        # self.source_V_a_range.connect_to_hardware(lambda:self.read_range('SOUR', 'VOLT'), 
        #             lambda _range:self.write_range(_range,'SOUR', 'VOLT'))
        # self.measure_V_a_range.connect_to_hardware(lambda:self.read_range('SENS', 'VOLT'), 
        #             lambda _range:self.write_range(_range,'SENS','VOLT'))
        # self.source_I_a_range.connect_to_hardware(lambda:self.read_range('SOUR', 'CURR'), 
        #             lambda _range:self.write_range(_range,'SENS','CURR'))
        # self.measure_I_a_range.connect_to_hardware(lambda:self.read_range('SENS', 'CURR'), 
        #             lambda _range:self.write_range(_range,'SENS','CURR'))
        
        # self.output_a_on.connect_to_hardware(K.read_output_on, 
        #             lambda on:K.write_output_on(on))
        
        # self.NPLC_a.connect_to_hardware(lambda: K.read_NPLC(),
        #             lambda time:K.write_NPLC(time))
        # self.delay_time_a.connect_to_hardware(lambda: K.read_measure_delay(),
        #             lambda delay:K.write_measure_delay(delay))
        
        # self.is_a_measuring.connect_to_hardware(read_func=K.read_is_measuring)        
        
        print('connected to ',self.name)
        
    
    def disconnect(self):
        #disconnect hardware
        if hasattr(self, 'keithley'):
            self.keithley.write_output_on(False)
            self.keithley.close()
        
            # clean up hardware object
            del self.keithley
        
        print('disconnected ',self.name)
        
    # def write_range(self, _range, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):
    #     if volt_or_curr == 'VOLT':
    #         _range = self.v_ranges[_range]
    #     elif volt_or_curr == 'CURR':
    #         _range = self.i_ranges[_range]
    #     self.keithley.write_range(_range, sour_or_sens, volt_or_curr)
        
    # def read_range(self, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):
    #     _range = self.keithley.read_range(sour_or_sens, volt_or_curr)
    #     if volt_or_curr == 'VOLT':
    #         return self.v_ranges_inv[_range]
    #     elif volt_or_curr == 'CURR':
    #         return self.i_ranges_inv[_range]      
        
    def reset(self):
        self.keithley.reset()

        