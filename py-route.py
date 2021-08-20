from tkinter import *
from tkinter import font
from tkinter.filedialog import askopenfilename
from PIL import ImageDraw, ImageTk
import PIL.Image
import numpy as np
from np_Gauss import gauss
import math
from xml.dom import minidom

class myTrack():
    def __init__(self, gpx_path):
        #-------------------------------------------------------------------------------
        # ADOPTED FROM "GPX TRACK VISUALIZER ideagora geomatics-2018 http://www.geodose.com/"
        #-------------------------------------------------------------------------------
        #READ GPX FILE
        data=open(gpx_path)
        xmldoc = minidom.parse(data)
        track = xmldoc.getElementsByTagName('trkpt')
        elevation=xmldoc.getElementsByTagName('ele')
        datetime=xmldoc.getElementsByTagName('time')
        self.n_track=len(track)
        #PARSING GPX ELEMENT
        self.lon_list=[]
        self.lat_list=[]
        self.h_list=[]
        self.time_list=[]
        for s in range(self.n_track):
            lon,lat=track[s].attributes['lon'].value,track[s].attributes['lat'].value
            elev=elevation[s].firstChild.nodeValue
            self.lon_list.append(float(lon))
            self.lat_list.append(float(lat))
            self.h_list.append(float(elev))
            # PARSING TIME ELEMENT
            dt=datetime[s+1].firstChild.nodeValue #skip the first datatime[], which is in the header
            time_split=dt.split('T')
            hms_split=time_split[1].split(':')
            time_hour=int(hms_split[0])
            time_minute=int(hms_split[1])
            time_second=int(hms_split[2].split('.')[0])
            total_second=time_hour*3600+time_minute*60+time_second
            self.time_list.append(total_second)
        #POPULATE DISTANCE AND SPEED LIST
        self.d_list=[0.0]
        self.speed_list=[0.0]
        for k in range(1, self.n_track):
            l=k-1
            XY0=self.geo2cart(self.lon_list[l],self.lat_list[l],self.h_list[l])
            XY1=self.geo2cart(self.lon_list[k],self.lat_list[k],self.h_list[k])
            #DISTANCE
            d=self.distance(XY0[0],XY0[1],XY1[0],XY1[1])
            sum_d=d+self.d_list[-1]
            self.d_list.append(sum_d)
            #SPEED
            s=self.speed(XY0[0],XY0[1],XY1[0],XY1[1],self.time_list[l],self.time_list[k])
            self.speed_list.append(s)
    #GEODETIC TO CARTERSIAN FUNCTION
    def geo2cart(self,lon,lat,h):
        a=6378137 #WGS 84 Major axis
        b=6356752.3142 #WGS 84 Minor axis
        e2=1-(b**2/a**2)
        N=float(a/math.sqrt(1-e2*(math.sin(math.radians(abs(lat)))**2)))
        X=(N+h)*math.cos(math.radians(lat))*math.cos(math.radians(lon))
        Y=(N+h)*math.cos(math.radians(lat))*math.sin(math.radians(lon))
        return X,Y
    #DISTANCE FUNCTION
    def distance(self,x1,y1,x2,y2):
        d=math.sqrt((x1-x2)**2+(y1-y2)**2)
        return d
    #SPEED FUNCTION
    def speed(self,x1,y1,x2,y2,t1,t2):
        d=math.sqrt((x1-x2)**2+(y1-y2)**2)
        delta_t=t2-t1
        s=float(d/delta_t)
        return s

