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

def r_type(raw_bits,rd,rs1 ,rs2):
    global current_pc
    val1,val2=registers[rs1],registers[rs2]
    f3=(raw_bits>>12)&0x7
    f7=(raw_bits>>25)&0x7F
    out=0

    if f3==0:
        # Add or Sub depends on f7
        out=val1+val2 if f7==0x00 else val1-val2
    elif f3==0x1: 
        out=val1<<(val2&0x1F) # SLL
    elif f3==0x2:
        if (force_signed(val1)<force_signed(val2)): # SLT
            out =1
        else:
            out=0
    elif f3==0x3:
        if ((val1&0xFFFFFFFF)<(val2&0xFFFFFFFF)): #SLTU
            out=1
        else:
            out=0
    elif f3==0x4: 
        out=val1^val2
    elif f3==0x5:
        # Logic vs Arithmetic shift
        if f7==0x00:
            out=(val1&0xFFFFFFFF)>>(val2&0x1F)
        else:
            out=force_signed(val1)>>(val2&0x1F)
    elif f3==0x6: 
        out=val1|val2
    elif f3==0x7: 
        out=val1&val2

    if rd!=0: 
        registers[rd]= out&0xFFFFFFFF
        
    current_pc+=4

def i_type(raw_bits,op,rd,rs1):
    global current_pc
    # Extract 12-bit immediate
    imm=sign_extend((raw_bits>>20)&0xFFF,12)
    src_val=registers[rs1]
    f3=(raw_bits>>12)&0x7

    if op==0x03: # lw
        mem_list,offset=resolve_address(src_val+imm,"load")
        if rd!=0: 
            registers[rd]=mem_list[offset]

    elif op==0x13: # addi / sltiu
        if f3==0x0:
            res=src_val+imm
        elif f3==0x3:
            if ((src_val&0xFFFFFFFF)<(imm&0xFFFFFFFF)):
                res=1
            else:
                res=0
        else:
            # if we get here, something is wrong with the input file
            print(f"Unhandled f3 {f3} for addi-type",file=sys.stderr)
            sys.exit(1)
        if rd!=0: 
            registers[rd]=res&0xFFFFFFFF

    elif op==0x67: # jalr
        jump_target=(src_val+imm)&~1
        if rd!=0: 
            registers[rd]=(current_pc+4)&0xFFFFFFFF
        current_pc=jump_target
        return 
    current_pc+=4



