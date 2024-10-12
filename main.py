print("Hello world")
import time
time.sleep(10)

from machine import Pin, WIZNET_PIO_SPI, SoftSPI
import network
import time
from ST7735 import TFT
from sysfont import sysfont

# Setup W5500 Network
def w5x00_init():
    spi = WIZNET_PIO_SPI(baudrate=31_250_000, mosi=Pin(23),miso=Pin(22),sck=Pin(21)) #W55RP20 PIO_SPI
    print("Setup WIZNET5K")
    nic = network.WIZNET5K(spi,Pin(20),Pin(25)) #spi,cs,reset pin
    nic.active(True)
    print("Setup ifconfig")
    #nic.ifconfig('dhcp')       
    nic.ifconfig(('192.168.77.99','255.255.255.0','192.168.77.1','8.8.8.8'))
    while not nic.isconnected():
        time.sleep(1)
        print(nic.regs())
    print('IP address:', nic.ifconfig())

print("Setup W5500")
w5x00_init()

# Setup LCD Driver
from ST7735 import TFT
from sysfont import sysfont
from machine import SoftSPI,Pin
import time

# - 1=GND : GP2
# - 2=VCC : GP3
# - 3=SCK : GP4
# - 4=SDA : GP5
# - 5=RES : GP6
# - 6=RS  : GP7
# - 7=CS  : GP8
# - 8=LEDA: GP9
Pin(2, Pin.OUT).off()
Pin(3, Pin.OUT).on()
Pin(9, Pin.OUT).on()
tft_spi = SoftSPI(baudrate=100_000_000, sck=Pin(4), mosi=Pin(5), miso=Pin(10))
tft=TFT(tft_spi, aDC=7, aReset=6, aCS=8)
tft.initr()
tft.rotation(2)
tft.rgb(True)

def LCD_Update(Alarm, Running, Motor, Red, Green):
    tft.fill(TFT.BLACK)
    tft.text((0, 0),
             "Running" if Running else "Stopped",
             TFT.GREEN if Running else TFT.RED,
             sysfont, 3, nowrap=True)
    
    tft.text((0, 160-sysfont["Height"]*3),
             "Alarm" if Alarm else "Normal",
             TFT.YELLOW, sysfont, 3, nowrap=True)
    
    if Red:
        tft.fillcircle((128/2+30, 60), 20, TFT.RED)
    else:
        tft.circle((128/2+30, 60), 20, TFT.RED)
      
    if Green:
        tft.fillcircle((128/2-30, 60), 20, TFT.GREEN)
    else:
        tft.circle((128/2-30, 60), 20, TFT.GREEN)
        
    if Motor:
        tft.fillrect((128/2-100/2, 90), (100, 20), TFT.CYAN)
    else:
        tft.rect((128/2-100/2, 90), (100, 20), TFT.CYAN)

tft.fill(TFT.BLACK)
tft.text((0, 0), "Welcome", TFT.WHITE, sysfont, 3, nowrap=True)

# Setup modbus master
from umodbus.tcp import TCP as ModbusTCPMaster

print("Starting Modbus Master")
tcp_device = ModbusTCPMaster(
    slave_ip='192.168.77.55',
    slave_port=502,
    timeout=10
)

previous_status = []
while True:
    time.sleep(1)
    coil_status = tcp_device.read_coils(
        slave_addr=1,
        starting_addr=0,
        coil_qty=8)
    #print('Status of coil', coil_status)
    
    input_status = tcp_device.read_discrete_inputs(
        slave_addr=1,
        starting_addr=0,
        input_qty=8)
    #print('Status of inputs', input_status)
    
    current_status = [input_status[-2-1],
                      coil_status[-5-1],
                      coil_status[-2-1],
                      coil_status[-1-1],
                      coil_status[-0-1],]
    alarm_status, running_status, motor_status, green_led, red_led = current_status
    print(f"ALARM: {alarm_status*1} | RUNNING: {running_status*1} | MOTOR: {motor_status*1} | RED LED: {red_led*1} | GREEN LED: {green_led*1}")
    
    if current_status != previous_status:
        print("[Update]")
        LCD_Update(alarm_status, running_status, motor_status, red_led, green_led)

    previous_status = current_status

