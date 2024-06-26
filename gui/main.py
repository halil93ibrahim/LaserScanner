from tkinter import *
from tkinter import messagebox
from pymodbus.client.sync import ModbusSerialClient
import time
import threading
import queue
import numpy as np
import datetime

global dm1, filewin, filewin, lower_bound_entry, upper_bound_entry
mb_com = 'COM3'
plc_mb_add = 0x02
dtc_mb_add = 0x01
laser_read_add = 4096
status_flag_add = 2048
run_flag_add = 2049
motor_flag_add = 2050
dir_flag_add = 2051
stop_flag_add = 2052
count_add = 3584
count_add1 = 3585
scale = 80
lower_bound = 290
upper_bound = 1310
adc_low = 1600
adc_high = 9999
x_lim = 1500  # mm
y_lim = 3000  # mm
# m = 1017.6/8359
# b = 98.128322
# 9978 1310.5
# 1603 292.9


class GuiPart:
    def __init__(self, master, frame1, frame2, queue, strt_fnc, stp_fnc, go_fnc, hm_fnc, read_laser_fnc, switch_fnc):
        self.queue = queue

        # buttons
        strt = Button(frame2, text="Start", command=strt_fnc, width=10)
        strt.grid(column=1, row=2, padx=10, pady=10)
        stp = Button(frame2, text="Stop", command=stp_fnc, width=10)
        stp.grid(column=3, row=2, padx=10, pady=10)
        go = Button(frame1, text="Go", command=go_fnc, width=10)
        go.grid(column=0, row=1, padx=10, pady=10)
        stp1 = Button(frame1, text="Stop", command=stp_fnc, width=10)
        stp1.grid(column=1, row=1, padx=10, pady=10)
        hm = Button(frame1, text="Home", command=hm_fnc, width=10)
        hm.grid(column=3, row=1, padx=10, pady=10)
        read_laser = Button(frame1, text="Read Laser", command=read_laser_fnc, width=10)
        read_laser.grid(column=2, row=1, padx=10, pady=10)
        switch = Scale(frame2, orient=HORIZONTAL, length=50, to=1, showvalue=False, sliderlength=25, command=switch_fnc)
        switch.grid(column=0, row=1, padx=10, pady=0)
        # switch_lbl_txt = "Search direction X-Y"



