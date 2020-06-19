'''
Created on Sep 8, 2014

@author: Edward Barnard and Benedikt Ursprung
'''

from ScopeFoundry  import Measurement, LQRange, h5_io
import time
import numpy as np
import pyqtgraph as pg

class PhotocurrentIVMeasurement(Measurement):
    """
    Can be tuned to perform a fast IV measurement. Use fast delay and adc_int_time and disable autoranges
    """
        
    name = "photocurrrent_iv"
    
    def setup(self):

        # logged quantities
<<<<<<< HEAD
        kwargs = {'unit':'V', 'vmin':-5, 'vmax':5, 'spinbox_decimals':3}
        self.voltage_range = self.settings.New_Range('source_voltage',  initials = [-1, 1, 0.1], 
                                                     include_sweep_type = False, **kwargs)

        self.save_h5 = self.settings.New('save_h5', bool, initial = True)
        
=======
        V_lqs_params = dict(unit='V', vmin=-5, vmax=5, spinbox_decimals = 3)
        self.source_voltage_min = self.settings.New("source_voltage_min", initial = -1, **V_lqs_params)
        self.source_voltage_max = self.settings.New("source_voltage_max", initial = +1, **V_lqs_params)
        self.source_voltage_delta = self.settings.New("source_voltage_delta", initial=0.1, **V_lqs_params)
        self.source_voltage_steps = self.settings.New("source_voltage_steps", int, initial = 10, vmin=1, vmax=1000,)
        self.acquisition_time = self.settings.New("acquisition_time", initial = 0.0, unit='sec')
        
        self.voltage_range = LQRange(self.source_voltage_min, self.source_voltage_max, self.source_voltage_delta, self.source_voltage_steps)

>>>>>>> e5493a783f6e78e2ea9555b6c40b3825d58a65a6
    def setup_figure(self):
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))
        self.plot = self.graph_layout.addPlot(title="Photocurrent IV")
        self.plot_line = self.plot.plot()
        self.plot.showGrid(True,True)
        self.plot.setLabel('left', 'current', 'A')
        self.plot.setLabel('bottom', 'voltage', 'V')
<<<<<<< HEAD
=======
        
>>>>>>> e5493a783f6e78e2ea9555b6c40b3825d58a65a6

    def run(self):
        #Hardware
        K = self.app.hardware['keithley_sourcemeter']
        KS = K.settings
        
        self.keithley = K.keithley
        
        K.reset('a')
        KS.output_a_on.update_value(True)
        
        #measure IV
        self.Iarray,self.Varray = self.keithley.measureIV_A(self.source_voltage_steps.val, 
                             Vmin = self.source_voltage_min.val, 
                             Vmax = self.source_voltage_max.val, 
<<<<<<< HEAD
                             KeithleyADCIntTime=KS['NPLC_a'], 
                             delay=KS['delay_time_a'])
=======
                             KeithleyADCIntTime=1, delay=self.settings['acquisition_time'])
>>>>>>> e5493a783f6e78e2ea9555b6c40b3825d58a65a6
        
        KS.output_a_on.update_value(False)
        
<<<<<<< HEAD
        if self.settings['save_h5']:
            self.save_h5()
        
    def save_h5(self):
=======
        self.plot_line.setData(self.Varray,self.Iarray)
        
                
>>>>>>> e5493a783f6e78e2ea9555b6c40b3825d58a65a6
        # h5 data file setup
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        self.h5_filename = self.h5_file.filename
        self.h5_file.attrs['time_id'] = self.t0
<<<<<<< HEAD
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        H['V'] = np.array(self.Varray)
        H['I'] = np.array(self.Iarray)
        self.h5_file.close()
=======
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)      
        H['V'] = self.Varray
        H['I'] = self.Iarray
        self.h5_file.close()
        print('run done')
>>>>>>> e5493a783f6e78e2ea9555b6c40b3825d58a65a6
        
    def update_display(self):
        self.plot_line.setData(self.Varray,self.Iarray)

