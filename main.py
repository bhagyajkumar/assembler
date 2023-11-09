import sqlite3
from tabulate import tabulate

db = sqlite3.connect(":memory:")

curr = db.cursor()
curr.execute("CREATE TABLE commands (mem_loc string, label string, opcode string, operand string);")
curr.execute("CREATE TABLE symbols (label string, mem_loc string)")
curr.close()

pgm_name = ""
pc = 0
initial_memory_location = None
instructions = None

optab = {
    "LDA" : "23",
    "ADD" : "69",
    "HLDA" : "2F"
}

with open("ins.asm", "r") as f:
    instructions = f.read()
    instructions = instructions.strip()

def extract_lines(st: str):
    return st.split("\n")

def get_command_items(cmd: str):
    cmd = cmd.strip()
    items = cmd.split(" ")
    for i, j in enumerate(items):
        if len(j) == 0:
            items.pop(i)
    return items

def tokenize(command_items):
    global pgm_name
    global pc
    global initial_memory_location
    
    details = {}
    first_line = command_items[0]
    if first_line[1] == "START":
        pgm_name = first_line[0]
        initial_memory_location = int(first_line[2], 16)
        pc = initial_memory_location
        details[hex(pc)] = {
            "LABEL": pgm_name,
            "OPCODE": "START",
            "OPERAND": first_line[2]
        }
        for i in command_items[1:]:
            label = ""
            opcode = ""
            operand = ""
            if len(i) == 3:
                label = i[0]
                opcode = i[1]
                operand = i[2]

            elif len(i) == 2:
                label = None
                opcode = i[0]
                operand = i[1]

            elif len(i) == 1:
                opcode = i[0]

            if opcode == "WORD":
                pc += 3
            elif opcode == "RESW":
                pc += int(operand, 16) * 3
            elif opcode == "BYTE":
                pc += len(operand)
            elif opcode == "RESB":
                pc += int(operand)
            else:
                pc += 3

            if opcode == "END":
                break

            details[hex(pc)] = {
                "LABEL": label,
                "OPCODE": opcode,
                "OPERAND": operand
            }

            if label is not None:

                if label in symbols.keys():
                    raise "Duplicate Symbol"
                if len(label) > 0:
                    symbols[label] = hex(pc)
                    curr = db.cursor()
                    curr.execute("INSERT INTO symbols (label, mem_loc) values (?,?)", [label, hex(pc)])

            curr = db.cursor()
            curr.execute("INSERT INTO commands (mem_loc, label, opcode, operand) VALUES (?,?,?,?)",
                         [hex(pc), label, opcode, operand])
            db.commit()
            curr.close()
        curr = db.cursor()
        curr.execute("INSERT INTO commands (mem_loc, label, opcode, operand) VALUES (?,?,?,?)",
                         [hex(pc), "", "END",""])
        db.commit()
    else:
        print("error initialization")


lines = extract_lines(instructions)
command_items = []
symbols = {}

for i in lines:
    command_items.append(get_command_items(i))

tokenize(command_items)

curr = db.cursor()

header = ["mem_loc", "label", "opcode", "operand"]
res = curr.execute("SELECT mem_loc, label, opcode, operand FROM commands;")
db_data = res.fetchall()

print("\n\n Intermediate table \n ------------------")
print(tabulate(db_data, headers=header, tablefmt="grid"))

print("\n\nSymbol table \n------------")
header = ["label", "mem_loc"]
res = curr.execute("SELECT mem_loc, label FROM symbols;")
db_data = res.fetchall()
print(tabulate(db_data, headers=header, tablefmt="grid"))


def pass2():
    curr = db.cursor()
    header = "H"
    header += pgm_name.ljust(6)
    header += hex(initial_memory_location)[2:].rjust(6, '0')
    length = pc - initial_memory_location
    header += hex(length)[2:].rjust(6, '0')
    print(header)

    text_record = ""
    for row in curr.execute("SELECT mem_loc, opcode, operand FROM commands WHERE opcode NOT LIKE 'RES%' AND opcode <> 'END';"):
        mem_loc, opcode, operand = row
        if len(text_record) == 0:
            text_record += "T" + hex(int(mem_loc, 16))[2:].rjust(6, '0')

        text_record += optab[opcode] + (operand if operand is not None else "")

    if len(text_record) > 0:
        print(text_record)

    for row in curr.execute("SELECT operand FROM commands WHERE opcode='END';"):
        operand, = row
        print("E" + operand.rjust(6, '0'))


pass2()
