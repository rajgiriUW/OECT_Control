'''
Created on Feb 27, 2019

@author: Benedikt Ursprung, Brian Shevitski
'''

from ScopeFoundry  import Measurement, h5_io
import time
import numpy as np
import pyqtgraph as pg


class IVBaseMeasurement(Measurement):
    '''
    Sources voltage and measures (after a delay time) the voltage and current of channel A 
    of a Keithley sourcemeter unit.
    Can be used as a stand alone iv measurement or as a Base class.
    If used as a base class override collect_Vs(self, i, Vs, I_measured, V_measured) and 
    self.save_collected()
    '''
    name = "iv_base_measurement"
    
    def setup(self):
        kwargs = {'unit':'V', 'vmin':-5, 'vmax':5, 'spinbox_decimals':6}
        self.voltage_range = self.settings.New_Range('source_voltage',  initials = [-0.2, 0.8, 0.1], include_sweep_type = True, **kwargs)
        self.save_h5 = self.settings.New('save_h5', bool, initial = True)
    
    def setup_figure(self):
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))        
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.plot.showGrid(True,True)
        self.plot_line = self.plot.plot()
        self.plot.setLabel('left', 'current', 'A')
        self.plot.setLabel('bottom', 'voltage', 'V')

    def run(self):
        self.t0 = time.time()

        #Hardware
        self.keithley_hw = self.app.hardware['keithley_sourcemeter']
        KS = self.keithley_hw.settings
        
        self.keithley = self.keithley_hw.keithley
        
        KS['output_a_on'] = True
        
        time.sleep(0.5)

        #measure IV        
        self.V_sources = self.voltage_range.sweep_array        
        self.I_array = np.zeros_like(self.V_sources, float)
        self.V_array = np.zeros_like(self.V_sources, float)
        
        for i,Vs in enumerate(self.V_sources):
            self.ii = i
            self.set_progress(i/len(self.V_sources) * 100)

            KS['source_V_a'] = Vs
            time.sleep(KS['delay_time_a'])
            self.keithley_hw.settings.I_a.read_from_hardware()
            self.keithley_hw.settings.V_a.read_from_hardware()
            self.I_array[i] = KS["I_a"]
            self.V_array[i] = KS["V_a"]
            self.collect_Vs(i, Vs, KS["I_a"], KS["V_a"])
        
        KS['output_a_on'] = False

        if self.settings['save_h5']:
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
            self.h5_filename = self.h5_file.filename
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)        
            H['V_sourced'] = self.V_sources  
            H['V'] = np.array(self.V_array)
            H['I'] = np.array(self.I_array)
            self.save_collected()
            self.h5_file.close()
        
        
    def update_display(self):
        self.plot_line.setData(self.V_array[:self.ii],self.I_array[:self.ii])
        
    def collect_Vs(self, i, Vs, I_measured, V_measured):
        '''
        override me!
        '''
        print('sourced Voltage', i, Vs, I_measured, V_measured)        
        
    def save_collected(self):
        '''
        override me! You can use self.h5_meas_group and self.h5_file
        '''
        pass               


class IVTRPL(IVBaseMeasurement):
    
    name = 'iv_trpl'
    
    hardware_requirements = ['picoharp', 'keithley_sourcemeter']

    
    def pre_run(self):
        IVBaseMeasurement.pre_run(self)
        
        M = self.picoharp_histogram_measure = self.app.measurements.picoharp_histogram
        M.settings['save_h5'] = False
        M.pre_run()
        
        Ns = len(self.voltage_range.sweep_array)
        self.time_traces = np.zeros((Ns, M.data_slice.stop))
        self.elapsed_meas_time = np.zeros(Ns)
        
    def collect_Vs(self, i, Vs, I_measured, V_measured):
        IVBaseMeasurement.collect_Vs(self, i, Vs, I_measured, V_measured)

        M = self.picoharp_histogram_measure
        self.start_nested_measure_and_wait(M, start_time=0.2)

        self.time_traces[i,:] = M.histogram_data
        self.elapsed_meas_time[i] = M.elapsed_meas_time
        
    def save_collected(self):
        H = self.h5_meas_group
        H['time_traces'] = self.time_traces
        H['time_array'] = self.picoharp_histogram_measure.time_array
        H['elapsed_meas_time'] = self.elapsed_meas_time
        self.h5_file.close()
        
    def post_run(self):
        IVBaseMeasurement.post_run(self)

        M = self.picoharp_histogram_measure
        M.settings['save_h5'] = True
