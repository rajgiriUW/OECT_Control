'''

@author: Linda Taing
'''
from ScopeFoundry import HardwareComponent

try:
    from .keithley237_sourcemeter_interface import Keithley237SourceMeter
except Exception as err:
    print("Cannot load required modules for Keithley SourceMeter:", err)


class Keithley237SourceMeterComponent(HardwareComponent): #object-->HardwareComponent
    
    name = 'keithley237_sourcemeter'
    debug = False
    
    # SOURCE_MEASURE_DEFAULT = 'voltage/current'
    CURRENT_COMPLIANCE_DEFAULT = 0.1
    def setup(self):
        self.debug = True
        
        self.port = self.settings.New('port', dtype=str)
        
        # self.source_measure_choice = {'voltage/current': 0, 'current/voltage': 1} 
        # self.function_choice = {'DC': 0, 'sweep': 1}
        # self.range_choice = {'auto / auto': 0, '1nA / 1.1V': 1, '10nA / 11V': 2, '100nA / 110V': 3, '0.001mA / 1100V': 4,
                # '0.01mA / 1100V': 5, '0.1mA / 1100V': 6, '1mA / 1100V': 7, '10mA / 1100V': 8, '100mA / 1100V': 9}
        # self.filter_choice = {'disabled': 0, '2 readings': 1, '4 readings': 2, '8 readings': 3, '16 readings': 4, '32 readings': 5}
        # self.intg_time_choice = {'fast period': 0, 'medium period': 1, 'line cycle period @ 50 hZ': 2, 'line cycle period @ 60 hZ': 3}
        # self.sense_choice = {'local': 0, 'sense': 1}

        # self.source_measure_choice_inv = {v:k for k,v in self.source_measure_choice.items()}
        # self.function_choice_inv = {v:k for k,v in self.function_choice.items()}
        # self.range_choice_inv = {v:k for k,v in self.range_choice.items()}
        # self.filter_choice_inv = {v:k for k,v in self.filter_choice.items()}
        # self.intg_time_choice_inv = {v:k for k,v in self.intg_time_choice.items()}
        # self.sense_choice_inv = {v:k for k,v in self.sense_choice.items()} 
        
        # #set up settings in hardware panel
        # self.range_1100v = self.settings.New('1100V_range', bool, initial=False)
        # self.source_measure = self.settings.New('source_measure', str, choices = self.source_measure_choice.keys(), initial = SOURCE_MEASURE_DEFAULT)
        # self.function = self.settings.New('function', str, choice=self.function_choice.keys())
        # self.source_range = self.settings.New('source_range', str, choices=self.range_choice.keys())
        # self.source_level = self.settings.New('source_level')
        # self.voltage_compliance_level = self.settings.New('voltage_compliance_level', unit='V', si=True)
        self.current_compliance_level = self.settings.New('current_compliance_level', unit = 'A', si = True, initial = CURRENT_COMPLIANCE_DEFAULT)
        # self.compliance_measurement_range = self.settings.New('compliance_measurement_range', str, choices=self.range_choice.keys())
        # self.suppression = self.settings.New('suppression', bool)
        # self.dc_delay = self.settings.New('dc_delay', unit='s', si=True)
        # self.default_delay = self.settings.New('default_delay', bool)
        # self.filter = self.settings.New('filter', choices=self.filter_choice.key())
        # self.intg_time = self.settings.New('intg_time', choices=self.intg_time_choice.keys())
        # self.sense = self.settings.New('sense', choices=self.sense_choice.keys())


        
    def connect(self):
        if self.debug: print("connecting to keithley sourcemeter")
        
        # Open connection to hardware
        K = self.keithley = Keithley237SourceMeter(port=self.port.val, debug=self.debug_mode.val)
        K.write_compliance(CURRENT_COMPLIANCE_DEFAULT, 0)
        # def setup(self):
        #     K.write_1100V_range(True)
        #     K.write_source_and_function(0, 0)
        #     K.write_suppression(False)
        #     K.write_default_delay(True)


        # connect logged quantities - connects read, then write functions to settings
        # self.range_1100v.connect_to_hardware(lambda:K.read_1100V_range(), lambda on:K.write_100V_range(on))
        # self.source_measure.connect_to_hardware(lambda:K.read_source(), None)
        # self.function.connect_to_hardware(lambda:K.read_function(), None)
        # self.voltage_compliance_level.connect_to_hardware(None, lambda level:K.write_compliance(level, 0))

   
        
        print('connected to ',self.name)
        
    
    def disconnect(self):
        #disconnect hardware
        if hasattr(self, 'keithley'):
            self.keithley.write_output_on(False)
            self.keithley.close()
        
            # clean up hardware object
            del self.keithley
        
        print('disconnected ',self.name)
        
    def reset(self):
        self.keithley.reset()