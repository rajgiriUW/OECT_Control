from __future__ import division
'''
Created on Sept 8, 2014

@author: Edward Barnard and Benedikt Ursprung
'''

from .base_2d_scan import Base2DScan
import numpy as np
import time
from measurement_components.base_3d_scan import Base3DScan

class Photocurrent2DMeasurement(Base2DScan):
    name = "photocurrent_scan2D"
    def scan_specific_setup(self):
        print "scan_specific_setup", self.name
        
        self.display_update_period = 0.1 #seconds
        
        # logged quantities
        self.source_voltage = self.add_logged_quantity("source_voltage", dtype=float, unit='V', vmin=-5, vmax=5, ro=False)
        self.source_voltage.connect_bidir_to_widget(self.gui.ui.photocurrent2D_source_voltage_doubleSpinBox)
        
        self.chopp_frequency = self.add_logged_quantity("chopp_frequency", dtype=float, unit='Hz', vmin=0, vmax=1000, ro=False)
        self.chopp_frequency.connect_bidir_to_widget(self.gui.ui.photocurrent2D_chopp_frequency_doubleSpinBox)
        
                
        #connect events
        self.gui.ui.photocurrent2D_start_pushButton.clicked.connect(self.start)
        self.gui.ui.photocurrent2D_interrupt_pushButton.clicked.connect(self.interrupt)



    def setup_figure(self):
        self.fig = self.gui.add_figure("photocurrent2D_map", self.gui.ui.photocurrent2D_plot_groupBox)
        
        self.ax2d = self.fig.add_subplot(111)

        self.ax2d.set_xlim(0, 100)
        self.ax2d.set_ylim(0, 100)
        
        self.min_max_text = self.fig.text(0,0, "min,max")


    def pre_scan_setup(self):
        # hypserspectral scan specific setup

        #hardware
        self.keithley_hc = self.gui.keithley_sourcemeter_hc
        K1 = self.keithley = self.keithley_hc.keithley
        
        self.srs_hc = self.gui.srs_lockin_hc
        S1 = self.srs = self.srs_hc.srs
      
        
        #pre scan setup  
        K1.resetA()
        K1.setAutoranges_A()
        K1.setV_A( self.source_voltage.val )
        K1.switchV_A_on()
        
        #self.thorlabs_OC_hc = self.gui.thorlabs_powermeter_hc
        #self.thorlabs_OC = self.thorlabs_OC_hc.thorlabs_optical_chopper         
        #self.thorlabs_OC.write_freq( self.chopp_frequency.val )
        
        
        #create data arrays
        self.photocurrent_map = np.zeros((self.Nv, self.Nh), dtype=float)
        self.photocurrent_chopped_map = np.zeros((self.Nv, self.Nh), dtype=float)
        
        
        
        '''#update figure
        self.imgplot = self.ax2d.imshow(self.photocurrent_map, 
                                    origin='lower',
                                    interpolation='nearest', 
                                    extent=self.imshow_extent)
        
        '''

        #update chopped figure figure
        self.imgplot = self.ax2d.imshow(self.photocurrent_chopped_map, 
                                    origin='lower',
                                    interpolation='nearest', 
                                    extent=self.imshow_extent)
        
        
        
        
    def collect_pixel(self,i_h,i_v):

        # collect data
        #i_array = self.keithley.measureI_A(N=10,KeithleyADCIntTime=1,delay=0)     
        #avg_i = np.average(i_array)
        t0 = time.time()

        time.sleep(0.150)

        sens_changed = self.srs.auto_sensitivity()
        if sens_changed:
           time.sleep(0.5)
        


        avg_i_chopped = self.srs.get_signal()
        
        # store in arrays
        
        #self.photocurrent_map[i_v, i_h] = avg_i
        #print i_h, i_v, avg_i
        
        self.photocurrent_chopped_map[i_v, i_h] = avg_i_chopped
        #print i_h, i_v, avg_i_chopped, "Chopped"
        
        t1 = time.time()
        print "pixel took", t1-t0
        
        
    def scan_specific_savedict(self):
        save_dict = {
                     'photocurrent_map': self.photocurrent_map,
                     'photocurrent_chopped_map': self.photocurrent_chopped_map,
                    }
        return save_dict
    
    
    
    def update_display(self):    

        self.fig.clf()
        self.ax2d = self.fig.add_subplot(111)
        self.imgplot = self.ax2d.imshow(self.photocurrent_chopped_map, 
                                    origin='lower',
                                    interpolation='nearest', 
                                    extent=self.imshow_extent)


        #C = self.photocurrent_map
        C = self.photocurrent_chopped_map
        self.imgplot.set_data(C[::,::])
        
        try:
            count_min =  np.min(C[np.nonzero(C)])
        except Exception:
            count_min = 0
        count_max = np.max(C[2:,:])
        self.min_max_text.set_text("{:e}, {:e}".format(count_min, count_max))
        
        self.imgplot.set_clim(count_min, count_max )
        #self.imgplot.set_clim(0, 1e-6 )        
        self.fig.canvas.draw()



