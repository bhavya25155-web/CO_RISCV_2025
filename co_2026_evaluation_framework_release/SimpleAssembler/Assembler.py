import sys
#R-type funct7 | rs2 | rs1 | funct3 | rd | opcode
    
R_type_table = {
    "add":{
        "funct7": "0000000",
        "funct3": "000",
        "opcode": "0110011"},
    "sub":{
        "funct7": "0100000",
        "funct3": "000",
        "opcode": "0110011"},
    "sll":{
        "funct7": "0000000",
        "funct3": "001",
        "opcode": "0110011"},
    "slt":{
        "funct7": "0000000",
        "funct3": "010",
        "opcode": "0110011"},
    "sltu":{
        "funct7": "0000000",
        "funct3": "011",
        "opcode": "0110011"},
    "xor":{
        "funct7": "0000000",
        "funct3": "100",
        "opcode": "0110011"},
    "srl":{
        "funct7": "0000000",
        "funct3": "101",
        "opcode": "0110011"},
    "or":{
        "funct7": "0000000",
        "funct3": "110",
        "opcode": "0110011"},
    "and":{
        "funct7": "0000000",
        "funct3": "111",
        "opcode": "0110011"}}

# I-type imm[11:0] | rs1 | funct3 | rd | opcode

I_type_table = {
    "addi":{
        "funct3": "000",
        "opcode": "0010011"},
    "sltiu":{
        "funct3": "011",
        "opcode": "0010011"},
    "lw":{
        "funct3": "010",
        "opcode": "0000011"},
    "jalr":{
        "funct3": "000",
        "opcode": "1100111"}}

# S-type imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode

S_type_table = {
    "sw":{
        "funct3": "010",
        "opcode": "0100011"}}

# B-type imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode

B_type_table = {
    "beq":{
        "funct3": "000",
        "opcode": "1100011"},
    "bne":{
        "funct3": "001",
        "opcode": "1100011"},
    "blt":{
        "funct3": "100",
        "opcode": "1100011"},
    "bge":{
        "funct3": "101",
        "opcode": "1100011"},
    "bltu":{
        "funct3": "110",
        "opcode": "1100011"},
    "bgeu":{
        "funct3": "111",
        "opcode": "1100011"}}

# U-type imm[31:12] | rd | opcode

U_type_table = {
    "lui":{
        "opcode": "0110111"},
    "auipc":{
        "opcode": "0010111"}}

# J-type  imm[20|10:1|11|19:12] | rd | opcode

J_type_table = {
    "jal":{
        "opcode": "1101111"}}

registers = {
    "zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011", "tp": "00100",
    "t0": "00101", "t1": "00110", "t2": "00111", "s0": "01000", "fp": "01000",
    "s1": "01001", "a0": "01010", "a1": "01011", "a2": "01100", "a3": "01101",
    "a4": "01110", "a5": "01111", "a6": "10000", "a7": "10001", "s2": "10010",
    "s3": "10011", "s4": "10100", "s5": "10101", "s6": "10110", "s7": "10111",
    "s8": "11000", "s9": "11001", "s10": "11010", "s11": "11011", "t3": "11100",
    "t4": "11101", "t5": "11110", "t6": "11111",
    "x0": "00000", "x1": "00001", "x2": "00010", "x3": "00011", "x4": "00100",
    "x5": "00101", "x6": "00110", "x7": "00111", "x8": "01000",
    "x9": "01001", "x10": "01010", "x11": "01011", "x12": "01100", "x13": "01101",
    "x14": "01110", "x15": "01111", "x16": "10000", "x17": "10001", "x18": "10010",
    "x19": "10011", "x20": "10100", "x21": "10101", "x22": "10110", "x23": "10111",
    "x24": "11000", "x25": "11001", "x26": "11010", "x27": "11011", "x28": "11100",
    "x29": "11101", "x30": "11110", "x31": "11111"}

def immediate(x, bits):
    if bits<=0:
        return "error"
    x=x.strip()
    
    # check sign
    is_negative=False
    if x[0]=="-":
        is_negative=True
        x=x[1:]   # remove '-'
    if x=="" or not x.isdigit():
        return "error"
    y=int(x)
    
    # decimal→binary
    binary_int=0
    place=1
    if y==0:
        binary_int=0
    else:
        while y!=0:
            remainder=y%2
            binary_int=remainder*place+binary_int
            place=place*10
            y=y//2
            
    # integer binary to string
    binary=str(binary_int)
    
    # check for overflow
    if len(binary)>bits:
        return "error"
        
    # extend bits
    while len(binary)<bits:
        binary="0"+binary
        
    # positive number
    if not is_negative:
        return binary
        
    # negative number
    #one's complement
    flipped=""
    i=0
    while i<bits:
        if binary[i]=="0":
            flipped+="1"
        else:
            flipped+="0"
        i+=1
        
    # add 1
    result=list(flipped)
    carry=1
    i=bits - 1
    while i>=0 and carry==1:
        if result[i]=="0":
            result[i]="1"
            carry=0
        else:
            result[i]="0"
        i -=1
        
    #final string using for loop
    final_string=""
    for bit in result:
        final_string=final_string+bit
    return final_string


def encode_R_type(parts):
    instr, rd, rs1, rs2=parts
    entry=R_type_table[instr]

    funct7=entry["funct7"]
    funct3=entry["funct3"]
    opcode=entry["opcode"]

    return funct7+registers[rs2]+registers[rs1]+funct3+registers[rd]+opcode


