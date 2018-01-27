import struct 
import argparse 

FRAMESPERSECOND = 30

angle_offset = 180

BUTTONS = [
    (0x0001, "LEFT"), (0x0002, "RIGHT"), (0x0004, "DOWN"), (0x0008, "UP"),
    (0x0010, "Z"), (0x0020, "R"), (0x0040, "L"),
    (0x0100, "A"), (0x0200, "B"), (0x0400, "X"), (0x0800, "Y"),
    (0x1000, "START")
    ]
    
def read_uint32(f):
    return struct.unpack(">I", f.read(4))[0]

def read_float(f):
    return struct.unpack(">f", f.read(4))[0]

def read_short(f):
    return struct.unpack(">h", f.read(2))[0]
    
def read_ushort(f):
    return struct.unpack(">H", f.read(2))[0]

def read_ubyte(f):
    return struct.unpack(">b", f.read(1))[0]
    
def read_frameinfo(f, end):
    values = []
    while f.tell() < end:
        next = read_uint32(f)
        values.append(next)
        
    
    return values 


    
def pad_to_multiples_of_4(f):
    if f.tell() % 4 != 0:
        padcount = 4 - (f.tell() % 4)
        f.write(b"\x00"*padcount)
    
def write_command(f, commandname, framecount, args):
    f.write("{0}({1}, {2})\n".format(commandname, framecount, ", ".join(str(x) for x in args)))
    
def write_comment(f, comment):
    f.write("# ")
    f.write(comment)
    f.write("\n")


def count_frames(section):
    count = 0 
    for framecount, val in section:
        count += framecount 
        
    return count 

            

def get_buttons(buttonflags):
    buttons_active = []
    for val, button in BUTTONS:
        if buttonflags & val != 0:
            buttons_active.append(button)
            buttonflags &= ~val 
    
    if buttonflags != 0:
        print("Buttons unaccounted for!", buttonflags)
    return buttons_active

def buttons_to_value(buttons):
    buttonvalue = 0 
    for val, button in BUTTONS:
        if button in buttons:
            buttonvalue |= val 
            
    return buttonvalue
    
    
def pad_to_text(input, output):
    with input as f:
        record_string = f.read(0x10)
        framelength = read_uint32(f)
        analog_magnitude_frameinfo, analog_magnitude_values = read_uint32(f), read_uint32(f)
        analog_dir_frameinfo, analog_dir_values = read_uint32(f), read_uint32(f)
        buttoninput_frameinfo, buttoninput_values = read_uint32(f), read_uint32(f)
        trigger_1_frameinfo, trigger_1_values = read_uint32(f), read_uint32(f)
        trigger_2_frameinfo, trigger_2_values = read_uint32(f), read_uint32(f)
        
        f.read(4) # padding 
        
        index = 0
        
        
        
        with output as g:
            print(hex(analog_magnitude_frameinfo))
            # Analog stick magnitude
            f.seek(analog_magnitude_frameinfo)
            
            frameinfo = read_frameinfo(f, end=analog_magnitude_values) 
            
            f.seek(analog_magnitude_values)
            write_comment(g, "Analog Magnitude: ([How long in frames], [How far the stick is pushed from 0 to 32])")
            
            count = 0
            for framecount in frameinfo:
                value = read_float(f)
                
                write_command(g, "analog_magnitude", framecount, [value])
                count += framecount
            write_comment(g, "Actions for {} frames".format(count))
            
            g.write("\n")
            
            # Analog stick direction
            f.seek(analog_dir_frameinfo)
            frameinfo = read_frameinfo(f, end=analog_dir_values)
            
            f.seek(analog_dir_values)
            write_comment(g, "Analog Direction: ([How long in frames], [Stick Direction from -180 to 180)")
            count = 0
            for framecount in frameinfo:
                value = (read_short(f)/float(0x8000)) * 180
                write_command(g, "analog_direction", framecount, [value])
                count += framecount
            write_comment(g, "Actions for {} frames".format(count))
            
            g.write("\n")
            
            # Buttons 
            f.seek(buttoninput_frameinfo)
            frameinfo = read_frameinfo(f, end=buttoninput_values)
            
            f.seek(buttoninput_values)
            write_comment(g, "Buttons pressed: ([How long in frames], [Which buttons pressed])")
            count = 0 
            for framecount in frameinfo:
                value = read_ushort(f)
                buttons = get_buttons(value)
                
                write_command(g, "buttons_pressed", framecount, ["|".join(buttons)])
                count += framecount
            write_comment(g, "Actions for {} frames".format(count))
            
            g.write("\n")
            
            # First Trigger 
            f.seek(trigger_1_frameinfo)
            frameinfo = read_frameinfo(f, end=trigger_1_values)
            
            f.seek(trigger_1_values)
            write_comment(g, "Trigger 1 held: ([How long in frames], [How far it is pushed from 0 to 255])")
            count = 0 
            for framecount in frameinfo:
                value = read_ubyte(f)
                
                write_command(g, "trigger_1_held", framecount, [value])
                count += framecount
            write_comment(g, "Actions for {} frames".format(count))
            
            g.write("\n")
            
            # Second trigger
            f.seek(trigger_2_frameinfo)
            frameinfo = read_frameinfo(f, end=trigger_2_values)
            
            f.seek(trigger_2_values)
            write_comment(g, "Trigger 2 held: ([How long in frames], [How far it is pushed from 0 to 255])")
            count = 0 
            for framecount in frameinfo:
                value = read_ubyte(f)
                
                write_command(g, "trigger_2_held", framecount, [value])
                count += framecount
            write_comment(g, "Actions for {} frames".format(count))