class Photocurrent3DMeasurement(Base3DScan):
    name = "photocurrent_scan3D"
    def scan_specific_setup(self):
        print "scan_specific_setup", self.name
        
        self.display_update_period = 0.1 #seconds
        
        # logged quantities
        self.source_voltage = self.add_logged_quantity("source_voltage", dtype=float, unit='V', vmin=-5, vmax=5, ro=False)
        self.source_voltage.connect_bidir_to_widget(self.gui.ui.photocurrent2D_source_voltage_doubleSpinBox)
        
        #self.chopp_frequency = self.add_logged_quantity("chopp_frequency", dtype=float, unit='Hz', vmin=0, vmax=1000, ro=False)
        #self.chopp_frequency.connect_bidir_to_widget(self.gui.ui.photocurrent2D_chopp_frequency_doubleSpinBox)
        
                
        #connect events
        #self.gui.ui.photocurrent2D_start_pushButton.clicked.connect(self.start)
        #self.gui.ui.photocurrent2D_interrupt_pushButton.clicked.connect(self.interrupt)



    def setup_figure(self):
        pass

    def pre_scan_setup(self):
        # hypserspectral scan specific setup

        #hardware
        self.keithley_hc = self.gui.keithley_sourcemeter_hc
        K1 = self.keithley = self.keithley_hc.keithley
        
        self.srs_hc = self.gui.srs_lockin_hc
        S1 = self.srs = self.srs_hc.srs
      
        #pre scan setup  
        K1.resetA()
        K1.setAutoranges_A()
        K1.setV_A( self.source_voltage.val )
        K1.switchV_A_on()
        
        #self.thorlabs_OC_hc = self.gui.thorlabs_powermeter_hc
        #self.thorlabs_OC = self.thorlabs_OC_hc.thorlabs_optical_chopper         
        #self.thorlabs_OC.write_freq( self.chopp_frequency.val )
        
        
        #create data arrays
        self.photocurrent_map = np.zeros((self.Nz, self.Ny, self.Nx), dtype=float)
        self.photocurrent_chopped_map = np.zeros((self.Nz, self.Ny, self.Nx), dtype=float)
        
        
        
        
        
    def collect_pixel(self,i,j,k):

        # collect data
        #i_array = self.keithley.measureI_A(N=10,KeithleyADCIntTime=1,delay=0)     
        #avg_i = np.average(i_array)
        t0 = time.time()
        time.sleep(0.050)
        sens_changed = self.srs.auto_sensitivity()
        if sens_changed:
           time.sleep(0.5)
        
        avg_i_chopped = self.srs.get_signal()
        t1 =time.time()
        # store in arrays
        
        #self.photocurrent_map[i_v, i_h] = avg_i
        #print i_h, i_v, avg_i
        
        self.photocurrent_chopped_map[k,j,i] = avg_i_chopped
        print i,j,k, avg_i_chopped, "Chopped"
        print 'pixel took ', t1-t0        
        
        
    def scan_specific_savedict(self):
        save_dict = {
                     'photocurrent_map': self.photocurrent_map,
                     'photocurrent_chopped_map': self.photocurrent_chopped_map,
                    }
        return save_dict
    
    
    
    def update_display(self):    
        pass