import RPi.GPIO as GPIO
import os
import time

usleep = lambda x: time.sleep(x / 1000000.0)

GPIO.setwarnings(False)


class EEPROMProgrammer(object):

    DATA_BIT_LEN = 8 
    ADDR_BIT_LEN = 10 

    @property def address_pins(self):
        return {
            '0': 9,
            '1': 10,
            '2': 22,
            '3': 27,
            '4': 17,
            '5': 4,
            '6': 3,
            '7': 2,
            '8': 14,
            '9': 15,
            '10': 18
        }

    @property
    def data_pins(self):
        return {
            '0': 5,
            '1': 0,
            '2': 11,
            '3': 20,
            '4': 16,
            '5': 12,
            '6': 1,
            '7': 7
        }

    @property
    def data(self):
        # alias for `self.bits`
        return self.bits

    def __init__(self):
        self.we = 25
        self.oe = 21
        self.oe_enabled = self.we_enabled = False

        self.on_init()

    def on_init(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.we, GPIO.OUT)
        GPIO.setup(self.oe, GPIO.OUT)

        GPIO.output([self.we, self.oe], 1)

        self.bits = ['0'] * self.DATA_BIT_LEN
        self.address = ['0'] * self.ADDR_BIT_LEN

        GPIO.setup(list(self.address_pins.values()), GPIO.OUT, initial=0)
        GPIO.setup(list(self.data_pins.values()), GPIO.OUT, initial=0)

    def output_enable(self, enable=True):
        status = 1 if enable else 0
        GPIO.output(self.oe, status)

    def pulse_write(self):
        oe_state = self.oe_enabled

        self.update()
        usleep(150)
        
        GPIO.output(self.oe, 1)
        GPIO.output(self.we, 0)
        usleep(250)
        GPIO.output(self.we, 1)
        self.output_enable(oe_state)
    
    def set_address(self, addr):  # type: (list) -> None
        addr = self._tobinary(addr, size=10)
        addr = addr[::-1]  # bits need to go in reverse order when outputting to GPIO...
        for i, bit in enumerate(addr): 
            self.address[i] = bit
            GPIO.output(self.address_pins[str(i)], bit)

    def set_data(self, data):
        # alias function for `set_bits()`
        return self.set_bits(data)

    def set_bits(self, bits):  # type: (list) -> None
        if isinstance(bits, str):
            bits = list(map(int, bits))

        bits = bits[::-1]  # bits need to go in reverse order when outputting to GPIO...

        for i, bit in enumerate(bits):
            bit = 0 if not bit else 1
            self.bits[i] = bit
            GPIO.output(self.data_pins[str(i)], bit)

    def update(self):
        for i, bit in enumerate(self.bits):
            GPIO.output(self.data_pins[str(i)], bit)

        for i, addr in enumerate(self.address):
            GPIO.output(self.address_pins[str(i)], addr)

    def cleanup(self):
        GPIO.cleanup()
        self.on_init()

    def _tolist(self, s):
        if isinstance(s, str):
            return list(map(int, s))
        return s

    def _tobinary(self, x, size=10):  # type: (int) -> list
        if size == 10:
            return self._tolist('{0:010b}'.format(x))
        else:
            return self._tolist('{0:08b}'.format(x))
    
    def read(self, address):
        address = self._tolist(address)


def set_addr(prog):
    try:
        addr = int(input("Enter base-10 address (0-1023): "))
        if not 0 <= addr <= 1023:
            raise Exception("Invalid address: {}".format(addr))
            
    except Exception as e:
        print(e)
        
    prog.set_address(addr)
    

def set_data(prog):
    bits = str(input("Enter 8-bit word: "))
    prog.set_bits(bits)


def set_all(prog):
    data = str(input("Enter 8-bit word: "))
    for i in range(0, 1024):
        prog.set_address(i)
        prog.set_bits(data)
        prog.update()
        prog.pulse_write()


def main():

    os.system('clear')

    prog = EEPROMProgrammer()
    we = oe = False
    done = False
    while not done:
        print("Main Menu:")
        print("\tp) Program EEPROM")
        print("\t1) Set Bits")
        print("\t2) Set Address")
        print("\t3) Pulse WE")
        print("\t4) Print Current Bits")
        print("\t5) Print Current Address")
        print("\to) Print Output")
        print("\ts) Set All")
        print("\te) Exit")
        
        x = str(input("\nEnter command: "))
        print("")

        if x == '1':
            set_data(prog)
        elif x == '2':
            set_addr(prog)
        elif x == '3':
            prog.pulse_write()
        elif x == '4':
            print("Bits: {}".format("".join(map(str, prog.bits))))
        elif x == '5':
            print("Address: {}".format("".join(map(str, prog.address))))
        elif x == 'o':
            prog.output_enable(True)
            data = []
            for pos in list('01234567'):
                bit = GPIO.input(prog.data_pins[pos])
                data.append(bit)

            addr = "".join(map(str, prog.address))
            data = "".join(map(str, data))
            print("Data at address {}: {}\n".format(addr, data))
            
        elif x == 'p':
            set_data(prog)
            set_addr(prog)
            prog.update()
            prog.pulse_write()
        elif x == 's':
            set_all(prog)
        elif x == 'e':
            done = True
        else:
            print("Error: Invalid menu choice '%s'\n" % x)


if __name__ == '__main__':
    main()