def text_to_pad(input, output):
    analog_magnitude = []
    analog_dir = []
    button_input = []
    trigger1 = []
    trigger2 = []
    
    for i, line in enumerate(input):
        try:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue 
            
            bracket = line.find("(")
            if bracket == -1:
                raise RuntimeError("Malformed line, missing opening bracket")
            if not line.endswith(")"):
                raise RuntimeError("Malformed line, missing closing bracket")
            
            
            command = line[:bracket]
            args = [x.strip() for x in line[bracket+1:-1].split(",")]
            
            if len(args) != 2:
                raise RuntimeError("Wrong amount of arguments (has {}, needs to be 2)".format(len(args)))
            
            framecount = args[0]
            if framecount.endswith("s"):
                framecount = int(framecount[:-1])*FRAMESPERSECOND
            else:
                framecount = int(framecount)
            
            if command == "analog_magnitude":
                analog_magnitude.append((framecount, float(args[1])))
            elif command == "analog_direction":
                angle_degrees = float(args[1]) + angle_offset 
                
                if angle_degrees > 180:
                    overflow = angle_degrees - 180 
                    angle_degrees = -180 + overflow 
                elif angle_degrees < -180:
                    overflow = angle_degrees + 180
                    angle_degrees = 180+overflow
                
                angle = int((angle_degrees/180.0)*32768)
                if angle > 0x7FFF: 
                    print("angle exceeds limit", hex(angle))
                    angle = 0x7FFF 
                if angle < -0x8000: 
                    angle = -0x8000
                    print("angle exceeds limit", hex(angle))
                analog_dir.append((framecount, angle))
            elif command == "buttons_pressed":
                buttons = [x.strip().upper() for x in args[1].split("|")]
                
                button_input.append((framecount, buttons_to_value(buttons)))
            elif command == "trigger_1_held":
                trigger1.append((framecount, int(args[1])))
            elif command == "trigger_2_held":
                trigger2.append((framecount, int(args[1])))
        except Exception as error:
            print("Exception raised on line {} in input file!".format(i+1))
            raise 
        
    print("finished parsing input")
    
    frame1 = count_frames(analog_magnitude)
    frame2 = count_frames(analog_dir)
    frame3 = count_frames(button_input)
    frame4 = count_frames(trigger1)
    frame5 = count_frames(trigger2)
    
    if ( 
      (frame1 != frame2) or (frame1 != frame3) or 
      (frame1 != frame4) or (frame1 != frame5)):
        
        raise RuntimeError(
            ("Frame count doesn't match: \n"
            "Analog magnitude: {}\n"
            "Analog direction: {}\n"
            "Button input: {}\n"
            "Trigger 1: {}\n"
            "Trigger 2: {}").format(frame1, frame2, frame3, frame4, frame5)
            )
    
    max_frame = frame1  # because all frame counts are the same we can pick any as the max 
    
    output.write(b"MARIO RECORDv0.2")
    output.write(struct.pack(">I", max_frame))
    output.write(b"This is placeholder for the section offsets!")
    
    # Write analog magnitude 
    magnitude_frameinfo_start = output.tell()
    
    for framecount, value in analog_magnitude:
        output.write(struct.pack(">I", framecount))
        
    magnitude_values_start = output.tell()
    for framecount, value in analog_magnitude:
        output.write(struct.pack(">f", value))
    
    # Write analog direction 
    direction_frameinfo_start = output.tell()
    for framecount, value in analog_dir:
        output.write(struct.pack(">I", framecount))
        
    direction_values_start = output.tell()
    for framecount, value in analog_dir:
        output.write(struct.pack(">h", value))
    
    pad_to_multiples_of_4(output)
    
    
    # Write button input 
    buttons_frameinfo_start = output.tell()
    for framecount, value in button_input:
        output.write(struct.pack(">I", framecount))
        
    buttons_values_start = output.tell()
    for framecount, value in button_input:
        output.write(struct.pack(">H", value))
    
    pad_to_multiples_of_4(output)
        
    # Write trigger 1 input 
    trigger1_frameinfo_start = output.tell()
    for framecount, value in trigger1:
        output.write(struct.pack(">I", framecount))
        
    trigger1_values_start = output.tell()
    for framecount, value in trigger1:
        output.write(struct.pack(">B", value))
    
    pad_to_multiples_of_4(output)
    
    
    # Write trigger 2 input
    trigger2_frameinfo_start = output.tell()
    for framecount, value in trigger2:
        output.write(struct.pack(">I", framecount))
        
    trigger2_values_start = output.tell()
    for framecount, value in trigger2:
        output.write(struct.pack(">B", value))
    
    pad_to_multiples_of_4(output)
    
    output.seek(0x14)
    output.write(struct.pack(">II", magnitude_frameinfo_start, magnitude_values_start))
    output.write(struct.pack(">II", direction_frameinfo_start, direction_values_start))
    output.write(struct.pack(">II", buttons_frameinfo_start, buttons_values_start))
    output.write(struct.pack(">II", trigger1_frameinfo_start, trigger1_values_start))
    output.write(struct.pack(">II", trigger2_frameinfo_start, trigger2_values_start))
    
    output.write(b"\x00"*4)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="Filepath to pad file. If --txt2pad is set, file path to text file.")
    parser.add_argument("--txt2pad", action="store_true",
                        help="Set this option to convert the text file to pad.")
    parser.add_argument("output", default=None, nargs = '?',
                        help="Output path of the created text file. If --txt2pad is set, output path of the pad file.")
    
    args = parser.parse_args()
    
    input = args.input 
    
    if args.txt2pad and args.output is None:
        output = args.input+".pad"
    elif args.output is None:
        output = args.input+".txt"
    else:
        output = args.output
    
    if args.txt2pad:
        with open(input, "r") as f:
            with open(output, "wb") as g:
                text_to_pad(f, g)
    else:
        with open(input, "rb") as f:
            with open(output, "w") as g:
                pad_to_text(f, g)
            
        
        
        