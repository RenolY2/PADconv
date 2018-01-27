import struct
import math

from pad import write_command

def read_ulonglong_le(f):
    return struct.unpack("Q", f.read(8))[0]

def read_uint32_le(f):
     return struct.unpack("I", f.read(4))[0]

def read_ubyte_le(f):
     return struct.unpack("B", f.read(1))[0]
     

with open("newshadowtest.dtm", "rb") as f:
    f.seek(0xA)
    is_wiigame = read_ubyte_le(f)
    
    if is_wiigame:
        raise RuntimeError("Wii games are not supported (and Mario Sunshine is not a Wii game anyway)")
        
    f.seek(0x15)
    inputcount = read_ulonglong_le(f)
    
    print(inputcount)
    
    
    f.seek(0x9C)
    is_pal60 = read_ubyte_le(f)
    
    f.seek(0xED)
    tickcount = read_ulonglong_le(f)
    
    print("Is pal60:", is_pal60)
    print("tick count", tickcount)
    
    f.seek(0x100)
    
    analogstick_magnitude = []
    analogstick_direction = []
    buttons = []
    Lpressure = []
    Rpressure = []
    
    for i in range(inputcount):
        controllerdata = f.read(6)
        cstick_data = f.read(2) # We do not need this
        
        buttons1, buttons2, l_pressure, r_pressure, analog_x, analog_y = struct.unpack("B"*6, controllerdata)
        
        buttons.append((buttons1<<4) | buttons2) 
        
        """if buttons1 & (1 << 0): active_buttons.append("START")
        if buttons1 & (1 << 1): active_buttons.append("A")
        if buttons1 & (1 << 2): active_buttons.append("B")
        if buttons1 & (1 << 3): active_buttons.append("X")
        if buttons1 & (1 << 4): active_buttons.append("Y")
        if buttons1 & (1 << 5): active_buttons.append("Z")
        if buttons1 & (1 << 6): active_buttons.append("UP")
        if buttons1 & (1 << 7): active_buttons.append("DOWN")
        
        if buttons2 & (1 << 0): active_buttons.append("LEFT")
        if buttons2 & (1 << 1): active_buttons.append("RIGHT")
        if buttons2 & (1 << 2): active_buttons.append("L")
        if buttons2 & (1 << 3): active_buttons.append("R")"""
        
        dx = analog_x - 128 
        dy = analog_y - 128
        
        magnitude = ((dx**2 + dy**2)**0.5)/128.0
        if magnitude > 1: magnitude = 1 
        
        analogstick_magnitude.append(magnitude*32.0)
        
        angle = math.atan2(dx, dy) * (180/math.pi)
        analogstick_direction.append(angle)
        
        Lpressure.append(l_pressure)
        Rpressure.append(r_pressure)
    
    with open("newshadowtest.dtm.txt", "w") as g:
        for valueslist, valuetype in (
            (analogstick_magnitude, "analog_magnitude"),
            (analogstick_direction, "analog_direction"),
            (buttons, "buttons_pressed"),
            (Lpressure, "trigger_1_held"),
            (Rpressure, "trigger_2_held")
          ):
            print(valuetype)
            framecount = 0
            last = None 
            
            for val in valueslist:
                if last is None or last == val:
                    framecount += 1
                    last = val 
                else:
                    last = val
                    
                    if valuetype == "buttons_pressed":
                        
                        button1 = val >> 4
                        button2 = val & 0b1111
                        print(val, button1, button2)
                        
                        active_buttons = []
                        if button1 & (1 << 0) != 0: active_buttons.append("START")
                        if button1 & (1 << 1) != 0: active_buttons.append("A")
                        if button1 & (1 << 2) != 0: active_buttons.append("B")
                        if button1 & (1 << 3) != 0: active_buttons.append("X")
                        if button1 & (1 << 4) != 0: active_buttons.append("Y")
                        if button1 & (1 << 5) != 0: active_buttons.append("Z")
                        if button1 & (1 << 6) != 0: active_buttons.append("UP")
                        if button1 & (1 << 7) != 0: active_buttons.append("DOWN")
                        
                        if button2 & (1 << 0) != 0: active_buttons.append("LEFT")
                        if button2 & (1 << 1) != 0: active_buttons.append("RIGHT")
                        if button2 & (1 << 2) != 0: active_buttons.append("L")
                        if button2 & (1 << 3) != 0: active_buttons.append("R")
                        
                        print(button1 & (1<<1))
                        write_command(g, valuetype, framecount, [" | ".join(active_buttons)])
                    else:
                        write_command(g, valuetype, framecount, [val])
                        
                    framecount = 1
                    
            if framecount > 0:
                if valuetype == "buttons_pressed":
                    button1 = val >> 4
                    button2 = val & 0b1111
                    
                    active_buttons = []
                    if buttons1 & (1 << 0): active_buttons.append("START")
                    if buttons1 & (1 << 1): active_buttons.append("A")
                    if buttons1 & (1 << 2): active_buttons.append("B")
                    if buttons1 & (1 << 3): active_buttons.append("X")
                    if buttons1 & (1 << 4): active_buttons.append("Y")
                    if buttons1 & (1 << 5): active_buttons.append("Z")
                    if buttons1 & (1 << 6): active_buttons.append("UP")
                    if buttons1 & (1 << 7): active_buttons.append("DOWN")
                    
                    if buttons2 & (1 << 0): active_buttons.append("LEFT")
                    if buttons2 & (1 << 1): active_buttons.append("RIGHT")
                    if buttons2 & (1 << 2): active_buttons.append("L")
                    if buttons2 & (1 << 3): active_buttons.append("R")
                    
                
                    write_command(g, valuetype, framecount, [" | ".join(active_buttons)])
                else:
                    write_command(g, valuetype, framecount, [val])
                

        
        
        