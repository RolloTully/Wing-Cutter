from numpy import array, sin, cos, tan, arctan, hypot, sign, append, max, arctan2, sqrt, radians, around, zeros, unique, matmul, uint8, argmax, argmin, delete, dot, mean, arctan2, argmax, roll, absolute, pi, equal, empty, arange, isnan, NINF, Inf, r_, linspace, stack, concatenate
from scipy import interpolate
import matplotlib.pyplot as plt
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import Button, Label, IntVar, Checkbutton, Entry, filedialog, Tk, END, Canvas, HORIZONTAL
from tkinter.ttk import Progressbar
class CutterTools():
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
    def fucking_magic(self,root,tip,feed_rate,cut_radius): #Refactered, maybe working, if god knows he aint tellin
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
            print(self.root_dat)
            print("self.index",self.index)

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
    def offset_plane(self,dat, offset):
        self.offset_dat = []
        for self.elment in dat:
            self.offset_dat.append(append(self.elment,[offset]))
        return array(self.offset_dat)
    def rotate_data(self,data,alpha,rot_axis):
        self.rotated_dat= []
        for self.point in data:
            self.rel_point = self.point-rot_axis
            self.p_point = [sqrt(self.rel_point[0]**2+self.rel_point[1]**2),arctan2(self.rel_point[1],self.rel_point[0])]
            self.p_point[1]-= radians([alpha])
            self.c_points = array([self.p_point[0]*cos(self.p_point[1]),self.p_point[0]*sin(self.p_point[1])]).flatten()
            self.rotated_dat.append(self.c_points+rot_axis)
        self.rotated_dat = array(self.rotated_dat)
        return self.rotated_dat
    def slice(self,p1,p2,wing_span,x_offset,cutter_width=890):
        self.plane1 = p1
        self.plane2 = p2
        self.l_cutting_plane = []
        self.r_cutting_plane = []
        for self.index in range(self.plane1.shape[0]): #uses a paramerterisation to compute the coordinates
            self.pair = [self.plane1[self.index],self.plane2[self.index]]
            self.deriv = (self.pair[1]-self.pair[0])/wing_span
            self.left_tower_param = (0-x_offset)/self.deriv[2]
            self.right_tower_param = (cutter_width-x_offset)/self.deriv[2]
            self.left_tower_coord = self.pair[0]+self.left_tower_param*self.deriv
            self.right_tower_coord = self.pair[0]+self.right_tower_param*self.deriv
            self.l_cutting_plane.append(self.left_tower_coord)
            self.r_cutting_plane.append(self.right_tower_coord)
        return around(array(self.l_cutting_plane),2),around(array(self.r_cutting_plane),2)
    def generate_nc(self,lp,rp,name):
        print("opened "+str(name))
        self.output = open(name+".txt","w")

        self.output.write("G90\nM3\nG1 X 0 Y"+str(lp[0,1])+" A 0 B"+str(rp[0,1])+" F200\n")#Moves the wire to the correct starting location
        for self.index in range(len(lp)):
            self.output.write("G1 X"+str(lp[self.index,0])+" Y"+str(lp[self.index,1])+" A"+str(rp[self.index,0])+" B"+str(rp[self.index,1])+" F200\n")
        self.end_command = "G1 X"+str(lp[0,0])+" Y"+str(lp[0,1])+" A"+str(rp[0,0])+" B"+str(rp[0,1])+" F200\nG1 X0 A0 \n G1 Y0 B0\n M3" # returns the wire the the first point completing the countout cut
        self.output.write(self.end_command)
        self.output.close()
        print("closed")
    def generate_foil(self,foil,alpha,rot_axis,chord):
        self.scaled_foil = array(foil)*chord
        self.axis = array([chord*rot_axis,0])
        self.angledfoil = self.rotate_data(self.scaled_foil,alpha,self.axis)
        return self.angledfoil
    def generate_wing_angles(self, alpha_s, alpha_d, root, tip, wing_span, root_chord, tip_chord, set_forward=False):
        self.sweep_displacment = tan(radians(float(alpha_s)))*float(wing_span)
        self.diheadral_displacemnt = tan(radians(float(alpha_d)))*float(wing_span)
        self.angle_displacments = array([self.sweep_displacment,self.diheadral_displacemnt,0]).flatten()
        self.swept_root = root-self.angle_displacments
        self.swept_tip = tip
        return self.swept_root, self.swept_tip
