from numpy import array, sin, cos, tan, arctan, hypot, sign, append, max, arctan2, sqrt, radians, around, zeros, unique, matmul, uint8, argmax, argmin, delete, dot, mean, arctan2, argmax, roll, absolute, pi, equal, empty, arange, isnan, NINF, Inf, r_, linspace, stack, concatenate, minimum, all
from scipy import interpolate
import matplotlib.pyplot as plt
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import *
from tkinter import filedialog
#from tkinter.ttk import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *
from pyopengltk import OpenGLFrame
from winsound import *
import re
class Wing():
    '''A struct to hold information about a particuar wing section'''
    def __init__(self, root, tip, span):
        self.section_name = ""
        self.root = root
        self.tip = tip
        self.d_root = None
        self.d_tip = None
        self.retain_border = False
        self.span = span
        self.bounding_box = array([self.root.min(axis=0),self.tip.min(axis=0)]).min(axis=0)



class AppOgl(OpenGLFrame):
    def initgl(self):
        """Initalize gl states when the frame is created"""
        self.vertex_shader = """
        varying vec3 vN;
        varying vec3 v;
        varying vec4 color;
        void main(void)
        {
        v = vec3(gl_ModelViewMatrix * gl_Vertex);
        vN = normalize(gl_NormalMatrix * gl_Normal);
        color = gl_Color;
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }
        """
        self.fragment_shader = """
        varying vec3 vN;
        varying vec3 v;
        varying vec4 color;
        #define MAX_LIGHTS 1
        void main (void){
        vec3 N = normalize(vN);
        vec4 finalColor = vec4(0.0, 0.0, 0.0, 0.0);
        for (int i=0;i<MAX_LIGHTS;i++){
        vec3 L = normalize(gl_LightSource[i].position.xyz - v);
        vec3 E = normalize(-v); // we are in Eye Coordinates, so EyePos is (0,0,0)
        vec3 R = normalize(-reflect(L,N));
        vec4 Iamb = gl_LightSource[i].ambient;
        vec4 Idiff = gl_LightSource[i].diffuse * max(dot(N,L), 0.0);
        Idiff = clamp(Idiff, 0.0, 1.0);
        vec4 Ispec = gl_LightSource[i].specular * pow(max(dot(R,E),0.0),0.3*gl_FrontMaterial.shininess);
        Ispec = clamp(Ispec, 0.0, 1.0);
        finalColor += Iamb + Idiff + Ispec;
        }
        gl_FragColor = color * finalColor;
        }
        """
        self.program = compileProgram(compileShader(self.vertex_shader, GL_VERTEX_SHADER), compileShader(self.fragment_shader, GL_FRAGMENT_SHADER))
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(70, (700/500), 0.1, 50000.0)
        glTranslatef(0.0,0.0,-450.0)
        glMatrixMode(GL_MODELVIEW)
        glLight(GL_LIGHT0, GL_POSITION,  (0, 0, 1, 0.4))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0, 0.5, 0.1, 0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (1,1,1,0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 128)
        glEnable(GL_DEPTH_TEST)
        self.verticies=()
        self.edges=()
        glViewport(0, 0, self.width, self.height)
        glRotatef(20, 0, 1, 0)
        glRotatef(30, 0, 0, 1)
    def redraw(self):
        """Render a single frame"""
        #glRotatef(2, 1, 0, 0)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glColorMaterial(GL_FRONT_AND_BACK, GL_SPECULAR)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        glEnable(GL_LIGHTING)
        glUseProgram(self.program)
        glBegin(GL_TRIANGLE_STRIP)
        for self.vertex in self.edges:
            glColor4f(0,1,0,0.3)
            glVertex3fv(self.verticies[self.vertex])
        glEnd()
        glDisable(GL_LIGHTING)
        glDisable(GL_POLYGON_OFFSET_FILL)
        glDisable(GL_LIGHT0)
        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)
