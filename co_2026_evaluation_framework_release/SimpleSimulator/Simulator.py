import sys

# Simulation State
# x0 is hardwired to 0, x2 is usually SP
registers=[0]*32
registers[2]=0x0000017C 
current_pc=0

# Memory blocks-simpler lists are easier to manage than dicts
data_section=[0]*32  # 0x10000 area
stack_section=[0]*32 # 0x00100 area

instructions=[]
history_log=[]

def sign_extend(value, bit_count):

    # Standard sign extension trick
    if value&(1<<(bit_count-1)):
        return value-(1<<bit_count)
    return value

def force_signed(val):

    val&=0xFFFFFFFF
    if val>=0x80000000:
        return val-0x100000000
    else:
        return val

def resolve_address(addr,label):

    addr&=0xFFFFFFFF

    # checks alignment-RISC-V wants 4-byte alignment for words
    if addr%4!=0:
        print(f"Alignment Error, {label} at 0x{addr:08X} (PC=0x{current_pc:08X})",file=sys.stderr)
        sys.exit(1)

    # Data memory range
    if 0x00010000<=addr<=0x0001007C:
        return data_section,(addr-0x10000)>>2
    
    # Stack range
    elif 0x00000100<=addr<=0x0000017C:
        return stack_section,(addr-0x100)>>2

    print(f"Memory Access Out of Bounds: {label} at 0x{addr:08X}",file=sys.stderr)
    sys.exit(1)