def encode_I_type(parts):
    instr=parts[0]
    entry=I_type_table[instr]

    funct3=entry["funct3"]
    opcode=entry["opcode"]

    if instr == "lw":
        rd=parts[1]
        offset, rs1=parts[2].split("(")
        rs1=rs1.replace(")", "")
    else:
        rd=parts[1]
        rs1=parts[2]
        offset=parts[3]

    imm_bin=immediate(offset, 12)

    if imm_bin == "error":
        raise ValueError("Illegal Immediate")

    return imm_bin+registers[rs1]+funct3+registers[rd]+opcode


def encode_S_type(parts):
    instr=parts[0]
    entry=S_type_table[instr]

    funct3=entry["funct3"]
    opcode=entry["opcode"]

    rs2=parts[1]
    offset, rs1=parts[2].split("(")
    rs1=rs1.replace(")", "")

    imm_bin=immediate(offset, 12)

    if imm_bin == "error":
        raise ValueError("Illegal Immediate")

    imm_11_5=imm_bin[:7]
    imm_4_0=imm_bin[7:]

    return imm_11_5+registers[rs2]+registers[rs1]+funct3+imm_4_0+opcode


def encode_B_type(parts):
    instr, rs1, rs2, imm=parts
    entry=B_type_table[instr]

    funct3=entry["funct3"]
    opcode=entry["opcode"]

    if imm in label:
        offset=label[imm] - pc
    else:
        offset=int(imm, 0)

    imm_bin=immediate(str(offset), 13)

    if imm_bin == "error":
        raise ValueError("Illegal Immediate")

    return imm_bin[0]+imm_bin[2:8]+registers[rs2]+registers[rs1]+funct3+imm_bin[8:12]+imm_bin[1]+opcode


def encode_U_type(parts):
    instr, rd, imm=parts
    entry=U_type_table[instr]

    opcode=entry["opcode"]

    imm_bin=immediate(imm, 20)

    if imm_bin == "error":
        raise ValueError("Illegal Immediate")

    return imm_bin+registers[rd]+opcode


def encode_J_type(parts):
    instr, rd, imm=parts
    entry=J_type_table[instr]

    opcode=entry["opcode"]

    if imm in label:
        offset=label[imm] - pc
    else:
        offset=int(imm, 0)

    imm_bin=immediate(str(offset), 21)

    if imm_bin == "error":
        raise ValueError("Illegal Immediate")

    return imm_bin[0]+imm_bin[10:20]+imm_bin[9]+imm_bin[1:9]+registers[rd]+opcode

def check_registers(parts):
    i=1
    while i<len(parts):
        p=parts[i]
        if "(" in p:
            r=p[p.find("(")+1:p.find(")")]
            if r not in registers:
                raise ValueError("Invalid register "+r)
        else:
            if p in registers:
                i+=1
                continue
            if p in label:
                i+=1
                continue
            if p.startswith("-"):
                if p[1:].isdigit():
                    i+=1
                    continue
            elif p.isdigit():
                i+=1
                continue
            raise ValueError("Invalid register "+p)
        i+=1

def create_labels_and_instructions(cleaned_lines):
    label={}
    all_instrs=[]
    temp_pc=0
    for line in cleaned_lines:
        instr_body=line
        if ":" in line:
            lbl_name=line[:line.index(":")].strip()
            if lbl_name=="":
                raise ValueError("Empty label")
            if not lbl_name[0].isalpha():
                raise ValueError("Label must start with a letter")
            label[lbl_name]=temp_pc
            instr_body=line[line.index(":")+1:].strip()
        if instr_body!="":
            all_instrs.append(instr_body)
            temp_pc+=4
    return label,all_instrs


def get_instruction_type(instr):
    instr=instr.lower()
    
    if instr in R_type_table:
        return 0

    elif instr in I_type_table:
        return 1

    elif instr in S_type_table:
        return 2

    elif instr in B_type_table:
        return 3

    elif instr in U_type_table:
        return 4

    elif instr in J_type_table:
        return 5

    else:
        return -1


def main_encoder(line):
    parts=line.replace(",", " ").split()

    if len(parts) == 0:
        raise ValueError("Empty instruction")

    check_registers(parts)

    instr=parts[0]
    inst_type=get_instruction_type(instr)

    match inst_type:
        case 0:
            return encode_R_type(parts)
        case 1:
            return encode_I_type(parts)
        case 2:
            return encode_S_type(parts)
        case 3:
            return encode_B_type(parts)
        case 4:
            return encode_U_type(parts)
        case 5:
            return encode_J_type(parts)
        case _:
            raise ValueError("Invalid instruction mnemonic: " + instr)


global pc
pc=0
label={}
all_instrs=[]
input_file=sys.argv[1]
output_file=sys.argv[2]
try:
    fin=open(input_file, "r")
    lines=fin.readlines()
    fin.close()

    cleaned_lines=[]
    for line in lines:
        line=line.strip()
        if line != "":
            cleaned_lines.append(line)

    label, all_instrs=create_labels_and_instructions(cleaned_lines)

    if len(all_instrs) == 0:
        raise ValueError("File is empty")
    normalized = [instr.replace(" ", "") for instr in all_instrs]
    if "beqzero,zero,0" not in normalized:
        raise ValueError("No Virtual Halt instruction found.")
    elif normalized[-1]!="beqzero,zero,0" :
        raise ValueError("Virtual halt not present as the last instruction.")


    fout=open(output_file, "w")

    pc=0
    for instr in all_instrs:
        binary=main_encoder(instr)
        fout.write(binary + "\n")
        pc += 4

    fout.close()

except Exception as e:
    print("Error at line", pc // 4 + 1, ":", e)
