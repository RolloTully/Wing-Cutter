from numpy import array, sin, cos, arctan, hypot, sign, append, max, arctan2, sqrt, radians, around
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import Button, Label, IntVar, Checkbutton, Entry, filedialog, Tk, END
class CutterTools():
    def k(self):
        return self.cut_radius/(1/self.feed_rate**2 )
    def der(self,p1,p2):
        self.d = p2-p1
        return self.d[1]/self.d[0]
    def y_i(self,m,p):
        return p[1]-m*p[0]
    def correct_c(self,m,r,c,s):#gradient, cut radius, current y-intercept, direction of travel
        self.correction = r/cos(arctan(m))
        if s==1:
            return c-self.correction
        if s==-1:
            return c+self.correction
    def fucking_magic(self,root,tip,feed_rate,cut_radius):
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
        self.x_max = max(self.new_root[:,0])
        self.y_max = max(self.new_root[:,1])
        self.new_root = self.new_root - array([self.x_max,self.y_max])
        self.new_tip = self.new_tip - array([self.x_max,self.y_max])
        return array(self.new_root),array(self.new_tip)
    def load_settings(self):
        self.settings = open("settings.txt","r").read().split("\n")[0:-2]
        for self.setting in self.settings:
            print(self.setting)
        self.settings = [float(self.num) for self.num in [self.el.split(":")[1]for self.el in self.settings]]
        self.root_c_lenth,self.tip_c_lenth,self.root_alpha,self.tip_alpha, self.wing_span, self.x_offset,self.cut_radius = self.settings
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
    def slice(self,p1,p2):
        self.plane1 = p1
        self.plane2 = p2
        self.l_cutting_plane = []
        self.r_cutting_plane = []
        for self.index in range(self.plane1.shape[0]): #uses a paramerterisation to compute the coordinates
            self.pair = [self.plane1[self.index],self.plane2[self.index]]
            self.der = (self.pair[1]-self.pair[0])/self.wing_span
            self.left_tower_param = (0-self.x_offset)/self.der[2]
            self.right_tower_param = (self.cutter_width-self.x_offset)/self.der[2]
            self.left_tower_coord = self.pair[0]+self.left_tower_param*self.der
            self.right_tower_coord = self.pair[0]+self.right_tower_param*self.der
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
        print(foil.shape)
        self.scaled_foil = array(foil)*chord
        print(self.scaled_foil.shape)
        self.axis = array([chord*rot_axis,0])
        self.angledfoil = self.rotate_data(self.scaled_foil,alpha,self.axis)
        return self.angledfoil
