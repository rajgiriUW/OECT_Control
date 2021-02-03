'''

@author: Linda Taing
'''

from __future__ import division
import numpy as np
import time
import pyvisa as pv


class Keithley2400SourceMeter(object):
    '''
    python wrapper for Keythley Source meter unit.
    '''
    KeithleyBaudRate = 9600
    
    def __init__(self, port, debug=False):
        self.port = port
        self.debug = debug
        
        self.resource_manager = pv.ResourceManager()
        self.keithley = self.resource_manager.open_resource(port)

        self.reset()
        time.sleep(0.1)        

    def ask(self, cmd):
        '''
        Writes specified to the device and returns the response.
        '''
        resp = self.keithley.query(cmd)
        if self.debug: print('response')
        return resp

    
    def send(self, cmd):
        '''
        Writes specified commands to the device.
        '''
        if self.debug: print('send', cmd)
        self.keithley.write(cmd)       

    def close(self):
        if (self.read_output_on): self.write_output_on(False) #disable output
        self.keithley.close()
        self.resource_manager.close()
        print('closed keithley')

    def source_V(self, V, mode = 'DC'):
        '''
        Set source voltage.
        '''
        self.send(":SOUR:VOLT:LEV %g" % (V))

    def source_I(self, I, mode = 'DC'):
        '''
        Set source current.
        '''
        self.send(":SOUR:CURR:LEV %g" % (I))
        
    def reset(self):
        '''
        Reset to factory defaults.
        '''
        self.send("status:queue:clear;*RST;:stat:pres;:*CLS;")
           
    def write_range(self, _range, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):
        '''
        determines the accuracy for measuring and sourcing
        Alternatively use setAutorange_A() which might be slower
            possible V ranges: 200 mV, 2 V, 20 V, 200V 
            possible I ranges: 100 nA, 1 uA, 10uA, ... 100 mA, 1 A, 1.5, 10 A (10 A only in pulse mode)
        refer to UserManual/Specification for accuracy.
        SOUR corresponds to source; SENS corresponds to measurement.
        VOLT corresponds to voltage; CURR corresponds to current.
        '''
        self.send(":{0}:{1}:RANG:AUTO 0;:{0}:{1}:RANG {2}".format(sour_or_sens, volt_or_curr, _range).upper())
        
            
    def read_range(self, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):            
        '''
        Return set range.
        '''
        resp = self.ask(":{0}:{1}:RANG?".format(sour_or_sens, volt_or_curr))
        return float(resp)
                
    def write_output_on(self, on = True):
        '''
        Enables/disables source output.
        '''
        s = {True:'OUTPUT ON',False:'OUTPUT OFF'}[on]
        self.send(s)


    def read_output_on(self):
        '''
        Returns whether source output is disabled.
        '''
        resp = self.ask("OUTPut?")
        return bool(float(resp))
      
    def read_V(self):
        '''
        Configure device to read voltage and return voltage reading.
        '''
        self.measure_voltage()
        resp = self.ask(":READ?")
        return float(resp)

    def measure_voltage(self, nplc=1, voltage=21.0, auto_range=True):
        """ Configures the measurement of voltage.
        :param nplc: Number of power line cycles (NPLC) from 0.01 to 10
        :param voltage: Upper limit of voltage in Volts, from -210 V to 210 V
        :param auto_range: Enables auto_range if True, else uses the set voltage
        """
        if (self.read_output_on() == False): self.write_output_on()
        self.send(":SENS:FUNC 'VOLT';"
                   ":SENS:VOLT:NPLC %f;:FORM:ELEM VOLT;" % nplc)
        if auto_range:
            self.send(":SENS:VOLT:RANG:AUTO 1;")
        else:
            self.write_range(voltage, "SENS", "VOLT")
    
    def read_I(self):
        '''
        Configure device to read current and return current reading.
        '''
        self.measure_current()
        resp = self.ask(":READ?")
        return float(resp)


    def measure_current(self, nplc=1, current=1.05e-4, auto_range=True):
        """ Configures the measurement of current.
        :param nplc: Number of power line cycles (NPLC) from 0.01 to 10
        :param current: Upper limit of current in Amps, from -1.05 A to 1.05 A
        :param auto_range: Enables auto_range if True, else uses the set current
        """
        if (self.read_output_on() == False): self.write_output_on()
        self.send(":SENS:FUNC 'CURR';"
                   ":SENS:CURR:NPLC %f;:FORM:ELEM CURR;" % nplc)
        if auto_range:
            self.send(":SENS:CURR:RANG:AUTO 1;")
        else:
            self.write_range(current, "SENS", "CURR")

    def write_NPLC(self, n):
        '''
        NPLC is number of power line cycles.  DC Voltage, DC Current, and Resistance measurement resolution, 
        accuracy is reduced by power line induced AC noise.  Using NPLC of 1 or greater increases AC noise 
        integration time, and increases measurement resolution and accuracy, however the trade-off 
        is slower measurement rates. (sets ADC_integration_time to NPLC*0.1/60 sec)
        '''
        self.send(":SENS:CURR:NPLC %f" % (n))
        
    def read_NPLC(self):
        resp = self.ask(":SENS:CURR:NPLC?")
        return int(float(resp) )
    
    def write_measure_delay(self, delay):
        '''
        delay [sec]: delay between measurements
        '''
        self.send(':TRIG:SEQ:DEL %g' % (delay))

    def read_measure_delay(self):
        resp = self.ask(':TRIG:SEQ:DEL?')
        return float(resp)

    def write_autozero(self, on):
        s = {'on': 1, 'off': 0, 'once': 'once'}[on]
        self.send(':SYST:AZER:STAT ' + str(s))

    def write_source_mode(self, volt_or_curr):
        self.send(':SOUR:FUNC:MODE %s' % (volt_or_curr.upper()))
        self.send(':SOUR:%s:MODE FIX' % (volt_or_curr.upper()))
        self.send(':SOUR:%s:RANG:AUTO 1' % (volt_or_curr.upper()))

    def write_current_compliance(self, i_compliance):
        self.send(':SENS:CURR:PROT %g' % i_compliance)

    def write_voltage_compliance(self, v_compliance):
        self.send(':SENS:VOLT:PROT %g' % v_compliance)

    def read_is_measuring(self, channel = 'a'):
        resp = self.ask("status:queue?;")[0]
        return bool(float(resp))
          
    def setRanges_A(self,Vmeasure,Vsource,Imeasure,Isource):
        '''
        set all ranges on channel A, to set individual channels use self.write_range()
        The range determines the accuracy for measuring and sourcing
        Alternatively use setAutorange_A() which might be slower
            possible V ranges: 200 mV, 2 V, 20 V, 200V 
            possible I ranges: 100 nA, 1 uA, 10uA, ... 100 mA, 1 A, 1.5, 10 A (10 A only in pulse mode)
        refer to UserManual/Specification for accuracy
        '''
        self.write_range(Vmeasure,'SENS', 'VOLT', 'a')
        self.write_range(Vsource,'SOUR', 'VOLT', 'a')
        self.write_range(Imeasure,'SENS', 'CURR', 'a')
        self.write_range(Isource,'SENS', 'CURR', 'a')