class ThreadedClient:
    state = 0  # state of the process
    count = 0  # distance in mm
    success = 0  # indicate whether motor reaches its destination
    motor_flag = 0  # chose a motor to drive, 1 for motor in x, 0 for motor in y
    dir_flag = 0  # direction of a motor, 1 for pos, 0 for neg

    def __init__(self, master, frame1, frame2, plc_mb_add, dtc_mb_add, status_flag_add, run_flag_add,
                 motor_flag_add, dir_flag_add, stop_flag_add, count_add, count_add1, scale, laser_read_add,x_lim,y_lim):

        self.master = master
        self.frame1 = frame1
        self.frame2 = frame2
        self.queue = queue.Queue()
        self.plc_mb_add = plc_mb_add
        self.dtc_mb_add = dtc_mb_add
        self.status_flag_add = status_flag_add
        self.run_flag_add = run_flag_add
        self.motor_flag_add = motor_flag_add
        self.dir_flag_add = dir_flag_add
        self.stop_flag_add = stop_flag_add
        self.count_add = count_add
        self.count_add1 = count_add1
        self.scale = scale
        self.laser_read_add = laser_read_add
        self.gui = GuiPart(master, self.frame1, self.frame2, self.queue, self.strt_func, self.stp_func, self.go_func,
                           self.hm_func, self.read_laser_fnc, self.switch_fnc)
        self.switch_lbl = Label(self.frame2, text="Search direction X-Y")
        self.switch_lbl.grid(column=0, row=0)
        self.xy = 1
        self.x_pos = 0
        self.y_pos = 0
        self.x_lim = x_lim
        self.y_lim = y_lim
        self.running = 0
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

    def workerThread1(self):

        # thread works in a infinite loop
        while 1:
            time.sleep(0.1)
            # scan grid
            if self.state == 1:
                dir = True  # set direction to pos

                if self.xy == 1:
                    nx = int(nx_entry.get())  # number of data points in x
                    ny = int(ny_entry.get())  # number of data points in y
                    x_res = int(x_res_entry.get())  # measurement resolution in x
                    y_res = int(y_res_entry.get())  # measurement resolution in y
                else:
                    ny = int(nx_entry.get())  # number of data points in x
                    nx = int(ny_entry.get())  # number of data points in y
                    y_res = int(x_res_entry.get())  # measurement resolution in x
                    x_res = int(y_res_entry.get())  # measurement resolution in y

                data = np.zeros((ny, nx))  # recorded data

                for y in range(0, int(ny)):
                    for x in range(0, int(nx) - 1):

                        # read laser
                        time.sleep(0.1)

                        result = client.read_holding_registers(self.laser_read_add, count=1, unit=self.dtc_mb_add)
                        if dir == True:
                            index_x = x
                        else:
                            index_x = nx - 1 - x
                        # record laser data
                        data[y][index_x] = round((result.registers[0] - adc_low) / (adc_high - adc_low) *
                                                 (upper_bound - lower_bound) + lower_bound, 2)
                        if self.xy == 1:
                            self.motor_flag = 1
                        else:
                            self.motor_flag = 0

                        self.count = x_res
                        self.dir_flag = dir

                        while self.success != 1 and self.running:
                            self.run_motor()
                            time.sleep(0.1)

                        self.success = 0

                        if self.running == 0:
                            break
                    if self.running == 0:
                        break
                    if not 'x' in locals():
                        x = -1

                    # read laser
                    result = client.read_holding_registers(self.laser_read_add, count=1, unit=self.dtc_mb_add)
                    if dir == True:
                        index_x = x + 1
                    else:
                        index_x = nx - 1 - x - 1

                    # record laser data
                    data[y][index_x] = round((result.registers[0] - adc_low) / (adc_high-adc_low) *
                                             (upper_bound - lower_bound) + lower_bound, 2)
                    # print(data[y][index_x])

                    # change direction in x for next row
                    dir = not dir

                    if y != int(ny) - 1:
                        if self.xy == 1:
                            self.motor_flag = 0
                        else:
                            self.motor_flag = 1

                        self.count = y_res
                        self.dir_flag = 1

                        while self.success != 1 and self.running:
                            self.run_motor()
                            time.sleep(0.1)

                    self.success = 0

                # save to a txt file
                # print(data)
                dummy = data
                np.savetxt('data' + datetime.date.today().__str__() + '-' +
                           datetime.datetime.now().timestamp().__str__() + '.txt', dummy, fmt="%.2f")

                # change state of the process
                self.state = 0

            # homming
            if self.state == 2:
                self.count = -2000
                # set direction
                if self.count < 0:
                    self.dir_flag = 0
                    self.count = -1 * self.count
                else:
                    self.dir_flag = 1

                self.motor_flag = 1  # choose motor in x direction

                while self.success != 1 and self.running:
                    self.run_motor()
                    time.sleep(0.1)

                self.success = 0
                self.count = -4000

                # set direction
                if self.count < 0:
                    self.dir_flag = 0
                    self.count = -1 * self.count
                else:
                    self.dir_flag = 1

                self.motor_flag = 0  # choose motor in x direction

                while self.success != 1 and self.running:
                    self.run_motor()
                    time.sleep(0.1)

                self.success = 0
                self.state = 0

            # go desired position
            if self.state == 3:
                self.count = int(go_x_entry.get())

                if self.count != 0:
                    # set direction
                    if self.count < 0:
                        self.dir_flag = 0
                        self.count = -1 * self.count
                    else:
                        self.dir_flag = 1

                    self.motor_flag = 1  # choose motor in x direction

                    while self.success != 1 and self.running:
                        self.run_motor()
                        time.sleep(0.1)

                self.success = 0
                self.count = int(go_y_entry.get())

                if self.count != 0:
                    # set direction
                    if self.count < 0:
                        self.dir_flag = 0
                        self.count = -1 * self.count
                    else:
                        self.dir_flag = 1

                    self.motor_flag = 0  # choose motor in y direction

                    while self.success != 1 and self.running:
                        self.run_motor()
                        time.sleep(0.1)

                self.success = 0
                self.state = 0

    def strt_func(self):
        try:
            nx = int(nx_entry.get())  # number of data points in x
            ny = int(ny_entry.get())  # number of data points in y
            x_res = int(x_res_entry.get())  # measurement resolution in x
            y_res = int(y_res_entry.get())  # measurement resolution in y
        except:
            messagebox.showerror("Invalid Input", "Input must be an integer")
            return

        if ((nx*x_res + self.x_pos) > self.x_lim) or ((ny*y_res + self.y_pos) > self.y_lim):
            messagebox.showerror("Laser Scanner Limit Exceeding", "Input exceeds Laser Scanner limits")
        else:
            self.running = 1
            self.state = 1

    def stp_func(self):
        client.write_coil(self.stop_flag_add, 1, unit=self.plc_mb_add)
        self.running = 0

    def hm_func(self):
        self.running = 1
        self.state = 2

    def go_func(self):
        try:
            go_x = int(go_x_entry.get())
            go_y = int(go_y_entry.get())
        except:
            messagebox.showerror("Invalid Input", "Input must be an integer")
            return

        if ((go_x + self.x_pos) > self.x_lim) or ((go_y + self.y_pos) > self.y_lim):
            messagebox.showerror("Laser Scanner Limit Exceeding", "Input exceeds Laser Scanner limits")
        else:
            self.running = 1
            self.state = 3

    def run_motor(self):
        result = client.read_coils(self.status_flag_add, 1, unit=self.plc_mb_add)
        if result.bits[0] == False:
            client.write_coil(self.motor_flag_add, self.motor_flag, unit=self.plc_mb_add)
            time.sleep(0.01)
            step_value = self.count * self.scale
            client.write_registers(self.count_add, step_value % 65535, unit=self.plc_mb_add)
            time.sleep(0.01)
            client.write_registers(self.count_add1, int(step_value / 65535), unit=self.plc_mb_add)
            time.sleep(0.01)
            client.write_coil(self.dir_flag_add, self.dir_flag, unit=self.plc_mb_add)
            time.sleep(0.01)
            client.write_coil(self.run_flag_add, 1, unit=self.plc_mb_add)
            time.sleep(0.01)
            result = client.read_coils(self.status_flag_add, 1, unit=self.plc_mb_add)

            while result.bits[0] == True:
                result = client.read_coils(self.status_flag_add, 1, unit=self.plc_mb_add)
                time.sleep(0.01)

            self.success = 1
        else:
            self.success = 0

    def read_laser_fnc(self):
        result = client.read_holding_registers(self.laser_read_add, unit=self.dtc_mb_add)
        print(round((result.registers[0] - adc_low) / (adc_high-adc_low) *
                                             (upper_bound - lower_bound) + lower_bound, 2))

    def switch_fnc(self, value):

        if value == "1":
            self.xy = 0
            self.switch_lbl.config(text="Search direction Y-X")
        else:
            self.xy = 1
            self.switch_lbl.config(text="Search direction X-Y")