class GUI():
    def __init__(self):
        self.cuttertools = CutterTools()
        self.window = Tk()
        self.window.title("Wing Cutter")
        self.window.geometry("950x900")
        self.root_data = None
        self.tip_data = None
        self.load_tip_button = Button(self.window,text="Load Tip .dat",command = self.load_tip_data)
        self.load_root_button = Button(self.window,text="Load Root .dat",command = self.load_root_data)
        self.load_tip_button.place(x=75,y=0)
        self.load_root_button.place(x=375,y=0)
        self.generate_tip_button = Button(self.window,text="Generate Tip",command = self.generate_tip_foil)
        self.generate_root_button = Button(self.window,text="Generate Root",command = self.generate_root_foil)
        self.generate_tip_button.place(x=75,y=240)
        self.generate_root_button.place(x=375,y=240)
        self.compute_geometry_button = Button(self.window,text="Compute Geometry",command = self.compute_geometry)
        self.compute_geometry_button.place(x=75,y=460)
        self.sliceandsave_button = Button(self.window,text="Slice & Save",command = self.sliceandsave)
        self.sliceandsave_button.place(x=650,y=260)
        self.adapative_toggle = IntVar()
        self.adaptive_toggle_input = Checkbutton(self.window,text="Adaptive Cutting Path",variable = self.adapative_toggle,onvalue=1,offvalue=0)
        self.adaptive_toggle_input.select()
        self.adaptive_toggle_input.place(x=650,y=240)
        self.mirror_mode_toggle = IntVar()
        self.mirror_mode_input = Checkbutton(self.window,text="Mirror Mode(make copies for both sides)",variable = self.mirror_mode_toggle,onvalue=1,offvalue=0)
        self.mirror_mode_input.place(x=650,y=280)
        Label(self.window,text="Beta 1.0").place(x=650,y=800)
        Label(self.window,text="Tip Angle[Degrees]").place(x=650,y=0)
        self.tip_alpha_input = Entry(self.window)
        self.tip_alpha_input.place(x=770,y=0)
        Label(self.window,text="Root Angle[Degrees]").place(x=650,y=20)
        self.root_alpha_input = Entry(self.window)
        self.root_alpha_input.place(x=770,y=20)
        Label(self.window,text="Tip Chord[mm]").place(x=650,y=40)
        self.tip_chord_input = Entry(self.window)
        self.tip_chord_input.place(x=770,y=40)
        Label(self.window,text="Root Chord[mm]").place(x=650,y=60)
        self.Root_chord_input = Entry(self.window)
        self.Root_chord_input.place(x=770,y=60)
        Label(self.window,text="Tip twist position[%]").place(x=650,y=80)
        self.tip_twist_percentage_input = Entry(self.window)
        self.tip_twist_percentage_input.insert(END,"0.25")
        self.tip_twist_percentage_input.place(x=770,y=80)
        Label(self.window,text="Root twist position[%]").place(x=650,y=100)
        self.root_twist_percentage_input = Entry(self.window)
        self.root_twist_percentage_input.insert(END,"0.25")
        self.root_twist_percentage_input.place(x=770,y=100)
        Label(self.window,text="Wingspan[mm]").place(x=650,y=120)
        self.wing_span_input= Entry(self.window)
        self.wing_span_input.place(x=770,y=120)
        Label(self.window,text="Machine Settings").place(x=650,y=160)
        Label(self.window,text="Block offset[mm]").place(x=650,y=180)
        self.x_offset_input= Entry(self.window)
        self.x_offset_input.insert(END,"145")
        self.x_offset_input.place(x=770,y=180)
        Label(self.window,text="Feed Rate[mm/min]").place(x=650,y=200)
        self.feed_rate_input= Entry(self.window)
        self.feed_rate_input.insert(END,"200")
        self.feed_rate_input.place(x=770,y=200)
        Label(self.window,text="Cutter Radius[mm]").place(x=650,y=220)
        self.cut_radius_input= Entry(self.window)
        self.cut_radius_input.insert(END,"0.65")
        self.cut_radius_input.place(x=770,y=220)
        self.true_tip_figure = Figure(figsize=(3,2),dpi=100)
        self.true_tip_plot = self.true_tip_figure.add_subplot()
        self.true_tip_canvas = FigureCanvasTkAgg(self.true_tip_figure, self.window)
        self.true_tip_canvas.get_tk_widget().place(x=0,y=260)
        self.true_root_figure = Figure(figsize=(3,2),dpi=100)
        self.true_root_plot = self.true_root_figure.add_subplot()
        self.true_root_canvas = FigureCanvasTkAgg(self.true_root_figure, self.window)
        self.true_root_canvas.get_tk_widget().place(x=320,y=260)
        self.tip_figure = Figure(figsize=(3,2),dpi=100)
        self.tip_plot = self.tip_figure.add_subplot()
        self.tip_canvas = FigureCanvasTkAgg(self.tip_figure, self.window)
        self.tip_canvas.get_tk_widget().place(x=0,y=30)
        self.root_figure = Figure(figsize=(3,2),dpi=100)
        self.root_plot = self.root_figure.add_subplot()
        self.root_canvas = FigureCanvasTkAgg(self.root_figure, self.window)
        self.root_canvas.get_tk_widget().place(x=320,y=30)
        self.computed_planes_figure = Figure(figsize=(4,4),dpi=100)
        self.computed_planes_plot = self.computed_planes_figure.add_subplot(projection = '3d')
        self.computed_canvas = FigureCanvasTkAgg(self.computed_planes_figure, self.window)
        self.computed_canvas.get_tk_widget().place(x=0,y=490)
        self.window.mainloop()
    def sliceandsave(self):
        print("Called")
        self.lp,self.rp = self.cuttertools.slice(self.computed_root,self.computed_tip)
        print("1")
        self.cuttertools.generate_nc(self.lp,self.rp,"gcode")
        print("2")
        print(self.mirror_mode_toggle.get())
        if self.mirror_mode_toggle.get():
            print("mirrored")
            self.cuttertools.generate_nc(self.rp,self.lp,"mirrored_gcode")
    def compute_geometry(self):
        self.new_root, self.new_tip = self.cuttertools.fucking_magic(self.true_root_foil,self.true_tip_foil,float(self.feed_rate_input.get()),float(self.cut_radius_input.get()))
        self.new_root = self.cuttertools.offset_plane(self.new_root,float(self.x_offset_input.get()))
        self.new_tip = self.cuttertools.offset_plane(self.new_tip,float(self.wing_span_input.get())+float(self.x_offset_input.get()))
        print(self.new_tip,self.new_root)
        self.tip_x_max = max(self.new_tip[:,0])
        self.tip_y_max = max(self.new_tip[:,1])
        self.root_x_max = max(self.new_root[:,0])
        self.root_y_max = max(self.new_root[:,1])
        self.plane_offset = array([0,0,0])
        if self.tip_x_max>self.root_x_max:
            self.plane_offset[0]=self.tip_x_max
        else:
            self.plane_offset[0]=self.root_x_max
        if self.tip_y_max>self.root_y_max:
            self.plane_offset[1]=self.tip_y_max
        else:
            self.plane_offset[1]=self.root_y_max
        self.computed_root = self.new_root - self.plane_offset
        self.computed_tip = self.new_tip - self.plane_offset
        self.computed_planes_plot.cla()
        self.computed_planes_plot.plot(self.computed_root[:,0],self.computed_root[:,1],self.computed_root[:,2],color='green')
        self.computed_planes_plot.plot(self.computed_tip[:,0],self.computed_tip[:,1],self.computed_tip[:,2],color='blue')
        for self.index in range(len(self.computed_root)):
            self.computed_planes_plot.plot([self.computed_root[self.index,0],self.computed_tip[self.index,0]], [self.computed_root[self.index,1],self.computed_tip[self.index,1]], [self.computed_root[self.index,2],self.computed_tip[self.index,2]],color='red')
        self.tip_canvas.draw()
    def format_dat(self,data):
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
        self.true_root_foil = self.cuttertools.generate_foil(self.root_data,int(self.root_alpha_input.get()),float(self.root_twist_percentage_input.get()),float(self.Root_chord_input.get()))
        self.true_root_plot.cla()
        self.true_root_plot.plot(self.true_root_foil[:,0],self.true_root_foil[:,1])
        self.true_root_canvas.draw()
    def generate_tip_foil(self):
        self.true_tip_foil = self.cuttertools.generate_foil(self.tip_data,float(self.tip_alpha_input.get()),float(self.tip_twist_percentage_input.get()),float(self.tip_chord_input.get()))
        self.true_tip_plot.cla()
        self.true_tip_plot.plot(self.true_tip_foil[:,0],self.true_tip_foil[:,1])
        self.true_tip_canvas.draw()
if __name__ == "__main__":
    GUI()