class myRoute:
    def __init__(self, width_canvas, height_canvas, root):
        self.root = root
        width_cal = 10
        width_btn = 12
        #DEFAULT VALUES
        self.colormap=['blue', 'turquoise', 'green', 'yellow green', 'tomato', 'red', 'deep pink', 'purple']
        self.w_canvas = width_canvas
        self.h_canvas = height_canvas
        self.last_route_percent=0
        self.current_route_percent=0
        #POINTS USED TO CALIBRATION
        self.cursor_x, self.cursor_y = 0, 0
        self.P1, self.P2, self.P3 = 0, 0, 0
        #MAP AND ROUTE OVERLAY STATUS
        self.whole_route_drawn=0
        self.map_shown=0
        #MANUUAL ROUTE SLIDER
        self.slided_route=[]
        self.coeff_x = np.array([1,0,0],float)
        self.coeff_y = np.array([0,1,0],float)
        #FONTS
        helv = font.Font(family='Helvetica', size=10, weight='bold')
        #CHOOSE MAP FILE
        self.frame_mapfile = LabelFrame(self.root, text="MAP file")
        self.frame_mapfile['font'] = helv
        self.frame_mapfile.grid(row=0, column=0, columnspan=2, sticky=E+W, padx=5, pady=5)
        self.frame_mapfile.columnconfigure(0, weight=1)
        self.frame_mapfile.columnconfigure(1, weight=4)
        self.button_mapfile = Button(self.frame_mapfile, text="Browse", width=width_btn, command=lambda: self.open_file('map'))
        self.entry_map = Entry(self.frame_mapfile, width=40)
        self.button_mapfile.grid(row=0, column=0, padx=5, pady=5)
        self.entry_map.grid(row=0, column=1, padx=5, pady=5)
        #CHOOSE GPX FILE
        self.frame_gpxfile = LabelFrame(self.root, text="GPX file")
        self.frame_gpxfile['font'] = helv
        self.frame_gpxfile.grid(row=1, column=0, columnspan=2, sticky=E+W,padx=5, pady=5)
        self.frame_gpxfile.columnconfigure(0, weight=1)
        self.frame_gpxfile.columnconfigure(1, weight=4)
        self.button_gpxfile = Button(self.frame_gpxfile, text="Browse", width=width_btn, command=lambda: self.open_file('gpx'))
        self.entry_gpx = Entry(self.frame_gpxfile, width=40)

        self.button_gpxfile.grid(row=0, column=0, columnspan=1, padx=5, pady=5)
        self.entry_gpx.grid(row=0, column=1, padx=5, pady=5)
        #MAP SIZE
        # put two labels here for height and width of the map file
        # or not?
        #MAP CALIBRATION
        self.frame_mapcal = LabelFrame(self.root, text="MAP Calibration")
        self.frame_mapcal['font'] = helv
        self.frame_mapcal.grid(row=2, column=0, columnspan=2, rowspan=1, sticky=N+E+W, padx=5, pady=5)
        #USE 3 POINTS TO CALIBRATE THE MAP
        for i in range(5):
            self.frame_mapcal.columnconfigure(i, weight=1)
        Label(self.frame_mapcal, text='X').grid(row=0, column=1, padx=5, pady=5)
        Label(self.frame_mapcal, text='Y').grid(row=0, column=2, padx=5, pady=5)
        Label(self.frame_mapcal, text='Longitude').grid(row=0, column=3, padx=5, pady=5)
        Label(self.frame_mapcal, text='Latitude').grid(row=0, column=4, padx=5, pady=5)
        #P1
        Label(self.frame_mapcal, fg='red', text='P1').grid(row=1, column=0, padx=5, pady=5)
        self.entry_x1=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='red')
        self.entry_x1.grid(row=1, column=1, padx=5, pady=5)
        self.entry_y1=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='red')
        self.entry_y1.grid(row=1, column=2, padx=5, pady=5)
        self.entry_lon1=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='red')
        self.entry_lon1.grid(row=1, column=3, padx=5, pady=5)
        self.entry_lat1=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='red')
        self.entry_lat1.grid(row=1, column=4, padx=5, pady=5)
        #P2
        Label(self.frame_mapcal, fg='green4', text='P2').grid(row=2, column=0, padx=5, pady=5)
        self.entry_x2=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='green4')
        self.entry_x2.grid(row=2, column=1, padx=5, pady=5)
        self.entry_y2=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='green4')
        self.entry_y2.grid(row=2, column=2, padx=5, pady=5)
        self.entry_lon2=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='green4')
        self.entry_lon2.grid(row=2, column=3, padx=5, pady=5)
        self.entry_lat2=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='green4')
        self.entry_lat2.grid(row=2, column=4, padx=5, pady=5)
        #P3
        Label(self.frame_mapcal, fg='blue', text='P3').grid(row=3, column=0, padx=5, pady=5)
        self.entry_x3=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='blue')
        self.entry_x3.grid(row=3, column=1, padx=5, pady=5)
        self.entry_y3=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='blue')
        self.entry_y3.grid(row=3, column=2, padx=5, pady=5)
        self.entry_lon3=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='blue')
        self.entry_lon3.grid(row=3, column=3, padx=5, pady=5)
        self.entry_lat3=Entry(self.frame_mapcal,width=width_cal,justify='center', fg='blue')
        self.entry_lat3.grid(row=3, column=4, padx=5, pady=5)
        #DATA FOR CHILSON MAP
        #self.entry_x1.insert(0, '19'); self.entry_y1.insert(0, '192');
        #self.entry_lon1.insert(0, '-83.900289'); self.entry_lat1.insert(0, '42.508828');
        #self.entry_x2.insert(0, '1067'); self.entry_y2.insert(0, '423');
        #self.entry_lon2.insert(0, '-83.858695'); self.entry_lat2.insert(0, '42.506322');
        #self.entry_x3.insert(0, '529'); self.entry_y3.insert(0, '144');
        #self.entry_lon3.insert(0, '-83.880742'); self.entry_lat3.insert(0, '42.511788');
        #CALIBRATION BUTTON
        self.button_mapCali = Button(self.frame_mapcal, width=width_btn,text="Calibrate", command=self.calibrate)
        self.button_mapCali['font'] = helv
        self.button_mapCali.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        #CONVERSION COEFFICIENT
        Label(self.frame_mapcal, text='Ax*Longitude').grid(row=5, column=2, padx=5, pady=5)
        Label(self.frame_mapcal, text='+Bx*Latitude').grid(row=5, column=3, padx=5, pady=5)
        Label(self.frame_mapcal, text='+Cx').grid(row=5, column=4, padx=5, pady=5)
        Label(self.frame_mapcal, text='X =').grid(row=6, column=1, sticky=E, padx=5, pady=5)
        self.entry_ax=Entry(self.frame_mapcal,width=width_cal,justify='center')
        self.entry_ax.grid(row=6, column=2, padx=5, pady=5)
        self.entry_bx=Entry(self.frame_mapcal,width=width_cal,justify='center')
        self.entry_bx.grid(row=6, column=3, padx=5, pady=5)
        self.entry_cx=Entry(self.frame_mapcal,width=width_cal,justify='center')
        self.entry_cx.grid(row=6, column=4, padx=5, pady=5)
        Label(self.frame_mapcal, text='Ay*Longitude').grid(row=7, column=2, padx=5, pady=5)
        Label(self.frame_mapcal, text='+By*Latitude').grid(row=7, column=3, padx=5, pady=5)
        Label(self.frame_mapcal, text='+Cy').grid(row=7, column=4, padx=5, pady=5)
        Label(self.frame_mapcal, text='Y =').grid(row=8, column=1, sticky=E, padx=5, pady=5)
        self.entry_ay=Entry(self.frame_mapcal,width=width_cal,justify='center')
        self.entry_ay.grid(row=8, column=2, padx=5, pady=5)
        self.entry_by=Entry(self.frame_mapcal,width=width_cal,justify='center')
        self.entry_by.grid(row=8, column=3, padx=5, pady=5)
        self.entry_cy=Entry(self.frame_mapcal,width=width_cal,justify='center')
        self.entry_cy.grid(row=8, column=4, padx=5, pady=5)
        #COMMAND BUTTONS
        self.frame_buttons = LabelFrame(self.root, relief=GROOVE)
        self.frame_buttons.grid(row=3, column=0, columnspan=2, rowspan=1, sticky=W+E, padx=5, pady=5)
        for i in range(3):
            self.frame_buttons.columnconfigure(i, weight=1)
        self.button_drawMap = Button(self.frame_buttons, width=width_btn, text="Show Map", command=self.drawMap)
        self.button_drawMap['font'] = helv
        self.button_drawMap.grid(row=0, column=0, padx=5, pady=5)
        self.button_drawTrack = Button(self.frame_buttons, width=width_btn, text="Full Route", command=self.drawRoute)
        self.button_drawTrack['font'] = helv
        self.button_drawTrack.grid(row=0, column=1, padx=5, pady=5)
        self.button_clear = Button(self.frame_buttons, width=width_btn, text="Clear All", command=self.clear)
        self.button_clear['font'] = helv
        self.button_clear.grid(row=0, column=2, padx=5, pady=5)
        self.button_exit = Button(self.frame_buttons, width=width_btn, text="Exit", command=self.root.destroy)
        self.button_exit['font'] = helv
        self.button_exit.grid(row=1, column=2, columnspan=3, padx=5, pady=5)
        #COLOR BAR
        self.frame_colorbar = Frame(self.root)
        self.frame_colorbar.grid(row=4, column=0, columnspan=2, rowspan=3, sticky=W+E, padx=5, pady=5)
        for i in range(len(self.colormap)):
            self.frame_colorbar.columnconfigure(i, weight=1)
        Label(self.frame_colorbar, text='slow').grid(row=1, column=0, sticky=E+W, padx=2, pady=2)
        Label(self.frame_colorbar, text='fast').grid(row=1, column=len(self.colormap)-1, sticky=E+W, padx=2, pady=2)
        for i in range(len(self.colormap)):
            Button(self.frame_colorbar, bd=0, bg=self.colormap[i]).grid(row=0, column=i, columnspan=1, sticky=E+W, pady=2)

        #CANVAS FOR MAP AND ROUTE
        self.frame_canvas = Frame(self.root, bg="white")
        self.frame_canvas.grid(row=0, column=2, columnspan=8, rowspan=7, padx=5, pady=5)
        self.canvas = Canvas(self.frame_canvas, width=self.w_canvas, height=self.h_canvas, background='white')
        self.canvas.grid(sticky=W+E+N+S, padx=2, pady=2)
        self.canvas.bind("<Button-3>", self.popup_canvas)
        #POPUP MENU TO ADD CALIBRATION POINT
        self.pop_add_cal = Menu(self.canvas, tearoff = 0)
        self.pop_add_cal.add_command(label ="add P1", command=lambda: self.addXY("P1"))
        self.pop_add_cal.add_command(label ="add P2", command=lambda: self.addXY("P2"))
        self.pop_add_cal.add_command(label ="add P3", command=lambda: self.addXY("P3"))
        #SLIDER BAR
        self.route_slider = Scale(self.root, from_=0, to=500, width=30, length=self.w_canvas, sliderlength=20,
                                  tickinterval=0, showvalue=0, orient=HORIZONTAL, troughcolor='yellow',
                                  command = self.updateRoute)
        #self.route_slider.bind("<ButtonRelease-1>", self.updateRoute)
        self.route_slider.grid(row=7, column=2, padx=5, pady=5)

        #SET DEFAULT STATE OF BUTTONS
        self.button_drawMap.configure(state=DISABLED)
        self.button_drawTrack.configure(state=DISABLED)
        self.route_slider.configure(state=DISABLED, takefocus=0)

    def open_file(self,filetype):
        if filetype=='map':
            entry=self.entry_map
            a, b = 'MAP(Image) Files', '*.png *.gif *.jpg *.jpeg'
        elif filetype=='gpx':
            entry=self.entry_gpx
            a, b = 'GPX Files', '*.gpx'
        pop_title='Open '+filetype+' files'
        filename = askopenfilename(title=pop_title, filetypes=[(a, b),('All Files', '*.*')])
        if filename:
            entry.delete(0,END)
            entry.insert(0,filename)
            entry.update_idletasks()
            entry.xview_scroll(len(entry.get()), UNITS)
            if filetype=='map':
                self.button_drawMap.configure(state=NORMAL)
                self.map_shown=0
                self.drawMap()
            elif filetype=='gpx':
                self.track = myTrack(self.entry_gpx.get())
                self.max_speed = max(self.track.speed_list)
                self.button_drawTrack.configure(state=NORMAL)
                self.route_slider.configure(state=NORMAL, takefocus=1)
        return

    def popup_canvas(self, event):
        try:
            self.pop_add_cal.tk_popup(event.x_root, event.y_root)
            self.cursor_x, self.cursor_y = event.x, event.y
        finally:
            self.pop_add_cal.grab_release()
        return

    def addXY(self, P):
        markersize=10
        if P=="P1":
            if self.P1:
                self.canvas.delete(self.P1)
            self.entry_x1.delete(0,"end"); self.entry_x1.insert(0, self.cursor_x)
            self.entry_y1.delete(0,"end"); self.entry_y1.insert(0, self.cursor_y)
            self.P1 = self.canvas.create_oval(self.cursor_x-markersize, self.cursor_y-markersize,
                                              self.cursor_x+markersize, self.cursor_y+markersize, width=2, outline='red')
        elif P=="P2":
            if self.P1:
                self.canvas.delete(self.P2)
            self.entry_x2.delete(0,"end"); self.entry_x2.insert(0, self.cursor_x)
            self.entry_y2.delete(0,"end"); self.entry_y2.insert(0, self.cursor_y)
            self.P2 = self.canvas.create_oval(self.cursor_x-markersize, self.cursor_y-markersize,
                                              self.cursor_x+markersize, self.cursor_y+markersize, width=2, outline='green4')
        elif P=="P3":
            if self.P1:
                self.canvas.delete(self.P3)
            self.entry_x3.delete(0,"end"); self.entry_x3.insert(0, self.cursor_x)
            self.entry_y3.delete(0,"end"); self.entry_y3.insert(0, self.cursor_y)
            self.P3 = self.canvas.create_oval(self.cursor_x-markersize, self.cursor_y-markersize,
                                              self.cursor_x+markersize, self.cursor_y+markersize, width=2, outline='blue')
        return

    def drawMap(self):
        if self.map_shown==1: return
        map_image = PIL.Image.open(self.entry_map.get())
        self.w_map, self.h_map = map_image.size
        map_image = map_image.resize((self.w_canvas, self.h_canvas), PIL.Image.ANTIALIAS)
        self.map_img = ImageTk.PhotoImage(map_image)
        self.canvas.create_image(0,0, anchor=NW, image=self.map_img)
        self.map_shown=1
        self.route_slider.set(0)
        return

    def calibrate(self):
        self.drawMap()
        #CALCULATE THE CONVERSION MATRIX BETWEEN LONGITUDE_LATITUDE AND CANVAS_XY
        gpsx = np.array([[self.entry_lon1.get(), self.entry_lat1.get(), 1],
                         [self.entry_lon2.get(), self.entry_lat2.get(), 1],
                         [self.entry_lon3.get(), self.entry_lat3.get(), 1]], float)
        mpx = np.array([self.entry_x1.get(), self.entry_x2.get(), self.entry_x3.get()], float)
        #mpx = mpx * self.w_canvas/self.w_map
        gpsy = np.array([[self.entry_lon1.get(), self.entry_lat1.get(), 1],
                         [self.entry_lon2.get(), self.entry_lat2.get(), 1],
                         [self.entry_lon3.get(), self.entry_lat3.get(), 1]], float)
        mpy = np.array([self.entry_y1.get(), self.entry_y2.get(), self.entry_y3.get()], float)
        #mpy = mpy * self.h_canvas/self.h_map
        self.coeff_x = gauss(gpsx, mpx)
        self.entry_ax.insert(0, self.coeff_x[0]); self.entry_bx.insert(0, self.coeff_x[1]); self.entry_cx.insert(0, self.coeff_x[2]);
        self.coeff_y = gauss(gpsy, mpy)
        self.entry_ay.insert(0, self.coeff_y[0]); self.entry_by.insert(0, self.coeff_y[1]); self.entry_cy.insert(0, self.coeff_y[2]);
        return

    def drawRoute(self):
        if self.whole_route_drawn==1: return
        #DRAW TRACK ON THE CANVAS
        for i in range (self.track.n_track):
            scatter_size = 2
            x0 = (self.coeff_x[0]*self.track.lon_list[i] + self.coeff_x[1]*self.track.lat_list[i] + self.coeff_x[2])
            y0 = (self.coeff_y[0]*self.track.lon_list[i] + self.coeff_y[1]*self.track.lat_list[i] + self.coeff_y[2])
            x1, y1 = (x0 - scatter_size), (y0 - scatter_size)
            x2, y2 = (x0 + scatter_size), (y0 + scatter_size)
            color_route = self.colormap[int(7*self.track.speed_list[i]/self.max_speed)]
            self.canvas.create_oval(x1, y1, x2, y2, width=1, outline= 'black', fill=color_route)
        self.whole_route_drawn=1
        self.route_slider.set(0)
        return

    def updateRoute(self,event):
        #UPDATE THE ROUTE
        self.current_route_percent=self.track.n_track*self.route_slider.get()/500
        if self.current_route_percent>self.last_route_percent:
            for i in range (int(self.last_route_percent), int(self.current_route_percent)):
                scatter_size = 2
                x0 = (self.coeff_x[0]*self.track.lon_list[i] + self.coeff_x[1]*self.track.lat_list[i] + self.coeff_x[2])
                y0 = (self.coeff_y[0]*self.track.lon_list[i] + self.coeff_y[1]*self.track.lat_list[i] + self.coeff_y[2])
                x1, y1 = (x0 - scatter_size), (y0 - scatter_size)
                x2, y2 = (x0 + scatter_size), (y0 + scatter_size)
                self.slided_route.append(self.canvas.create_oval(x1, y1, x2, y2, width=1, outline="blue", fill="blue"))
        else:
            for i in range (int(self.current_route_percent), int(self.last_route_percent)):
                self.canvas.delete(self.slided_route[len(self.slided_route)-1])
                del(self.slided_route[len(self.slided_route)-1])
        self.last_route_percent=self.current_route_percent
        return

    def clear(self):
        #self.output.set(self.track.n_track)
        self.canvas.delete("all")
        self.whole_route_drawn=0
        self.map_shown=0
        self.last_route_percent=0
        self.route_slider.set(0)
        self.img_content = PIL.Image.fromarray(np.zeros((self.w_canvas, self.h_canvas)))
        self.img_content = self.img_content.convert("1")
        self.draw = ImageDraw.Draw(self.img_content)
        return

def center(win):
    """
    centers a tkinter window
    :param win: the root or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    #y = win.winfo_screenheight() // 2 - win_height // 2
    y = 0
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

def main():
    #CONVERT GPX TO TRACK ARRAY
    #data=myTrack("garmin chilson.gpx")
    #START THE GUI
    root = Tk()
    root.title('py-route')
    width, height = 1100, 720
    myRoute(width, height, root)
    center(root)
    root.resizable(False, False)
    root.mainloop()
    return

if __name__ == '__main__':
    main()



