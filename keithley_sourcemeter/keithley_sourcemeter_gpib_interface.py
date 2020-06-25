'''
Created on 31.08.2014

@author: Benedikt Ursprung
'''

from __future__ import division
import numpy as np
import time
import matplotlib.pyplot as plt
import serial
import pyvisa as pv


class KeithleySourceMeter(object):
    '''
    python wrapper for Keythley Source meter unit.
    '''
    KeithleyBaudRate = 9600
    
    def __init__(self, port="GPIB0::22::INSTR", debug=False):
        self.port = port
        self.debug = debug
        
        # self.ser = serial.Serial(port=self.port, baudrate=self.KeithleyBaudRate, stopbits=1, xonxoff=0, rtscts=0, timeout=5.0)#,         
        # self.ser.flush()
        self.resource_manager = pv.ResourceManager()
        self.keithley = self.resource_manager.open_resource(port)
        self.keithley.read_termination = '\r'
        # self.keithley.read_termination = '\n'
        # self.keithley.read_termination = '\r\n'
        # self.keithley.read_termination = None

        # self.keithley.write_termination = '\r'
        # self.keithley.write_termination = '\n'
        # self.keithley.write_termination = '\r\n'
        self.keithley.write_termination = None

        self.reset()
        time.sleep(0.1)        

    def ask(self, cmd):
        # self.keithley.write(cmd)
        # resp = self.keithley.read()
        resp = self.keithley.query(cmd)
        if self.debug: print('response')
        return resp
    
    def send(self, cmd):
        # cmd += '\r\n'
        if self.debug: print('send', cmd)
        self.keithley.write(cmd)       

    def close(self):
        self.keithley.close()
        self.resource_manager.close()
        print('closed keithley')

    def source_V(self, V, mode = 'DC'):
        # self.send('smu{0}.source.func = smu{0}.OUTPUT_{1}VOLTS'.format(channel, mode))        
        # self.send('smu{0}.source.levelv = {1}'.format(channel, V))
        self.keithley.send(":SOUR:VOLT:LEV " + str(V))

    def source_I(self, I, mode = 'DC'):
        # self.send('smu{0}.source.func = smu{0}.OUTPUT_{1}AMPS'.format(channel,mode))        
        # self.send('smu{}.source.leveli = {}'.format(channel, I))
        self.keithley.send(":SOUR:CURR:LEV " + str(I))
        
    def reset(self):
        self.keithey.send("status:queue:clear;*RST;:stat:pres;:*CLS;")
           
    def write_range(self, _range, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):
        '''
        determines the accuracy for measuring and sourcing
        Alternatively use setAutorange_A() which might be slower
            possible V ranges: 200 mV, 2 V, 20 V, 200V 
            possible I ranges: 100 nA, 1 uA, 10uA, ... 100 mA, 1 A, 1.5, 10 A (10 A only in pulse mode)
        refer to UserManual/Specification for accuracy
        '''
        # self.send( 'smu{0}.{1}.range{2} = {3}'.format(channel,source_or_measure,v_or_i,_range) )
        self.send(":{0}:{1}:RANG:AUTO 0;:{0}:{1}:RANG {2}".format(sour_or_sens, volt_or_curr, _range).upper())
        # ":SOUR:CURR:RANG:AUTO 0;:SOUR:CURR:RANG %g" src current range
        # ":SOUR:VOLT:RANG:AUTO 0;:SOUR:VOLT:RANG %g" src voltage range
        # ":SENS:CURR:RANG:AUTO 0;:SENS:CURR:RANG %g" meas current range
        # ":SENS:VOLT:RANG:AUTO 0;:SENS:VOLT:RANG %g" meas voltage range
        
            
    def read_range(self, sour_or_sens = 'SOUR', volt_or_curr = 'VOLT'):            
        # resp = self.ask('print(smu{0}.{1}.range{2})'.format(channel,source_or_measure,v_or_i) )
        resp = self.ask(":{0}:{1}:RANG?".format(sour_or_sens, volt_or_curr))
        return float(resp)

    #comment out this function after fixing hardware-setting connection
    def read_source_volt_range(self):
        resp = self.ask(":SOUR:VOLT:RANG?")
        return float(resp)

        
    # def write_autorange_on(self, on = True, source_or_measure = 'source', v_or_i = 'v', channel = 'a'):
    #     _on = {True:'AUTORANGE_ON',False:'AUTORANGE_OFF'}[on]
    #     self.send( 'smu{0}.{1}.autorange{2} = smu{0}.{3}'.format(channel,source_or_measure,v_or_i, _on) )

    # def read_autorange(self,source_or_measure = 'source', v_or_i = 'v', channel = 'a'):
    #     resp = self.ask('print(smu{0}.{1}.autorange{2})'.format(channel,source_or_measure,v_or_i))
    #     return bool(float(resp))
        
    def write_output_on(self, on = True):
        # s = {True:'OUTPUT_ON',False:'OUTPUT_OFF'}[on]
        # self.send('smu{0}.source.output = smu{0}.{1}'.format(channel,s))
        s = {True:'OUTPUT ON',False:'OUTPUT OFF'}[on]
        self.send(s)

    def read_output_on(self):
        # resp = self.ask('print(smu{}.source.output)'.format(channel))
        resp = self.ask("OUTPut?")
        return bool(float(resp))
      
    def read_V(self):
        try:
            self.measure_voltage()
            resp = self.ask(":READ?")
            return float(resp)
        except:
            return 0

    def measure_voltage(self, nplc=1, voltage=21.0, auto_range=True):
        """ Configures the measurement of voltage.
        :param nplc: Number of power line cycles (NPLC) from 0.01 to 10
        :param voltage: Upper limit of voltage in Volts, from -210 V to 210 V
        :param auto_range: Enables auto_range if True, else uses the set voltage
        """
        self.send(":SENS:FUNC 'VOLT';"
                   ":SENS:VOLT:NPLC %f;:FORM:ELEM VOLT;" % nplc)
        if auto_range:
            self.send(":SENS:VOLT:RANG:AUTO 1;")
        else:
            self.write_range(voltage, "SENS", "VOLT")
            # self.voltage_range = voltage
        # self.check_errors()
    
    def read_I(self):
        # resp = self.ask('print(smu{}.measure.i())'.format(channel))
        try:
            self.measure_current()
            resp = self.ask(":READ?")
            return float(resp)
        except:
            return 0

    def measure_current(self, nplc=1, current=1.05e-4, auto_range=True):
        """ Configures the measurement of current.
        :param nplc: Number of power line cycles (NPLC) from 0.01 to 10
        :param current: Upper limit of current in Amps, from -1.05 A to 1.05 A
        :param auto_range: Enables auto_range if True, else uses the set current
        """
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
        self.write(":SENS:CURR:NPLC " + str(n))
        # self.send('smu{}.measure.nplc = {}'.format(channel, n))
        
    def read_NPLC(self):
        # resp = self.ask('print(smu{}.measure.nplc)'.format(channel))
        resp = self.ask(":SENS:CURR:NPLC?")
        return int(float(resp) )

    def write_source_delay(self, delay):
        self.send(':SOUR:DEL? ' + str(delay))
    
    def read_source_delay(self):
        resp = self.ask(":SOUR:DEL?")
        return float(resp)
    
    def write_measure_delay(self, delay):
        '''
        delay [sec]: delay between measurements
        '''
        # self.send('smu{}.measure.delay = {}'.format(channel, delay))
        self.send(':TRIG:SEQ:DEL ' + str(delay))

    def read_measure_delay(self):
        # resp = self.ask('print(smu{}.measure.delay)'.format(channel))
        resp = self.ask(':TRIG:SEQ:DEL?')
        return float(resp)

        
    # def prepare_buffer(self, buffer_n = '1'):
    #     # self.send( 'smu{}.nvbuffer{}.clear()'.format(channel, buffer_n) )
    #     # self.send( 'smu{}.nvbuffer{}.appendmode = 1'.format(channel, buffer_n))
    #     """ Resets the buffer. """
    #     self.keithley.write(":STAT:PRES;*CLS;:TRAC:CLEAR;:TRAC:FEED:CONT NEXT;")



    def read_is_measuring(self, channel = 'a'):
        resp = self.ask('print(status.measurement.instrument.smu{}.condition)'.format(channel))
        return bool(float(resp))
        
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

    # def getI_A(self):
    #     """
    #     DEPRECATED use read_I('a') gets a single current measurement
    #     """
    #     return self.read_I('a')

    # def getV_A(self):
    #     """
    #     DEPRECATED use read_V('a') gets a single voltage measurement, 
    #     """
    #     return self.read_V('a')

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

    def reset(self):
        self.send("status:queue:clear;*RST;:stat:pres;:*CLS;")
        
    # def setAutoranges_A(self):
    #     '''
    #     sets all ranges on channel A to auto, individual ranges can be set to auto with self.write_auto_range
    #     Alternatively use setRanges_A(Vmeasure,Vsource,Imeasure,Isource) 
    #     to set ranges manually, which might be faster
    #     '''
    #     self.write_autorange_on(True, 'source', 'v', 'a')
    #     self.write_autorange_on(True, 'source', 'i', 'a')
    #     self.write_autorange_on(True, 'measure', 'v', 'a')
    #     self.write_autorange_on(True, 'measure', 'i', 'a')

    # def setV_A(self,V):
    #     """
    #     DEPRECIATED set DC voltage on channel A and turns it on
    #     """
    #     self.source_V(V, 'a', 'DC')
        
    # def resetA(self):
    #     #depreciated 
    #     self.reset(channel='a')


# if __name__ == '__main__':
    
#     K1 = KeithleySourceMeter()

#     K1.reset('a')
    
#     #K1.setRanges_A(Vmeasure=2,Vsource=2,Imeasure=0.1,Isource=0.1)
#     #K1.setAutoranges_A()
#     K1.setV_A(V=0)
    
#     K1.switchV_A_on()

    
#     K1.setRanges_A(Vmeasure=2,Vsource=2,Imeasure=1,Isource=1)    
#     I,V = K1.measureIV_A(20, Vmin=-1, Vmax = 1, KeithleyADCIntTime=1, delay=0)
#     plt.plot(I,V)
#     plt.show()
    
#     K1.switchV_A_off()         
#     K1.close()

#     pass