window = Tk()
window.title("Laser Scanner GUI")
window.geometry('620x300')


def com_callback():
    global mb_com, dm1, filewin
    mb_com = dm1.get()
    filewin.destroy()


def donothing():
    global dm1, filewin
    filewin = Toplevel(window)
    dm = Label(filewin, text="COM Port (COMX):")
    dm.grid(column=0, row=0, padx=10, pady=10)
    dm1 = Entry(filewin, width=10)
    dm1.insert(END, mb_com)
    dm1.grid(column=1, row=0, padx=10)
    dm2 = Button(filewin, text="Ok", width=10, command=com_callback)
    dm2.grid(column=1, row=1, pady=10)


def range_callback():
    global filewin1, lower_bound_entry, upper_bound_entry, lower_bound, upper_bound
    upper_bound = upper_bound_entry.get()
    lower_bound = lower_bound_entry.get()
    filewin1.destroy()


def donothing1():
    global filewin1, lower_bound_entry, upper_bound_entry
    filewin1 = Toplevel(window)
    dmy = Label(filewin1, text="Upper Bound (mm):")
    dmy.grid(column=0, row=0, padx=10, pady=10)
    upper_bound_entry = Entry(filewin1, width=10)
    upper_bound_entry.insert(END, str(upper_bound))
    upper_bound_entry.grid(column=1, row=0, padx=10)
    dmy1 = Label(filewin1, text="Lower Bound (mm):")
    dmy1.grid(column=0, row=1, padx=10, pady=10)
    lower_bound_entry = Entry(filewin1, width=10)
    lower_bound_entry.insert(END, str(lower_bound))
    lower_bound_entry.grid(column=1, row=1, padx=10)
    dmy2 = Button(filewin1, text="Ok", width=10, command=range_callback)
    dmy2.grid(column=1, row=2, pady=10)


