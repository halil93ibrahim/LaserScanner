from tkinter import *
from pymodbus.client.sync import ModbusSerialClient
import time
import threading
import queue

mb_com = 'COM11'
plc_mb_add = 0x02
dtc_mb_add = 0x01
status_flag_add = 2048
run_flag_add = 2049
motor_flag_add = 2050
dir_flag_add = 2051
stop_flag_add = 2052
count_add = 3784
scale = 80

class GuiPart:
    def __init__(self, master, queue, strt_func, stp_fnc, go_fnc, hm_fnc):
        self.queue = queue
        # Set up the GUI

        strt = Button(window, text="Start", command=strt_func)
        strt.grid(column=1, row=5)
        stp = Button(window, text="Stop", command=stp_fnc)
        stp.grid(column=2, row=5)
        go = Button(window, text="Go", command=go_fnc)
        go.grid(column=3, row=5)
        hm = Button(window, text="Home", command=hm_fnc)
        hm.grid(column=4, row=5)

    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        msg = 10
        self.queue.put(msg)

class ThreadedClient:
    state = 0
    count = 0
    success = 0
    motor_flag = 0
    dir_flag = 0
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master, plc_mb_add, dtc_mb_add, status_flag_add, run_flag_add,
                 motor_flag_add, dir_flag_add, stop_flag_add, count_add, scale):

        self.master = master
        self.queue = queue.Queue()
        self.plc_mb_add = plc_mb_add
        self.dtc_mb_add = dtc_mb_add
        self.status_flag_add = status_flag_add
        self.run_flag_add = run_flag_add
        self.motor_flag_add = motor_flag_add
        self.dir_flag_add = dir_flag_add
        self.stop_flag_add = stop_flag_add
        self.count_add = count_add
        self.scale = scale
        self.gui = GuiPart(master, self.queue, self.strt_func, self.stp_func,
                           self.go_func, self.hm_func)
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        self.periodicCall()

    def periodicCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        """
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            import sys
            sys.exit(1)
        self.master.after(200, self.periodicCall)

    def workerThread1(self):

        while self.running:

            if self.state == 1:
                dir = 1
                nx = int(nx_entry.get())
                ny = int(ny_entry.get())
                x_res = int(x_res_entry.get())
                y_res = int(y_res_entry.get())
                for y in range(0, int(ny)):
                    for x in range(0, int(nx)):
                        print('%d. take step in x %d' % (x, dir * x_res))

                    dir = -1 * dir

                    if y != int(ny) - 1:
                        print('%d. take step in y %d' % (y, y_res))
                state = 0
            if self.state == 2:
                print("homming")

            if self.state == 3:
                self.count = int(go_x_entry.get())

                if self.count < 0:
                    self.dir_flag = 0
                    self.count = -1 * self.count
                else:
                    self.dir_flag = 1

                self.motor_flag = 1

                while self.success != 1:
                    self.run_motor()

                self.success = 0
                self.count = int(go_y_entry.get())

                if self.count < 0:
                    self.dir_flag = 0
                    self.count = -1 * self.count
                else:
                    self.dir_flag = 1

                self.motor_flag = 0

                while self.success != 1:
                    self.run_motor()

                self.success = 0

    def strt_func(self):
        dir = 1
        nx = int(nx_entry.get())
        ny = int(ny_entry.get())
        x_res = int(x_res_entry.get())
        y_res = int(y_res_entry.get())
        for y in range(0, int(ny)):
            for x in range(0, int(nx)):

                self.motor_flag = 1
                self.count = x_res
                self.dir_flag = dir

                while self.success != 1:
                    self.run_motor()

                self.success = 0

            dir = -1 * dir

            if y != int(ny) - 1:
                self.motor_flag = 0
                self.count = y_res
                self.dir_flag = 1

                while self.success != 1:
                    self.run_motor()

                self.success = 0

    def stp_func(self):
        print('send stop bit')
        self.running = 0

    def hm_func(self):
        self.state = 2

    def go_func(self):
        self.state = 3

    def run_motor(self):
        result = client.read_coils(self.status_flag_add, 1, unit=self.plc_mb_add)
        if result.bits[0] != True:
            client.write_coil(self.motor_flag_add, self.motor_flag, unit=self.plc_mb_add)
            time.sleep(0.01)
            client.write_registers(self.count_add, self.count * self.scale, unit=self.plc_mb_add)
            time.sleep(0.01)
            client.write_coil(self.dir_flag_add, self.dir_flag, unit=self.plc_mb_add)
            time.sleep(0.01)
            client.write_coil(self.run_flag_add, 1, unit=self.plc_mb_add)
            self.success = 1
        else:
            self.success = 0

window = Tk()

window.title("Laser Scanner GUI")

window.geometry('550x200')

lblg = Label(window, text="Set Initial Position")
lblg.grid(column=0, row=0)

lblgx = Label(window, text="X(mm):")
lblgx.grid(column=0, row=1)
go_x_entry = Entry(window,width=10)
go_x_entry.grid(column=1, row=1)

lblgy = Label(window, text="Y(mm):")
lblgy.grid(column=2, row=1)
go_y_entry = Entry(window,width=10)
go_y_entry.grid(column=3, row=1)

lblstg = Label(window, text="Settings")
lblstg.grid(column=0, row=2)

lblx = Label(window, text="X Resolution (mm):")
lblx.grid(column=0, row=3)
x_res_entry = Entry(window,width=10)
x_res_entry.grid(column=1, row=3)


lblx1 = Label(window, text="# Data Point In X:")
lblx1.grid(column=2, row=3)
nx_entry = Entry(window,width=10)
nx_entry.grid(column=3, row=3)

lbly = Label(window, text="Y Resolution (mm):")
lbly.grid(column=0, row=4)
y_res_entry = Entry(window,width=10)
y_res_entry.grid(column=1, row=4)


lbly1 = Label(window, text="# Data Point In Y:")
lbly1.grid(column=2, row=4)
ny_entry = Entry(window,width=10)
ny_entry.grid(column=3, row=4)

th_client = ThreadedClient(window, plc_mb_add, dtc_mb_add, status_flag_add, run_flag_add,
                 motor_flag_add, dir_flag_add, stop_flag_add, count_add, scale)

client = ModbusSerialClient('ascii',port=mb_com,stopbits=1,bytesize=7,parity='E',baudrate=9600)
window.mainloop()