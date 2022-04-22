from numpy import *
import cv2
from tkinter import filedialog
from scipy import interpolate
import matplotlib.pyplot as plt
from tqdm import tqdm

class Cell(object):
    def __init__(self,primary_corner,mat):
        self.corners = array([[0,0],
                              [1,0],
                              [0,1],
                              [1,1]]) + primary_corner
        self.material = mat


class Adaptive_cutting():
    def __init__(self):
        self.wire_length = 970#mm
        self.volts = 28
        self.amps = 1.78
        self.radiance = (self.volts*self.amps)/self.wire_length
        self.buffer = 10
        self.thermal_conductivity = 0.034
        self.specific_heat_capacity = 1300
        self.density = 52.3
        self.thermal_diffusivity = self.thermal_conductivity/(self.specific_heat_capacity*self.density)
    def k(self):
        return self.cut_radius*sqrt(self.feed_rate)
    def der(self,p1,p2):
        self.d = p2-p1
        #print(p1,p2,self.d,self.d[1]/self.d[0])
        return self.d[1]/self.d[0]
    def y_i(self,m,p):
        return p[1]-m*p[0]
    def correct_c(self,m,r,c,s):#gradient, cut radius, current y-intercept, direction of travel
        self.correction = r/cos(arctan(m))
        if s==1:
            return c-self.correction
        if s==-1:
            return c+self.correction
    def irradiance(self,dx,dy):
        self.r2 = dx**2+dy**2
        return self.radiance/(pi*self.r2)
    def fucking_magic(self,root,tip,feed_rate,cut_radius): #Refactered, maybe working, if god knows he aint tellin, BLACK BOX, IF YOU TOUCHEY YOU DIE
        '''Corrects the path to include the adjusted cutting radius'''
        self.root_dat = root
        self.tip_dat = tip
        self.feed_rate = feed_rate
        self.cut_radius = cut_radius
        self.root_line_params = []
        self.tip_line_params = []
        self.updated_root=[]
        self.updated_tip=[]
        for self.index in range(0,len(self.root_dat)-1):
            self.root_path_d = self.root_dat[self.index-1]-self.root_dat[self.index]
            self.tip_path_d = self.tip_dat[self.index-1]-self.tip_dat[self.index]
            self.root_sl= hypot(self.root_path_d[0],self.root_path_d[1])
            self.tip_sl= hypot(self.tip_path_d[0],self.tip_path_d[1])
            self.tip_frp = (self.tip_sl/self.root_sl)*self.feed_rate
            self.root_frp = self.feed_rate
            self.tip_rct = self.k()*(1/self.tip_frp**2)
            self.root_rct = self.k()*(1/self.root_frp**2)
            self.root_yi = self.y_i(self.der(self.root_dat[self.index],self.root_dat[self.index+1]),self.root_dat[self.index])
            self.tip_yi = self.y_i(self.der(self.tip_dat[self.index],self.tip_dat[self.index+1]),self.tip_dat[self.index])
            self.root_der = self.der(self.root_dat[self.index],self.root_dat[self.index+1])
            self.tip_der = self.der(self.tip_dat[self.index],self.tip_dat[self.index+1] )
            self.root_dir = sign(self.root_dat[self.index+1,0]-self.root_dat[self.index,0])
            self.tip_dir = sign(self.tip_dat[self.index+1,0]-self.tip_dat[self.index,0])
            self.corrected_root_line_yi = self.correct_c(self.root_der,self.root_rct,self.root_yi,self.root_dir)
            self.corrected_tip_line_yi = self.correct_c(self.tip_der,self.tip_rct,self.tip_yi,self.tip_dir)
            self.root_line_params.append([self.root_der,self.corrected_root_line_yi,self.root_dir])#Derivative, y_offset, direction
            self.tip_line_params.append([self.tip_der,self.corrected_tip_line_yi,self.tip_dir])
        self.root_line_params = array(self.root_line_params)
        self.updated_root = array(self.updated_root)
        self.root_line_params = array(self.root_line_params)
        self.tip_line_params = array(self.tip_line_params)
        self.new_root = []
        self.new_tip = []
        for self.index in range(0,len(self.root_line_params)):
            self.der1 = self.root_line_params[self.index-1,0]
            self.der2 = self.root_line_params[self.index,0]
            self.yi1 = self.root_line_params[self.index-1,1]
            self.yi2 = self.root_line_params[self.index,1]
            self.dir = self.root_line_params[self.index-1,2]
            self.root_x = (self.yi2-self.yi1)/(self.der1-self.der2)
            self.new_root_y = self.der1*self.root_x+self.yi1
            self.new_root.append([self.root_x,self.new_root_y])
            self.der1 = self.tip_line_params[self.index-1,0]
            self.der2 = self.tip_line_params[self.index,0]
            self.yi1 = self.tip_line_params[self.index-1,1]
            self.yi2 = self.tip_line_params[self.index,1]
            self.dir = self.tip_line_params[self.index-1,2]
            self.tip_x = (self.yi2-self.yi1)/(self.der1-self.der2)
            self.new_tip_y = self.der1*self.tip_x+self.yi1
            self.new_tip.append([self.tip_x,self.new_tip_y])
        self.new_root = array(self.new_root)
        self.new_tip = array(self.new_tip)
        return self.new_root, self.new_tip

    def initialise(self,foil):
        self.shape = array([int(max(foil[:,0])+(4*self.buffer)),int(max(foil[:,1])+(4*self.buffer))])
        self.thermal_profile = zeros((self.shape[1],self.shape[0]),dtype='uint8')
        self.material_profile = zeros((self.shape[1],self.shape[0]),dtype='uint8')
        self.material_profile[self.buffer:-self.buffer,self.buffer:-self.buffer] = 255
        for self.point in foil:
            #print(self.point[1],self.point[0])
            #print(self.thermal_profile[int(self.point[1]),int(self.point[0])])
            self.thermal_profile[int(self.point[1]+2*self.buffer),int(self.point[0]+2*self.buffer)] = 255
        #print(self.thermal_profile)
        #print(self.material_profile)
        cv2.imshow("thermal",self.thermal_profile)
        cv2.imshow("material",self.material_profile)
        cv2.waitKey(100)
        self.test()
    def pol2cart(self,vec):
        self.r, self.theta = vec
        return array([vec[0]*cos(vec[1]),vec[0]*sin(vec[1])])
    def cart2pol(self,vec):
        self.dx, self.dy = vec
        return array([sqrt(self.dx**2+self.dy**2),arctan2(self.dy,self.dx)])
    def los_surfaces(self,x=0,y=0):
        self.bulk_points = transpose(nonzero(cv2.Canny(self.material_profile,200,100) == 255))
        self.frame_shape = (self.material_profile.shape[0],self.material_profile.shape[1],3)
        self.can = cv2.cvtColor(cv2.Canny(self.material_profile,200,100),cv2.COLOR_GRAY2BGR)
        self.point_vectors = self.bulk_points-array([x,y])
        for self.point in tqdm(self.point_vectors):
            self.r, self.theta = self.cart2pol(self.point)
            self.scan_line = arange(0,self.r,1/int(2*self.r))
            self.scan_points = unique(  around(array([self.pol2cart([self.r1, self.theta]) for self.r1 in self.scan_line])),axis=0)
            self.overlap = count_nonzero(isin(self.scan_points, self.bulk_points))
            if self.overlap<2:
                print(self.overlap)
            self.output = self.can.copy()
            self.output[self.point[0],self.point[1]] = [0,0,255]
            for x in self.scan_points:
                #print(x)
                self.output[int(x[0]),int(x[1])]= [0,0,255]
            cv2.imshow("output",self.output)
            cv2.waitKey(1)
            #if self.overlap==1:
            #    print("case1")
            #    self.a,self.b = self.pol2cart(array([self.r,self.theta]))
            #    self.output[int(self.a),int(self.b)] = 255
            #    cv2.imshow("los",self.output)
            #    cv2.waitKey(0)
            #plt.cla()
            #plt.scatter(self.bulk_points[:,0],self.bulk_points[:,1])
            plt.plot(self.scan_points[:,0],self.scan_points[:,1],color="red")
        plt.show()
        self.u, self.indices = unique(around(self.polar_vector[:,1],2), return_index = True)
        self.los_points = array([self.polar_vector[self.index] for self.index in self.indices])
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(projection='polar')
        self.ax.scatter(self.los_points[:,1], self.los_points[:,0])
        plt.show()
    def test(self):
        print(self.material_profile.shape)
        self.surface = cv2.Canny(self.material_profile,100,200)
        cv2.imshow("Surface",self.surface)
        cv2.waitKey(100)
        self.los_surfaces()

class Main():
    def __init__(self):
        self.wing_chord = 200#mm
        self.adaptive_cutting = Adaptive_cutting()
        self.load_foil_data()
        #self.l_foil_dat, self.r_foil_dat = self.adaptive_cutting.fucking_magic(self.foil_dat,self.foil_dat,200,0.65)
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
        self.foil_dat = self.foil_dat*self.wing_chord
        self.foil_dat = unique(around(self.resample(self.foil_dat,2000)),axis=0)
        self.foil_dat = self.foil_dat - array([min(self.foil_dat[:,0]),min(self.foil_dat[:,1])])
if __name__ == "__main__":
    Main()