def donothing2():
    messagebox.showinfo("Source Code", "Visit https://github.com/halil93ibrahim/LaserScanner")


def donothing3():
    messagebox.showinfo("About", "Developed by\n \tKARDELEN MÜHENDİSLİK VE OTOMASYON\n \tHalil Ibrahim Ugurlu\n "
                                 "\tOsman Kaan Karagoz\n Report bugs or request enhancements to:\n "
                                 "\thalil93ibrahim@gmail.com\n \tkaragozosmankaan@gmail.com")


menubar = Menu(window)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Communication", command=donothing)
filemenu.add_command(label="Measurement Range", command=donothing1)
menubar.add_cascade(label="Settings", menu=filemenu)

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Source Code", command=donothing2)
helpmenu.add_command(label="About", command=donothing3)
menubar.add_cascade(label="Help", menu=helpmenu)

window.config(menu=menubar)

lblg = Label(window, text="Manual Control")
lblg.grid(column=0, row=0, padx=10, pady=10)

frame1 = Frame(window, width=450, height=300, bd=2, relief=SUNKEN)
frame1.grid(row=1, column=0, padx=10)

lblstg = Label(window, text="Grid Scanning")
lblstg.grid(column=0, row=2, padx=10, pady=10)

frame2 = Frame(window, width=450, height=300, bd=2, relief=SUNKEN)
frame2.grid(row=3, column=0, padx=10)

lblgx = Label(frame1, text="X (mm):")
lblgx.grid(column=0, row=0, pady=10)
go_x_entry = Entry(frame1, width=10)
go_x_entry.grid(column=1, row=0)

lblgy = Label(frame1, text="Y (mm):")
lblgy.grid(column=2, row=0)
go_y_entry = Entry(frame1, width=10)
go_y_entry.grid(column=3, row=0)

lblx = Label(frame2, text="X Resolution (mm):")
lblx.grid(column=1, row=0, padx=10, pady=10)
x_res_entry = Entry(frame2, width=10)
x_res_entry.grid(column=2, row=0)

lblx1 = Label(frame2, text="Number of Data Points In X:")
lblx1.grid(column=3, row=0, padx=10)
nx_entry = Entry(frame2, width=10)
nx_entry.grid(column=4, row=0, padx=10)

lbly = Label(frame2, text="Y Resolution (mm):")
lbly.grid(column=1, row=1)
y_res_entry = Entry(frame2, width=10)
y_res_entry.grid(column=2, row=1)

lbly1 = Label(frame2, text="Number of Data Points In Y:")
lbly1.grid(column=3, row=1)
ny_entry = Entry(frame2, width=10)
ny_entry.grid(column=4, row=1)

# Create a thread for the process
th_client = ThreadedClient(window, frame1, frame2, plc_mb_add, dtc_mb_add, status_flag_add, run_flag_add,
                           motor_flag_add, dir_flag_add, stop_flag_add, count_add, count_add1, scale, laser_read_add,
                           x_lim, y_lim)

# Set Modbus Client
client = ModbusSerialClient('ascii', port=mb_com, stopbits=1, bytesize=7, parity='E', baudrate=9600)
window.mainloop()
