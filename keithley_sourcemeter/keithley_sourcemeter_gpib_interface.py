'''
Created on 31.08.2014

@author: Benedikt Ursprung
'''

from __future__ import division
import numpy as np
import time
import matplotlib.pyplot as plt
import pymeasure
from pymeasure.instruments.keithley import *



class KeithleySourceMeter(object):
    '''
    python wrapper for Keythley Source meter unit.
    '''
    KeithleyBaudRate = 9600
    
    def __init__(self, port="GPIB0::22", debug=False):
        self.port = port
        self.debug = debug

        self.keithley = Keithley2400(port)
        # self.keithley.reset()
        # self.keithley.reset_buffer()
        self.measure_delay = 0
        time.sleep(0.1)        

    def close(self):
        self.keithley.shutdown()
        print('closed keithley')

    def source_V(self, V):
        self.keithley.source_voltage = V

    def source_I(self, I):
        self.keithley.source_current = I
        
    def reset(self):
        self.keithley.reset()
           
  
    def write_range(self, _range, source_or_measure = 'source', v_or_i = 'v'):
        '''
        determines the accuracy for measuring and sourcing
        Alternatively use setAutorange_A() which might be slower
        possible V ranges: 200 mV, 2 V, 20 V, 200V 
        possible I ranges: 100 nA, 1 uA, 10uA, ... 100 mA, 1 A, 1.5, 10 A (10 A only in pulse mode)
        refer to UserManual/Specification for accuracy
        '''
        if (source_or_measure == "source"):
            if (v_or_i == "v"):
                self.keithley.source_voltage_range = _range
            elif (v_or_i == "i"):
                self.keithley.source_current_range = _range
        elif (source_or_measure == "measure"):
            if (v_or_i == "v"):
                self.keithley.voltage_range = _range
            elif (v_or_i == "i"):
                self.keithley.current_range = _range


            
    def read_range(self,source_or_measure = 'source', v_or_i = 'v'):
        if (source_or_measure == "source"):
            if (v_or_i == "v"):
                return self.keithley.source_voltage_range
            elif (v_or_i == "i"):
                return self.keithley.source_current_range
        elif (source_or_measure == "measure"):
            if (v_or_i == "v"):
                return self.keithley.voltage_range
            elif (v_or_i == "i"):
                return self.keithley.current_range
        
    def read_V(self):
        try:
            return self.keithley.voltage
        except:
            return 0

    def read_I(self):
        try:
            return self.keithley.current  
        except:
            return 0

    def write_NPLC(self, n):
        '''
        NPLC is number of power line cycles.  DC Voltage, DC Current, and Resistance measurement resolution, 
        accuracy is reduced by power line induced AC noise.  Using NPLC of 1 or greater increases AC noise 
        integration time, and increases measurement resolution and accuracy, however the trade-off 
        is slower measurement rates. (sets ADC_integration_time to NPLC*0.1/60 sec)
        '''
        self.keithley.current_nplc = n
        
    def read_NPLC(self):
        return self.keithley.current_nplc
            
    def prepare_buffer(self, channel = 'a', buffer_n = '1'):
        # self.send( 'smu{}.nvbuffer{}.clear()'.format(channel, buffer_n) )
        # self.send( 'smu{}.nvbuffer{}.appendmode = 1'.format(channel, buffer_n))
        self.keithley.reset_buffer()

        
    # def measureIV_A(self, N, Vmin, Vmax, NPLC=1, delay=0,channel='a'):
    #     """
    #     sweeps voltage from Vmin to Vmax in N steps and measures current using channel A
    #     returns I,V arrays, where I is measured, V is sourced
    #     NPLC = 1 sets integration time in Keitheley ADC to 0.1/60 sec
    #         Note: lowering NPLC increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)
    #     delay [sec]: delay between measurements
    #     """
        
    #     self.send('format.data = format.ASCII')
        
    #     # Buffer
    #     self.prepare_buffer(channel) 
        
    #     # collect source values
    #     self.send( 'smu{}.nvbuffer{}.collectsourcevalues = 1'.format(channel, '1'))

    #     # Timestamps (if needed uncomment lowest section)       
    #     #self.send('smua.nvbuffer1.collecttimestamps = 1')
    #     #self.send('smua.nvbuffer1.timestampresolution=0.000001')

    #     # Speed configurations: 
    #     # autozero = 0 = off no significant speed boost
    #     # deleay/delayfactor seem to be 0 by default
    #     # nplc really does boost steed: nplc = 0.1 sets integration time in Keitheley ADC to 0.1/60
    #     #     Note: lowering nplc increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)   
    #     self.write_NPLC(NPLC, 'a')   
    #     self.write_measure_delay(delay)
        
    #     # Make N measurements  
    #     dV = str(float(Vmax-Vmin)/(N-1))
    #     self.send( 'smu{}.measure.count = 1'.format(channel))
    #     self.send(('for v = 0, '+str(N)+'do smu{}.source.levelv = v*'+dV+'+'+str(Vmin)+' smu{}.measure.i(smu{}.nvbuffer1) end').format(channel) )
    #     time.sleep( N*(delay+0.05) ) # wait for the measurement to be completed 
    #     # read out measured currents
    #     StrI = self.ask('printbuffer(1, smu{}.nvbuffer1.n, smu{}.nvbuffer1.readings)'.format(channel))
    #     if self.debug: print("I:", repr(StrI))
    #     print(StrI.split(','))
    #     I = np.array(StrI.split(','), dtype = np.float32)
        
    #     # read out sourced voltages        
    #     StrV = self.ask('printbuffer(1, smu{}.nvbuffer1.n, smu{}.nvbuffer1.sourcevalues)'.format(channel))   
    #     if self.debug: print("V:", repr(StrV))
    #     V = np.array(StrV.split(','), dtype = np.float32)
    #     return I,V          

    #     #Strt = self.ask('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.timestamps)')
    #     #t = np.array(Strt.split(','),dtype = np.float32)  
    #     #return t,I 

    
    # def measureI_A(self, N, NPLC=1, delay=0):
    #     """
    #     takes N current measurements and returns them as ndarray
    #     delay [sec]: delay between measurements
    #     """
        
    #     self.send('format.data = format.ASCII')
        
    #     # Buffer
    #     self.send('smua.nvbuffer1.clear()')
    #     self.send('smua.nvbuffer1.appendmode = 1')
    #     self.send('smua.measure.count = 1')
    #     #self.ser.write('smua.nvbuffer2.appendmode = 1\r\n')        
    #     #self.ser.write('smua.nvbuffer2.clear()\r\n')            

    #     # Timestamps (if needed uncomment lowest section)       
    #     #self.ser.write('smua.nvbuffer1.collecttimestamps = 1\r\n')
    #     #self.ser.write('smua.nvbuffer1.timestampresolution=0.000001\r\n')

    #     # Speed configurations: 
    #     # autozero = 0 = off no significant speed boost
    #     # deleay/delayfactor seem to be 0 by default
    #     #     Note: lowering nplc increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)   
    #     self.write_NPLC(NPLC, 'a')   
    #     self.write_measure_delay(delay)
    #     #self.send('smua.measure.delayfactor = 0')
    #     #self.send('smua.measure.autozero = 0')
        
    #     # Make N measurements
          
    #     self.send('for v = 1, '+str(N)+'do smua.measure.i(smua.nvbuffer1) end')
    #     # read out measured currents
    #     StrI = self.ask('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
    #     return np.array(StrI.split(','),dtype = np.float32)
    
    #     #Strt = self.ask('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.timestamps)')
    #     #t = np.array(Strt.split(','),dtype = np.float32)  
    #     #return t,I 


    def setRanges_A(self,Vmeasure,Vsource,Imeasure,Isource):
        '''
        set all ranges on channel A, to set individual channels use self.write_range()
        The range determines the accuracy for measuring and sourcing
        Alternatively use setAutorange_A() which might be slower
            possible V ranges: 200 mV, 2 V, 20 V, 200V 
            possible I ranges: 100 nA, 1 uA, 10uA, ... 100 mA, 1 A, 1.5, 10 A (10 A only in pulse mode)
        refer to UserManual/Specification for accuracy
        '''
        self.write_range(Vmeasure,'measure', 'v')
        self.write_range(Vsource,'source', 'v')
        self.write_range(Imeasure,'measure', 'i')
        self.write_range(Isource,'source', 'i')
        
if __name__ == '__main__':
    
    K1 = KeithleySourceMeter()

    # K1.reset('a')
    
    #K1.setRanges_A(Vmeasure=2,Vsource=2,Imeasure=0.1,Isource=0.1)
    #K1.setAutoranges_A()
    K1.setV_A(V=0)
    
    K1.switchV_A_on()

    
    K1.setRanges_A(Vmeasure=2,Vsource=2,Imeasure=1,Isource=1)    
    I,V = K1.measureIV_A(20, Vmin=-1, Vmax = 1, KeithleyADCIntTime=1, delay=0)
    plt.plot(I,V)
    plt.show()
    
    K1.switchV_A_off()         
    K1.close()

    pass