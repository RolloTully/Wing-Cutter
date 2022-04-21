from numpy import *
import cv2
from tkinter import filedialog
from scipy import interpolate
class Adaptive_cutting():
    def __init__(self):
        self.buffer = 10
    def initialise(self,foil):
        self.shape = array([int(max(foil[:,0])+(2*self.buffer)),int(max(foil[:,1])+(2*self.buffer))])
        self.thermal_profile = zeros((self.shape[1],self.shape[0]))
        for self.point in foil:
            print(self.point[1],self.point[0])
            print(self.thermal_profile[int(self.point[1]),int(self.point[0])])
            self.thermal_profile[int(self.point[1]+self.buffer),int(self.point[0]+self.buffer)] = 255
        cv2.imshow("test",self.thermal_profile)
        cv2.waitKey(0)


class Main():
    def __init__(self):
        self.adaptive_cutting = Adaptive_cutting()
        self.load_foil_data()
        self.adaptive_cutting.initialise(self.foil_dat)

    def resample(self, foil, samples):#refactored to used a fit point spline because linear inteprolaten is hot grabage that breaks everything
        '''Uses B-spline interpolation to smooth and interolate the input spline for more easy data handling, and avoiding co linear points'''
        self.foil_x = array(foil)[:,0]
        self.foil_y = array(foil)[:,1]
        self.foil_x = r_[self.foil_x,self.foil_x[0]]
        self.foil_y = r_[self.foil_y,self.foil_y[0]]
        self.tck , self.u = interpolate.splprep([self.foil_x,self.foil_y],k=5,s=0.1,per=True)
        self.i_x, self.i_y = interpolate.splev(linspace(0,1,samples),self.tck)
        self.resampled_foil = stack((self.i_x,self.i_y),axis=1)
        return self.resampled_foil

    def format_dat(self,data):
        self.data = data.split("\n")
        self.formatted = [self.el.split(" ") for self.el in self.data]
        self.formatted  = [[float(self.num) for self.num in list(filter(lambda x:x!='',self.coord))]for self.coord in self.formatted]#list(map(float,self.formatted))
        self.formatted = list(filter(lambda x:x!=[],self.formatted))
        return self.formatted

    def load_foil_data(self):
        self.foil_address = filedialog.askopenfilename()
        self.raw = open(self.foil_address,'r').read()
        self.foil_dat = array(self.format_dat(self.raw))[2:-2]
        self.foil_dat = self.foil_dat*300
        self.foil_dat = unique(around(self.resample(self.foil_dat,2000)),axis=0)
        print(array([min(self.foil_dat[:,0]),min(self.foil_dat[:,1])]))
        self.foil_dat = self.foil_dat - array([min(self.foil_dat[:,0]),min(self.foil_dat[:,1])])
if __name__ == "__main__":
    Main()
