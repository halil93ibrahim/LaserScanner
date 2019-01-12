import threading
import time
from tkinter import *
from pymodbus.client.sync import ModbusSerialClient

def num2bits(num):
    b = bin(num)[2:]
    b = (16 - len(b)) * '0' + b
    bin_list = []
    for i in range(16):
        if b[15-i] == '1':
            bin_list.append(True)
        else:
            bin_list.append(False)
    return bin_list

window = Tk()

window.title("Laser Scanner GUI")

window.geometry('450x200')

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


client = ModbusSerialClient('ascii',port='COM11',stopbits=1,bytesize=7,parity='E',baudrate=9600)

slave_add = 0x01
status_flag_add = 2048
run_flag_add = 2049
motor_flag_add = 2050
dir_flag_add = 2051
count_add = 3584
scale = 80

def strt_func():
    dir = 1
    nx = int(nx_entry.get())
    ny = int(ny_entry.get())
    x_res = int(x_res_entry.get())
    y_res = int(y_res_entry.get())
    for y in range(0, int(ny)):
        for x in range(0, int(nx)):
            print('%d. take step in x %d' % (x, dir*x_res))

        dir = -1*dir

        if y != int(ny)-1:
            print('%d. take step in y %d' % (y, y_res))

def stp_func():
    print("stop")

def hm_func():
    print("homming")

def go_func():
    gx = int(go_x_entry.get())
    gy = int(go_y_entry.get())

    if gx < 0:
        dir_flag = 0
        gx = -1*gx
    else:
        dir_flag = 1

    motor_flag = 1

    while 1:
        result = client.read_coils(status_flag_add, 1, unit=slave_add)
        if result.bits[0] != True:
            print('going in x')
            client.write_coil(motor_flag_add, motor_flag, unit=slave_add)
            time.sleep(0.01)
            client.write_registers(count_add, gx*scale, unit=slave_add)
            time.sleep(0.01)
            client.write_coil(dir_flag_add, dir_flag, unit=slave_add)
            time.sleep(0.01)
            client.write_coil(run_flag_add, 1, unit=slave_add)
            break
        else:
            print('motor is busy')
            time.sleep(0.01)

    if gy < 0:
        dir_flag = 0
        gy = -1 * gy
    else:
        dir_flag = 1

    motor_flag = 0

    while 1:
        result = client.read_coils(status_flag_add, 1, unit=slave_add)
        if result.bits[0] != True:
            print('going in y')
            client.write_coil(motor_flag_add, motor_flag, unit=slave_add)
            time.sleep(0.01)
            client.write_registers(count_add, gy*scale, unit=slave_add)
            time.sleep(0.01)
            client.write_coil(dir_flag_add, dir_flag, unit=slave_add)
            time.sleep(0.01)
            client.write_coil(run_flag_add, 1, unit=slave_add)
            break
        else:
            print('motor is busy')
            time.sleep(0.01)

    print(gx, gy)

# strt = Button(window, text="Start", command=strt_func)
# strt.grid(column=1, row=5)
#
# stp = Button(window, text="Stop", command=stp_func)
# stp.grid(column=2, row=5)

go = Button(window, text="Go", command=go_func)
go.grid(column=4, row=1)

hm = Button(window, text="Home", command=hm_func)
hm.grid(column=5, row=1)

class ButtonHandler(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.event = event
    def run (self):

        dir = 1
        nx = int(nx_entry.get())
        ny = int(ny_entry.get())
        x_res = int(x_res_entry.get())
        y_res = int(y_res_entry.get())
        for y in range(0, int(ny)):
            for x in range(0, int(nx)):

                if self.event.is_set():
                    print("Stopped")
                    return

                print('%d. take step in x %d' % (x, dir * x_res))

            dir = -1 * dir

            if y != int(ny) - 1:
                print('%d. take step in y %d' % (y, y_res))



myEvent = threading.Event()

#The start button
strt = Button(window,text="Start",command=lambda: ButtonHandler(myEvent).start())
strt.grid(column=1, row=5)

#Say this is the exit button
stp = Button(window, text="Stop",command=lambda: myEvent.set())
stp.grid(column=2, row=5)

window.mainloop()