class CutterTools():
    def k(self):
        return self.cut_radius*sqrt(self.feed_rate)
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
    def generate_foil(self,foil,alpha,rot_axis,chord):
        self.scaled_foil = array(foil)*chord
        self.axis = array([chord*rot_axis,0])
        self.angledfoil = self.rotate_data(self.scaled_foil,alpha,self.axis)
        return self.angledfoil
    def generate_wing_angles(self, alpha_s, alpha_d, root, tip, wing_span, root_chord, tip_chord, set_forward=False, set_backward = False):
        if set_forward:
            self.diheadral_displacemnt = tan(radians(float(alpha_d)))*float(wing_span)
            self.angle_displacments = array([0,self.diheadral_displacemnt,0]).flatten()
            if alpha_s <=0:
                self.swept_root = root-self.angle_displacments
                self.swept_tip = tip
            elif alpha_s > 0:
                self.swept_root = root
                self.swept_tip = tip+self.angle_displacments
            return self.swept_root, self.swept_tip
        if set_backward:
            self.sweep_displacment = float(root_chord) - float(tip_chord)
            self.diheadral_displacemnt = tan(radians(float(alpha_d)))*float(wing_span)
            self.angle_displacments = array([self.sweep_displacment,self.diheadral_displacemnt,0]).flatten()
            self.swept_root = root-self.angle_displacments
            self.swept_tip = tip
            return self.swept_root, self.swept_tip
        else:
            self.sweep_displacment = tan(radians(float(alpha_s)))*float(wing_span)+((float(root_chord)/4)-(float(tip_chord)/4))
            self.diheadral_displacemnt = tan(radians(float(alpha_d)))*float(wing_span)
            self.angle_displacments = array([self.sweep_displacment,self.diheadral_displacemnt,0]).flatten()
            self.swept_root = root-self.angle_displacments
            self.swept_tip = tip
        return self.swept_root, self.swept_tip
