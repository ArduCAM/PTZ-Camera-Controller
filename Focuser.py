import sys
import time
import os



class Focuser:
    bus = None
    CHIP_I2C_ADDR = 0x0C
    BUSY_REG_ADDR = 0x04
    def __init__(self, bus):
        try:
            import smbus
            self.bus = smbus.SMBus(bus)
        except:
            sys.exit(0)
        
    def read(self,chip_addr,reg_addr):
        value = self.bus.read_word_data(chip_addr,reg_addr)
        value = ((value & 0x00FF)<< 8) | ((value & 0xFF00) >> 8)
        return value
# return self.focus_value

    def write(self,chip_addr,reg_addr,value):
        if value < 0:
            value = 0
        value = ((value & 0x00FF)<< 8) | ((value & 0xFF00) >> 8)
        return self.bus.write_word_data(chip_addr,reg_addr,value)

    OPT_BASE    = 0x1000
    OPT_FOCUS   = OPT_BASE | 0x01
    OPT_ZOOM    = OPT_BASE | 0x02
    OPT_MOTOR_X = OPT_BASE | 0x03
    OPT_MOTOR_Y = OPT_BASE | 0x04
    OPT_IRCUT   = OPT_BASE | 0x05
    opts = {
        # OPT_FOCUS : {
        OPT_ZOOM  : {
            "REG_ADDR" : 0x01,
            "MIN_VALUE": 0,
            "MAX_VALUE": 20000,
            "DEF_VALUE": 0,
            "RESET_ADDR": 0x01 + 0x0A,
        },
        # OPT_ZOOM  : {
        OPT_FOCUS : {    
            "REG_ADDR" : 0x00,
            "MIN_VALUE" : 0,
            "MAX_VALUE": 20000,
            "DEF_VALUE": 0,
            "RESET_ADDR": 0x00 + 0x0A,
        },
        OPT_MOTOR_X : {
            "REG_ADDR" : 0x05,
            "MIN_VALUE" : 0,
            "MAX_VALUE": 180,
            "RESET_ADDR": None,
        },
        OPT_MOTOR_Y : {
            "REG_ADDR" : 0x06,
            "MIN_VALUE" : 0,
            "MAX_VALUE": 180,
            "RESET_ADDR": None,
        },
        OPT_IRCUT : {
            "REG_ADDR" : 0x0C, 
            "MIN_VALUE" : 0,
            "MAX_VALUE": 0x01,   
            "RESET_ADDR": None,
        }
    }

    def isBusy(self):
        return self.read(self.CHIP_I2C_ADDR,self.BUSY_REG_ADDR) != 0

    def waitingForFree(self):
        count = 0
        begin = time.time()
        while self.isBusy() and count < (5 / 0.01):
            count += 1
            time.sleep(0.01)

    def reset(self,opt,flag = 1):
        self.waitingForFree()
        info = self.opts[opt]
        if info == None or info["RESET_ADDR"] == None:
            return
        self.write(self.CHIP_I2C_ADDR,info["RESET_ADDR"],0x0000)
        if flag & 0x01 != 0:
            self.waitingForFree()
        self.set(opt, info["MIN_VALUE"])

    def get(self,opt,flag = 0):
        self.waitingForFree()
        info = self.opts[opt]
        return self.read(self.CHIP_I2C_ADDR,info["REG_ADDR"])

    def set(self,opt,value,flag = 1):
        self.waitingForFree()
        info = self.opts[opt]
        if value > info["MAX_VALUE"]:
            value = info["MAX_VALUE"]
        if value < info["MIN_VALUE"]:
            value = info["MIN_VALUE"]
        self.write(self.CHIP_I2C_ADDR,info["REG_ADDR"],value)
        if flag & 0x01 != 0:
            self.waitingForFree()

pass 

def test():
    focuser = Focuser(7)
    focuser.set(Focuser.OPT_FOCUS, 0)
    time.sleep(3)
    focuser.set(Focuser.OPT_FOCUS, 0)
    time.sleep(3)
    focuser.reset(Focuser.OPT_FOCUS)

if __name__ == "__main__":
    test()