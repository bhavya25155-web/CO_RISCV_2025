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

def b_type(raw_bits, rs1, rs2):

    global current_pc

    # branches have weird scattered immediate format
    imm = sign_extend(((raw_bits >> 31) << 12) | (((raw_bits >> 7) & 1) << 11) |
                       (((raw_bits >> 25) & 0x3f) << 5) | (((raw_bits >> 8) & 0xf) << 1), 13)
    val1, val2 = registers[rs1], registers[rs2]
    f3 = (raw_bits >> 12) & 0x7

    is_taken = False
    if f3 == 0: 
        is_taken = (val1 == val2)

    elif f3 == 1: 
        is_taken = (val1 != val2)

    elif f3 == 4: 
        is_taken = force_signed(val1) < force_signed(val2)

    elif f3 == 5: 
        is_taken = force_signed(val1) >= force_signed(val2)

    elif f3 == 6:
        is_taken = (val1 & 0xFFFFFFFF) < (val2 & 0xFFFFFFFF)

    elif f3 == 7:
        is_taken = (val1 & 0xFFFFFFFF) >= (val2 & 0xFFFFFFFF)
        
    current_pc = (current_pc + imm) & 0xFFFFFFFF if is_taken else current_pc + 4

def check_for_halt(raw_bits):

    # treating 'beq x0, x0, 0' as the end of the program
    return raw_bits == 0x00000063

def save_state():

    # saves current PC and all regs in binary for the trace file
    row = f"0b{current_pc & 0xFFFFFFFF:032b} "
    row += " ".join(f"0b{(registers[i] if i != 0 else 0):032b}" for i in range(32))
    history_log.append(row + " ")

def start_engine(output_file):

    global current_pc

    # limit to 10M cycles so we don't loop forever on bad code
    for _ in range(10_000_000):
        if current_pc%4!=0:
            print(f"Error: unaligned PC 0x{current_pc:08X}",file=sys.stderr)
            sys.exit(1)
        pc_idx=current_pc>>2
        if pc_idx>=len(instructions):
            print(f"PC out of bounds: 0x{current_pc:08X}",file=sys.stderr)
            sys.exit(1)

        cmd=instructions[pc_idx]

        if check_for_halt(cmd):
            save_state()
            # final memory dump
            for i in range(32):
                real_addr=0x00010000+(i*4)
                history_log.append(f"0x{real_addr:08X}:0b{data_section[i]:032b}")
            break

        # Decode basic fields
        opcode=cmd&0x7F
        rd_idx=(cmd>>7)&0x1F
        rs1_idx=(cmd>>15)&0x1F
        rs2_idx=(cmd>>20)&0x1F

        if opcode==0x33: 
            r_type(cmd,rd_idx,rs1_idx,rs2_idx)

        elif opcode in (0x03,0x13,0x67): 
            i_type(cmd,opcode,rd_idx,rs1_idx)

        elif opcode==0x23: # sw
            s_imm=sign_extend(((cmd>>25)<<5)|((cmd>>7)&0x1F),12)
            m_target,m_idx=resolve_address(registers[rs1_idx]+s_imm,"store")
            m_target[m_idx]=registers[rs2_idx]&0xFFFFFFFF
            current_pc+=4

        elif opcode==0x63: 
            b_type(cmd,rs1_idx,rs2_idx)

        elif opcode in (0x37,0x17): # lui/auipc
            u_imm=cmd&0xFFFFF000
            if rd_idx!=0:
                if opcode==0x37:
                    registers[rd_idx] =u_imm&0xFFFFFFFF
                else:
                    registers[rd_idx]=(current_pc+u_imm)&0xFFFFFFFF
            current_pc+=4

        elif opcode==0x6F: # jal
            j_imm=sign_extend(((cmd>>31)<<20)|(((cmd>>12)&0xff)<<12)|
                               (((cmd>>20)&1)<<11)|(((cmd>>21)&0x3ff)<<1),21)
            if rd_idx!=0: 
                registers[rd_idx]=(current_pc+4)&0xFFFFFFFF
            current_pc=(current_pc+j_imm)&0xFFFFFFFF

        registers[0]=0 # x0 hardwired to 0
        save_state()

    with open(output_file,'w') as f:
        f.write('\n'.join(history_log) + '\n')


with open(sys.argv[1],'r') as f:
    # Load binary strings as integers
    for line in f:
        if line.strip():
            instructions.append(int(line.strip(),2))
        
start_engine(sys.argv[2])