class GUI(Tk):
    def __init__(self,parent):
        Tk.__init__(self, parent)
        self.parser = re.compile("G[10]")
        self.parent = parent
        self.cuttertools = CutterTools()
        self.wings = []
        self.title("Wing Cutter")
        self.geometry("1200x900+20+20")
        self.load_tip_button = Button(self,text="Load Tip .dat",command = self.load_tip_data)
        self.load_root_button = Button(self,text="Load Root .dat",command = self.load_root_data)
        self.load_tip_button.place(x=75,y=0)
        self.load_root_button.place(x=275,y=0)
        self.generate_tip_button = Button(self,text="Generate Tip",command = self.generate_tip_foil)
        self.generate_root_button = Button(self,text="Generate Root",command = self.generate_root_foil)
        self.generate_tip_button.place(x=75,y=132)
        self.generate_root_button.place(x=275,y=132)
        self.compute_geometry_button = Button(self,text="Compute Geometry",command = self.compute_geometry)
        self.compute_geometry_button.place(x=75,y=260)
        self.Add_to_button = Button(self,text="Add to cutting plan",command = self.Add_to)
        self.Add_to_button.place(x=420,y=300)
        self.clear_button = Button(self,text="Clear cutting plan",command = self.Clear)
        self.clear_button.place(x=420,y=330)
        self.Export_button = Button(self,text="Export",command = self.Export)
        self.Export_button.place(x=560,y=300)
        self.adaptive_toggle = IntVar()
        self.adaptive_toggle_input = Checkbutton(self,text="Adaptive Cutting Path",variable = self.adaptive_toggle,onvalue=1,offvalue=0)
        self.adaptive_toggle_input.select()
        self.adaptive_toggle_input.place(x=420,y=260)
        self.mirror_mode_toggle = IntVar()
        self.mirror_mode_input = Checkbutton(self,text="Mirror Mode(make copies for both sides)",variable = self.mirror_mode_toggle,onvalue=1,offvalue=0)
        self.mirror_mode_input.place(x=420,y=280)
        self.back_toggle = IntVar()
        self.back_mode_input = Checkbutton(self,text="Set back",variable = self.back_toggle,onvalue=1,offvalue=0)
        self.back_mode_input.place(x=700,y=260)
        self.forward_toggle = IntVar()
        self.forward_mode_input = Checkbutton(self,text="Set forward",variable = self.forward_toggle,onvalue=1,offvalue=0)
        self.forward_mode_input.place(x=700,y=280)
        Label(self,text="Beta 2.2").place(x=10,y=840)
        Label(self,text="For Help or Troubleshooting, Email: HotWireTroubles@gmail.com").place(x=10,y=860)

        '''Wing Param Inputs'''
        Label(self,text="Tip Angle[Degrees]").place(x=420,y=0)
        self.tip_alpha_input = Entry(self, width = 7)
        self.tip_alpha_input.insert(END,"0")
        self.tip_alpha_input.place(x=570,y=0)
        Label(self,text="Root Angle[Degrees]").place(x=420,y=20)
        self.root_alpha_input = Entry(self, width = 7)
        self.root_alpha_input.insert(END,"0")
        self.root_alpha_input.place(x=570,y=20)
        Label(self,text="Tip Chord[mm]").place(x=420,y=40)
        self.tip_chord_input = Entry(self, width = 7)
        self.tip_chord_input.insert(END,"100")
        self.tip_chord_input.place(x=570,y=40)
        Label(self,text="Root Chord[mm]").place(x=420,y=60)
        self.Root_chord_input = Entry(self, width = 7)
        self.Root_chord_input.insert(END,"100")
        self.Root_chord_input.place(x=570,y=60)
        Label(self,text="Tip twist position[%]").place(x=420,y=80)
        self.tip_twist_percentage_input = Entry(self, width = 7)
        self.tip_twist_percentage_input.insert(END,"0.25")
        self.tip_twist_percentage_input.place(x=570,y=80)
        Label(self,text="Root twist position[%]").place(x=420,y=100)
        self.root_twist_percentage_input = Entry(self, width = 7)
        self.root_twist_percentage_input.insert(END,"0.25")
        self.root_twist_percentage_input.place(x=570,y=100)
        Label(self,text="Wingspan[mm]").place(x=420,y=120)
        self.wing_span_input= Entry(self, width = 7)
        self.wing_span_input.insert(END,"600")
        self.wing_span_input.place(x=570,y=120)
        Label(self,text="Sweep Angle[Degrees]").place(x=420,y=140)
        self.wing_Sweep_input= Entry(self, width = 7)
        self.wing_Sweep_input.insert(END,"0")
        self.wing_Sweep_input.place(x=570,y=140)
        Label(self,text="Diheadral Angle[Degrees]").place(x=420,y=160)
        self.wing_Diheadral_input= Entry(self, width = 7)
        self.wing_Diheadral_input.insert(END,"0")
        self.wing_Diheadral_input.place(x=570,y=160)
        Label(self,text="Number of copies").place(x=620,y=200)
        self.copies= Entry(self, width = 7)
        self.copies.insert(END,"1")
        self.copies.place(x=725,y=200)

        '''NACA Foil Inputs'''
        Label(self,text="Tip Foil Number(4 Digit NACA)").place(x=620,y=0)
        self.tip_foil_num= Entry(self, width = 7)
        self.tip_foil_num.place(x=800,y=0)
        Label(self,text="Root Foil Number(4 Digit NACA)").place(x=620,y=20)
        self.root_foil_num= Entry(self, width = 7)
        self.root_foil_num.place(x=800,y=20)

        '''Foam Dimensions Input'''
        Label(self,text="Foam Dimensions:").place(x=620,y=60)
        Label(self,text="Block Height[mm]").place(x=620,y=80)
        self.foam_height= Entry(self, width = 7)
        self.foam_height.place(x=730,y=80)
        self.foam_height.insert(END,"200")
        Label(self,text="Block Length[mm]").place(x=620,y=100)
        self.foam_length= Entry(self, width = 7)
        self.foam_length.place(x=730,y=100)
        self.foam_length.insert(END, "700")

        '''Machine settings Input'''
        Label(self,text="Machine Settings:").place(x=420,y=180)
        Label(self,text="Block offset[mm]").place(x=420,y=200)
        self.x_offset_input= Entry(self, width = 7)
        self.x_offset_input.insert(END,"145")
        self.x_offset_input.place(x=570,y=200)
        Label(self,text="Feed Rate[mm/min]").place(x=420,y=220)
        self.feed_rate_input= Entry(self, width = 7)
        self.feed_rate_input.insert(END,"200")
        self.feed_rate_input.place(x=570,y=220)
        Label(self,text="Cutter Radius[mm]").place(x=420,y=240)
        self.cut_radius_input= Entry(self, width = 7)
        self.cut_radius_input.insert(END,"1.0")
        self.cut_radius_input.place(x=570,y=240)

        '''Generated Input figure'''
        self.true_tip_figure = Figure(figsize=(2,1),dpi=100)
        self.true_tip_plot = self.true_tip_figure.add_subplot()
        self.true_tip_plot.set_aspect('equal')
        self.true_tip_canvas = FigureCanvasTkAgg(self.true_tip_figure, self)
        self.true_tip_canvas.get_tk_widget().place(x=0,y=160)

        '''Generated Root figure'''
        self.true_root_figure = Figure(figsize=(2,1),dpi=100)
        self.true_root_plot = self.true_root_figure.add_subplot()
        self.true_root_plot.set_aspect('equal')
        self.true_root_canvas = FigureCanvasTkAgg(self.true_root_figure, self)
        self.true_root_canvas.get_tk_widget().place(x=210,y=160)

        '''Tip Input figure'''
        self.tip_figure = Figure(figsize=(2,1),dpi=100)
        self.tip_plot = self.tip_figure.add_subplot()
        self.tip_plot.set_aspect('equal')
        self.tip_canvas = FigureCanvasTkAgg(self.tip_figure, self)
        self.tip_canvas.get_tk_widget().place(x=0,y=30)

        '''Root Input figure'''
        self.root_figure = Figure(figsize=(2,1),dpi=100)
        self.root_plot = self.root_figure.add_subplot()
        self.root_plot.set_aspect('equal')
        self.root_canvas = FigureCanvasTkAgg(self.root_figure, self)
        self.root_canvas.get_tk_widget().place(x=210,y=30)
        self.computed_planes_figure = Figure(figsize=(4,4),dpi=100)
        self.computed_planes_plot = self.computed_planes_figure.add_subplot(projection = '3d')
        self.computed_canvas = FigureCanvasTkAgg(self.computed_planes_figure, self)
        self.computed_canvas.get_tk_widget().place(x=0,y=290)

        """GCode Command View"""
        self.gcode_figure = Figure(figsize=(4,4),dpi=100)
        self.gcode_plot = self.gcode_figure.add_subplot(projection = '3d')
        self.gcode_canvas = FigureCanvasTkAgg(self.gcode_figure, self)
        self.gcode_canvas.get_tk_widget().place(x=500,y=330)
        self.mainloop()

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
    def gen_naca(self, foil_num): #genrates 4 digit naca air foils
        self.foil_num = str(foil_num)
        self.max_camber = int(self.foil_num[0])/100
        self.max_camber_pos = int(self.foil_num[1])/10
        self.thickness_ratio = int(self.foil_num[2:])/100
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
    def pack(self):
        '''Packs the wings for cutting, not the most efficent but its ok'''
        '''If people want to update this to please feel free to'''
        '''if you want to update it please consult the notes'''
        self.block_height = float(self.foam_height.get())
        self.block_length = float(self.foam_length.get())
        self.x_offset = 0
        self.y_offset = 0
        self.cutting_plan = []
        self.new_x_offset = 0
        for self.section in self.wings:
            print("x:",self.x_offset," y:",self.y_offset)
            if self.x_offset>self.block_length:
                print("There is insufficent foam to perform the requested operation")
                pass
            elif (abs(self.section.bounding_box[0])>self.block_length)or(abs(self.section.bounding_box[1])>self.block_height):#Case1 The wing is too big
                print("path beyond cutter capacity, this foil will not be cut")
                pass
            elif (self.y_offset + self.section.bounding_box[1])+self.block_height>0: # Case2 The Wing will fit in the current column
                if self.section.bounding_box[0] > self.new_x_offset:
                    self.new_x_offset = self.section.bounding_box[0]
                self.section.root = self.section.root+array([self.x_offset, self.y_offset,0])
                self.section.tip = self.section.tip+array([self.x_offset, self.y_offset,0])
                self.cutting_plan.append(self.section)
                self.y_offset += (self.section.bounding_box[1]-10)
            elif (self.y_offset + self.section.bounding_box[1]-10)+self.block_height<=0:# Case3 The Wing will not fit in the current column
                if self.new_x_offset == 0:
                    self.new_x_offset = self.section.bounding_box[0]
                self.x_offset += self.new_x_offset-10
                if self.section.bounding_box[0] < self.new_x_offset:
                    self.new_x_offset = self.section.bounding_box[0]
                self.new_x_offset = 0
                self.y_offset = 0
                self.section.root = self.section.root+array([self.x_offset, self.y_offset,0])
                self.section.tip = self.section.tip+array([self.x_offset, self.y_offset,0])
                self.cutting_plan.append(["return",self.x_offset])
                self.cutting_plan.append(self.section)
                self.y_offset += (self.section.bounding_box[1]-10)
        plt.show()
        for self.section in self.wings:
            print(self.section.bounding_box)
        return self.cutting_plan
    def Clear(self):
        self.wings = []
    def Add_to(self):
        self.compute_geometry()
        for i in range(int(self.copies.get())):
            self.wings.append(Wing(self.final_root, self.final_tip,int(self.wing_span_input.get())))
            if self.mirror_mode_toggle.get():
                print("mirrored")
                self.wings.append(Wing(self.final_tip, self.final_root,int(self.wing_span_input.get())))
    def Export(self):
        '''Exports path as Gcode'''
        self.cutter_commands = []
        self.cutting_plan = self.pack() #packs wings in to single cutting path
        self.coding = ""
        self.p=0
        self.gcode_plot.cla()
        print("opened "+str("test"))
        self.output = open("test"+".txt","w")
        self.coding+="G90\n M3\nG1 X0 Y0 A0 B0 F600\nG1 X0 Y-10 A0 B-10 F200\nG92 X0 Y0 A0 B0\n"#G90 set absolute positoning, M3 heat wire, G1 move to home, G1 Move down 10 mm, G92 Set current positon as home
        for self.wing_section in self.cutting_plan:
            if not isinstance(self.wing_section,(Wing)):#Moves wire to next column if return command is encountered
                print(self.wing_section)
                self.coding+="G1 X"+str(self.p)+" A"+str(self.p)+" F200\n"
                self.coding+="G1 Y10 B10 F200\n"
                self.coding+="G1 X"+str(self.wing_section[1])+" A"+str(self.wing_section[1])+"F600\n"
                self.p=self.wing_section[1]
            else:
                self.rp, self.lp = self.cuttertools.slice(self.wing_section.root,self.wing_section.tip,self.wing_section.span,int(self.x_offset_input.get()))
                self.coding+="G1 Y"+str(self.lp[0,1])+" B"+str(self.rp[0,1])+" F200\n"
                for self.index in range(len(self.lp)):
                    self.coding+="G1 X"+str(self.lp[self.index,0])+" Y"+str(self.lp[self.index,1])+" A"+str(self.rp[self.index,0])+" B"+str(self.rp[self.index,1])+" F200\n"
                self.coding+="G1 X"+str(self.lp[0,0])+" Y"+str(self.lp[0,1])+" A"+str(self.rp[0,0])+" B"+str(self.rp[0,1])+" F200\n"
                self.coding+="G1 X"+str(self.p)+" A"+str(self.p)+" F200\n"
        self.end_command = "G1 X"+str(self.p)+" A"+str(self.p)+"F200\nG1 Y10 B10 \nM3\n G1 X0 A0 F600\n" # returns the wire the the first point completing the countout cut
        self.coding+=(self.end_command)
        self.output.write(self.coding)
        self.output.close()

        print("You have arrived here")
        self.filtered = []
        for self.line in self.coding.split("\n"):
            self.q = self.parser.match(self.line)
            if self.q is not None:
                self.filtered.append(re.split('(?=[A-Z])',self.line.split("F")[0][3:].strip())[1:])
        self.C_x = 0
        self.C_y = 0
        self.C_a = 0
        self.C_b = 0
        self.extracted_root = []
        self.extracted_tip = []
        for self.line in self.filtered:
            print(self.line)
            for self.a in self.line:
                if 'X' in self.a:
                    self.C_x = float(self.a[1:])
                elif 'Y' in self.a:
                    self.C_y = float(self.a[1:])
                elif 'A' in self.a:
                    self.C_a = float(self.a[1:])
                elif 'B' in self.a:
                    self.C_b = float(self.a[1:])
            self.extracted_root.append([self.C_x, self.C_y,0])
            self.extracted_tip.append([self.C_a, self.C_b,600])
        self.extracted_root = array(self.extracted_root)
        self.extracted_tip = array(self.extracted_tip)
        print(self.extracted_root)
        self.gcode_plot.plot(self.extracted_root[:,0],self.extracted_root[:,1],self.extracted_root[:,2])
        self.gcode_plot.plot(self.extracted_tip[:,0],self.extracted_tip[:,1],self.extracted_tip[:,2])
        plt.show()
        print("closed")

    def compute_geometry(self):
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
        self.tip_x_max = max(self.new_tip_3d[:,0])
        self.tip_y_max = max(self.new_tip_3d[:,1])
        self.root_x_max = max(self.new_root_3d[:,0])
        self.root_y_max = max(self.new_root_3d[:,1])
        self.plane_offset = array([0,0,0])
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
        self.final_root,self.final_tip = self.cuttertools.generate_wing_angles(self.wing_Sweep_input.get(), self.wing_Diheadral_input.get(), self.computed_root, self.computed_tip, self.wing_span_input.get(), self.Root_chord_input.get(), self.tip_chord_input.get(), self.forward_toggle.get(), self.back_toggle.get())
        self.computed_planes_plot.cla()
        self.computed_planes_plot.plot(self.final_root[:,0],self.final_root[:,1],self.final_root[:,2],color='green')
        self.computed_planes_plot.plot(self.final_tip[:,0],self.final_tip[:,1],self.final_tip[:,2],color='blue')
        self.tip_canvas.draw()
        #self.Compute_faces()
    def Compute_faces(self):
        '''Tidying up ready for opengl'''
        self.gl_tip = self.final_tip
        self.gl_root = self.final_root
        self.gl_tip = self.gl_tip - self.gl_root.min(axis=0)
        self.gl_root = self.gl_root - self.gl_root.min(axis=0)
        self.gl_tip = self.gl_tip - self.gl_root.max(axis=0)/2
        self.gl_root = self.gl_root - self.gl_root.max(axis=0)/2
        self.gl_root[:,2] = self.gl_root[:,2] - self.gl_tip[:,2].max(axis=0)/2
        self.gl_tip[:,2]  = self.gl_tip[:,2] - self.gl_tip[:,2].max(axis=0)/2
        '''Converts coordinates to faces '''
        self.faces = ()
        self.verticies = ()
        for self.index in range(0,self.gl_tip.shape[0]-1,2):
            self.faces = self.faces + ((self.index,self.index+1))
            self.verticies = self.verticies + (tuple(self.gl_root[self.index]),tuple(self.gl_tip[self.index]))
        self.open_gl_frame.verticies = self.verticies
        self.open_gl_frame.edges = self.faces
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
        self.true_tip_foil = self.cuttertools.generate_foil(self.tip_data,int(self.tip_alpha_input.get()),float(self.tip_twist_percentage_input.get()),float(self.tip_chord_input.get()))
        self.true_tip_plot.cla()
        self.true_tip_plot.plot(self.true_tip_foil[:,0],self.true_tip_foil[:,1])
        self.true_tip_canvas.draw()
if __name__ == "__main__":
    GUI(None)