class GUI():
    def __init__(self):
        self.cuttertools = CutterTools()
        self.window = Tk()
        self.cutting_plan=[]
        self.window.title("Wing Cutter")
        self.window.geometry("950x900")
        self.load_tip_button = Button(self.window,text="Load Tip .dat",command = self.load_tip_data)
        self.load_root_button = Button(self.window,text="Load Root .dat",command = self.load_root_data)
        self.load_tip_button.place(x=75,y=0)
        self.load_root_button.place(x=275,y=0)
        self.generate_tip_button = Button(self.window,text="Generate Tip",command = self.generate_tip_foil)
        self.generate_root_button = Button(self.window,text="Generate Root",command = self.generate_root_foil)
        self.generate_tip_button.place(x=75,y=132)
        self.generate_root_button.place(x=275,y=132)
        self.compute_geometry_button = Button(self.window,text="Compute Geometry",command = self.compute_geometry)
        self.compute_geometry_button.place(x=75,y=260)
        self.Add_to_button = Button(self.window,text="Add to cutting plan",command = self.Add_to)
        self.Add_to_button.place(x=420,y=320)

        self.save_button = Button(self.window,text="Save",command = self.save)
        self.save_button.place(x=560,y=320)

        self.adaptive_toggle = IntVar()
        self.adaptive_toggle_input = Checkbutton(self.window,text="Adaptive Cutting Path",variable = self.adaptive_toggle,onvalue=1,offvalue=0)
        self.adaptive_toggle_input.select()
        self.adaptive_toggle_input.place(x=420,y=260)
        self.set_forward_toggle = IntVar()
        self.set_forward_toggle_input = Checkbutton(self.window,text="Set Forward",variable = self.set_forward_toggle,onvalue=1,offvalue=0)
        self.set_forward_toggle_input.place(x=420,y=300)

        self.mirror_mode_toggle = IntVar()
        self.mirror_mode_input = Checkbutton(self.window,text="Mirror Mode(make copies for both sides)",variable = self.mirror_mode_toggle,onvalue=1,offvalue=0)
        self.mirror_mode_input.place(x=420,y=280)
        Label(self.window,text="Beta 1.4").place(x=420,y=570)
        Label(self.window,text="For Help or Troubleshooting, Email: HotWireTroubles@gmail.com").place(x=500,y=820)
        '''Wing Param Inputs'''
        Label(self.window,text="Tip Angle[Degrees]").place(x=420,y=0)
        self.tip_alpha_input = Entry(self.window)
        self.tip_alpha_input.insert(END,"0")
        self.tip_alpha_input.place(x=570,y=0)
        Label(self.window,text="Root Angle[Degrees]").place(x=420,y=20)
        self.root_alpha_input = Entry(self.window)
        self.root_alpha_input.insert(END,"0")
        self.root_alpha_input.place(x=570,y=20)
        Label(self.window,text="Tip Chord[mm]").place(x=420,y=40)
        self.tip_chord_input = Entry(self.window)
        self.tip_chord_input.insert(END,"100")
        self.tip_chord_input.place(x=570,y=40)
        Label(self.window,text="Root Chord[mm]").place(x=420,y=60)
        self.Root_chord_input = Entry(self.window)
        self.Root_chord_input.insert(END,"100")
        self.Root_chord_input.place(x=570,y=60)
        Label(self.window,text="Tip twist position[%]").place(x=420,y=80)
        self.tip_twist_percentage_input = Entry(self.window)
        self.tip_twist_percentage_input.insert(END,"0.25")
        self.tip_twist_percentage_input.place(x=570,y=80)
        Label(self.window,text="Root twist position[%]").place(x=420,y=100)
        self.root_twist_percentage_input = Entry(self.window)
        self.root_twist_percentage_input.insert(END,"0.25")
        self.root_twist_percentage_input.place(x=570,y=100)
        Label(self.window,text="Wingspan[mm]").place(x=420,y=120)
        self.wing_span_input= Entry(self.window)
        self.wing_span_input.insert(END,"600")
        self.wing_span_input.place(x=570,y=120)
        Label(self.window,text="Sweep Angle[Degrees]").place(x=420,y=140)
        self.wing_Sweep_input= Entry(self.window)
        self.wing_Sweep_input.insert(END,"0")
        self.wing_Sweep_input.place(x=570,y=140)
        Label(self.window,text="Diheadral Angle[Degrees]").place(x=420,y=160)
        self.wing_Diheadral_input= Entry(self.window)
        self.wing_Diheadral_input.insert(END,"0")
        self.wing_Diheadral_input.place(x=570,y=160)
        '''NACA Foil Inputs'''
        Label(self.window,text="Tip Foil Number(4 Digit NACA)").place(x=700,y=0)
        self.tip_foil_num= Entry(self.window)
        self.tip_foil_num.place(x=890,y=0)
        Label(self.window,text="Root Foil Number(4 Digit NACA)").place(x=700,y=20)
        self.root_foil_num= Entry(self.window)
        self.root_foil_num.place(x=890,y=20)
        '''Machine settings Input'''
        Label(self.window,text="Machine Settings:").place(x=420,y=180)
        Label(self.window,text="Block offset[mm]").place(x=420,y=200)
        self.x_offset_input= Entry(self.window)
        self.x_offset_input.insert(END,"145")
        self.x_offset_input.place(x=570,y=200)
        Label(self.window,text="Feed Rate[mm/min]").place(x=420,y=220)
        self.feed_rate_input= Entry(self.window)
        self.feed_rate_input.insert(END,"200")
        self.feed_rate_input.place(x=570,y=220)
        Label(self.window,text="Cutter Radius[mm]").place(x=420,y=240)
        self.cut_radius_input= Entry(self.window)
        self.cut_radius_input.insert(END,"0.65")
        self.cut_radius_input.place(x=570,y=240)
        '''Generated Input figure'''
        self.true_tip_figure = Figure(figsize=(2,1),dpi=100)
        self.true_tip_plot = self.true_tip_figure.add_subplot()
        self.true_tip_plot.set_aspect('equal')
        self.true_tip_canvas = FigureCanvasTkAgg(self.true_tip_figure, self.window)
        self.true_tip_canvas.get_tk_widget().place(x=0,y=160)
        '''Generated Root figure'''
        self.true_root_figure = Figure(figsize=(2,1),dpi=100)
        self.true_root_plot = self.true_root_figure.add_subplot()
        self.true_root_plot.set_aspect('equal')
        self.true_root_canvas = FigureCanvasTkAgg(self.true_root_figure, self.window)
        self.true_root_canvas.get_tk_widget().place(x=210,y=160)
        '''Tip Input figure'''
        self.tip_figure = Figure(figsize=(2,1),dpi=100)
        self.tip_plot = self.tip_figure.add_subplot()
        self.tip_plot.set_aspect('equal')
        self.tip_canvas = FigureCanvasTkAgg(self.tip_figure, self.window)
        self.tip_canvas.get_tk_widget().place(x=0,y=30)
        '''Root Input figure'''
        self.root_figure = Figure(figsize=(2,1),dpi=100)
        self.root_plot = self.root_figure.add_subplot()
        self.root_plot.set_aspect('equal')
        self.root_canvas = FigureCanvasTkAgg(self.root_figure, self.window)
        self.root_canvas.get_tk_widget().place(x=210,y=30)
        self.computed_planes_figure = Figure(figsize=(4,4),dpi=100)
        self.computed_planes_plot = self.computed_planes_figure.add_subplot(projection = '3d')
        self.computed_canvas = FigureCanvasTkAgg(self.computed_planes_figure, self.window)
        self.computed_canvas.get_tk_widget().place(x=0,y=290)
        self.window.mainloop()

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

    def gen_naca(self, foil_num):#Bug some where here
        self.foil_num = str(foil_num)
        print(f"FOIL NUMBER {self.foil_num}---------------------------------------")
        self.max_camber = int(self.foil_num[0])/100
        self.max_camber_pos = int(self.foil_num[1])/10
        self.thickness_ratio = int(self.foil_num[2:])/100
        print(f"Foil number: {self.foil_num} Max camber: {self.max_camber} Max camber percentage: {self.max_camber_pos} thickness ratio: {self.thickness_ratio}")
        self.foil_surface = []
        for x in range(100,0,-1):
            self.pp = x/100
            self.thickness = 5*self.thickness_ratio*(0.2969*sqrt(self.pp)-0.1260*self.pp-0.3516*self.pp**2+0.2843*self.pp**3-0.1015*self.pp**4)
            if self.pp<=self.max_camber_pos:
                if self.max_camber != 0:
                    self.camber_offset = (self.max_camber/self.max_camber_pos**2)*(2*self.max_camber_pos*self.pp-self.pp**2)
                    self.offset_theta = arctan((2*self.max_camber/self.max_camber_pos**2)*(self.max_camber_pos-self.pp))

                else:
                    self.camber_offset = 0
                    self.offset_theta = 0
            else:
                if self.max_camber!=0:
                    self.camber_offset = (self.max_camber/(1-self.max_camber_pos)**2)*((1-2*self.max_camber_pos)+2*self.max_camber_pos*self.pp-self.pp**2)
                    self.offset_theta = arctan((2*self.max_camber/(1-self.max_camber_pos)**2)*(self.max_camber_pos-self.pp))
                else:
                    self.camber_offset = 0
                    self.offset_theta = 0
            self.x_a = self.pp - self.thickness*sin(self.offset_theta)
            self.y_a = self.camber_offset+self.thickness*cos(self.offset_theta)
            self.foil_surface.append([self.x_a,self.y_a])

        for x in range(0,100,1):
            self.pp = x/100
            self.thickness = 5*self.thickness_ratio*(0.2969*sqrt(self.pp)-0.1260*self.pp-0.3516*self.pp**2+0.2843*self.pp**3-0.1015*self.pp**4)
            if self.pp<=self.max_camber_pos:
                if self.max_camber!=0:
                    self.camber_offset = (self.max_camber/self.max_camber_pos**2)*(2*self.max_camber_pos*self.pp-self.pp**2)
                    self.offset_theta = arctan((2*self.max_camber/self.max_camber_pos**2)*(self.max_camber_pos-self.pp))
                else:
                    self.camber_offset = 0
                    self.offset_theta = 0
            else:
                if self.max_camber!=0:
                    self.camber_offset = (self.max_camber/(1-self.max_camber_pos)**2)*((1-2*self.max_camber_pos)+2*self.max_camber_pos*self.pp-self.pp**2)
                    self.offset_theta = arctan((2*self.max_camber/(1-self.max_camber_pos)**2)*(self.max_camber_pos-self.pp))
                else:
                    self.camber_offset = 0
                    self.offset_theta = 0
            self.x_a = self.pp+self.thickness*sin(self.offset_theta)
            self.y_a = self.camber_offset-self.thickness*cos(self.offset_theta)
            self.foil_surface.append([self.x_a,self.y_a])
        self.foil_surface = array(self.foil_surface)
        return self.foil_surface
    def Add_to(self):
        self.compute_geometry()
        self.lp,self.rp = self.cuttertools.slice(self.computed_root,self.computed_tip,int(self.wing_span_input.get()),int(self.x_offset_input.get()))
        #self.Cutting_plan.append([self.lp,self.rp])
        self.cutting_plan.append([self.lp,self.rp])

    def save(self):
        for self.num, self.paths in enumerate(self.cutting_plan):
            print(self.num)
            self.cuttertools.generate_nc(self.paths[0],self.paths[1],str(self.num)+"gcode")
            if self.mirror_mode_toggle.get():
                print("mirrored")
                self.cuttertools.generate_nc(self.paths[1],self.paths[0],str(self.num)+"mirrored_gcode")


    def compute_geometry(self):#Known Good, Tested
        self.generate_root_foil()
        self.generate_tip_foil()
        self.resampled_root_foil = self.resample(self.true_root_foil, 1000)
        self.resampled_tip_foil = self.resample(self.true_tip_foil, 1000)
        if self.adaptive_toggle.get():
            self.adjusted_root, self.adjusted_tip = self.cuttertools.fucking_magic(self.resampled_root_foil,self.resampled_tip_foil,float(self.feed_rate_input.get()),float(self.cut_radius_input.get()))
        else:
            self.adjusted_root, self.adjusted_tip = self.resampled_root_foil, self.resampled_tip_foil
        self.new_root_3d = self.cuttertools.offset_plane(self.adjusted_root,float(self.x_offset_input.get()))
        self.new_tip_3d = self.cuttertools.offset_plane(self.adjusted_tip,float(self.wing_span_input.get())+float(self.x_offset_input.get()))
        #print(self.adjusted_root, self.adjusted_tip)
        self.tip_x_max = max(self.new_tip_3d[:,0])
        self.tip_y_max = max(self.new_tip_3d[:,1])
        self.root_x_max = max(self.new_root_3d[:,0])
        self.root_y_max = max(self.new_root_3d[:,1])
        print(f"tip x max {self.tip_x_max}, tip y max {self.tip_y_max}, root x max {self.root_x_max}, root y max {self.root_y_max}")
        self.plane_offset = array([0,0,0])
        print(f"Plane offset {self.plane_offset}")
        if self.tip_x_max>self.root_x_max:
            self.plane_offset[0]=self.tip_x_max
        else:
            self.plane_offset[0]=self.root_x_max
        if self.tip_y_max>self.root_y_max:
            self.plane_offset[1]=self.tip_y_max
        else:
            self.plane_offset[1]=self.root_y_max
        self.computed_root = self.new_root_3d - self.plane_offset
        self.computed_tip = self.new_tip_3d - self.plane_offset
        self.final_root,self.final_tip = self.cuttertools.generate_wing_angles(self.wing_Sweep_input.get(), self.wing_Diheadral_input.get(), self.computed_root, self.computed_tip, self.wing_span_input.get(), self.Root_chord_input.get(), self.tip_chord_input.get(), self.set_forward_toggle.get())
        self.computed_planes_plot.cla()
        self.computed_planes_plot.plot(self.final_root[:,0],self.final_root[:,1],self.final_root[:,2],color='green')
        self.computed_planes_plot.plot(self.final_tip[:,0],self.final_tip[:,1],self.final_tip[:,2],color='blue')
        self.x_lim_upper = max(self.computed_tip[:,0])
        for self.index in range(len(self.final_root)):
            self.computed_planes_plot.plot([self.final_root[self.index,0],self.final_tip[self.index,0]], [self.final_root[self.index,1],self.final_tip[self.index,1]], [self.final_root[self.index,2],self.final_tip[self.index,2]],color='red')
        self.tip_canvas.draw()
    def format_dat(self,data):
        # TODO: Needs Improvment for greater compatibility
        self.data = data.split("\n")
        self.formatted = [self.el.split(" ") for self.el in self.data]
        self.formatted  = [[float(self.num) for self.num in list(filter(lambda x:x!='',self.coord))]for self.coord in self.formatted]#list(map(float,self.formatted))
        self.formatted = list(filter(lambda x:x!=[],self.formatted))
        return self.formatted
    def load_root_data(self):
        self.foil_address = filedialog.askopenfilename()
        self.raw = open(self.foil_address,'r').read()
        self.foil_dat = array(self.format_dat(self.raw))[2:-2]
        self.root_data = self.foil_dat
        self.root_plot.cla()
        self.root_plot.plot(self.foil_dat[:,0],self.foil_dat[:,1])
        self.root_canvas.draw()
    def load_tip_data(self):
        self.foil_address = filedialog.askopenfilename()
        self.raw = open(self.foil_address,'r').read()
        self.foil_dat = array(self.format_dat(self.raw))[2:-2]
        self.tip_data = self.foil_dat
        self.tip_plot.cla()
        self.tip_plot.plot(self.foil_dat[:,0],self.foil_dat[:,1])
        self.tip_canvas.draw()
    def generate_root_foil(self):
        if self.root_foil_num.get() != "":
            self.root_data = self.gen_naca(self.root_foil_num.get())
        self.true_root_foil = self.cuttertools.generate_foil(self.root_data,int(self.root_alpha_input.get()),float(self.root_twist_percentage_input.get()),float(self.Root_chord_input.get()))
        self.true_root_plot.cla()
        self.true_root_plot.plot(self.true_root_foil[:,0],self.true_root_foil[:,1])
        self.true_root_canvas.draw()
    def generate_tip_foil(self):
        if self.tip_foil_num.get() !="":
            self.tip_data = self.gen_naca(self.tip_foil_num.get())
        self.true_tip_foil = self.cuttertools.generate_foil(self.tip_data,float(self.tip_alpha_input.get()),float(self.tip_twist_percentage_input.get()),float(self.tip_chord_input.get()))
        self.true_tip_plot.cla()
        self.true_tip_plot.plot(self.true_tip_foil[:,0],self.true_tip_foil[:,1])
        self.true_tip_canvas.draw()
if __name__ == "__main__":
    GUI()
