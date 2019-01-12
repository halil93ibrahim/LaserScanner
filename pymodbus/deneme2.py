from pymodbus.client.sync import ModbusSerialClient
#from pymodbus.client import sync

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


client = ModbusSerialClient('ascii',port='COM11',stopbits=1,bytesize=7,parity='E',baudrate=9600)
client.write_coils(2048, num2bits(15), unit=0x01)
#client.write_register(404098,0,unit=0x01)
# client.write_coil(2048, 1, unit=0x01)
result = client.read_coils(404097,16,unit=0x01)
print(result.bits)
#reg = client.read_register(404098,unit=0x01)
#print(reg)
client.close()
