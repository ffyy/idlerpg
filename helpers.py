import re

def make_table(input) -> str:
    column_widths = []
    RIGHT_ALIGN_EXPRESSION = "^(?:\d+(?:\.\d+)?h?|\d+\/\d+|\d+->\d+|-\d+)$" #used to identify cells which should be right aligned

    for i,column in enumerate(input):
        column_widths.append(0)
        for subitem in input[i]:
            if len(subitem) > column_widths[i]:
                column_widths[i] = len(subitem)

    #top line
    table = "```\n+"
    for column_width in column_widths:
        table = "".join([table, "-"*(column_width+2)])
        table = "".join([table, "+"])
    table = "".join([table, "\n"])

    #headers
    for i,column in enumerate(input):
        table = "".join([table, "|"])
        table = " ".join([table, column[0]])
        table = "".join([table, " "*(column_widths[i] + 1 - len(column[0]))])
    table = "".join([table, "|\n+"])

    #line below
    for column_width in column_widths:
        table = "".join([table, "-"*(column_width+2)])
        table = "".join([table, "+"])
    table = "".join([table, "\n"])

    #rows
    for header in input:
        del header[0]

    while len(input[0]) > 0:
        for i, column in enumerate(input):
            table = "".join([table, "|"])
            if re.match(RIGHT_ALIGN_EXPRESSION, column[0]):
                table = "".join([table, " "*(column_widths[i] + 1 - len(column[0]))])
                table = "".join([table, column[0]])
                table = "".join([table, " "])
            if not re.match(RIGHT_ALIGN_EXPRESSION, column[0]):
                table = " ".join([table, column[0]])
                table = "".join([table, " "*(column_widths[i] + 1 - len(column[0]))])
            del column[0]
        table = "".join([table, "|\n"])

    #bottom line
    table = "".join([table, "+"])
    for column_width in column_widths:
        table = "".join([table, "-"*(column_width+2)])
        table = "".join([table, "+"])
    table = "".join([table, "```"])

    return(table)

def make_hp_bar(current_hp, max_hp, width=10) -> str:
    hp_ratio = current_hp / max_hp * width
    filled_squares = int(hp_ratio)

    FILLED_SYMBOL = "■"
    EMPTY_SYMBOL = "□"
    PARTIAL_SYMBOL = "□"

    hp_bar = "["
    for i in range(filled_squares):
        hp_bar= "".join([hp_bar, FILLED_SYMBOL])

    if filled_squares > 0 and hp_ratio % filled_squares > 0:
        hp_bar= "".join([hp_bar, PARTIAL_SYMBOL])
        filled_squares += 1

    for i in range(width-filled_squares):
        hp_bar= "".join([hp_bar, EMPTY_SYMBOL])

    hp_bar= "".join([hp_bar, "]"])

    return hp_bar

def make_boss_hp_bar(name, current_hp, max_hp, width=50, target_number=None) -> str:
    boss_string = "".join([" "*((width+1-len(name))//2), name])
    hp_bar = make_hp_bar(current_hp, max_hp, width)
    boss_hp_bar = "```\n"
    boss_hp_bar = "".join([boss_hp_bar, boss_string])
    boss_hp_bar = "\n".join([boss_hp_bar, hp_bar])
    if target_number:
        target_number_string_length = len("Target number: " + str(target_number))
        boss_hp_bar = "\n".join([boss_hp_bar, " "*((width+1-target_number_string_length)//2)])
        boss_hp_bar = "".join([boss_hp_bar, "Target number:"])
        boss_hp_bar = " ".join([boss_hp_bar, str(target_number)])
        print(boss_string)
    boss_hp_bar = "".join([boss_hp_bar, "```"])
    return boss_hp_bar

def debug_print(var):
    printstring = "------"
    printstring = "\n".join([printstring,"the type is"])
    printstring = " ".join([printstring, str(type(var))])
    printstring = "\n".join([printstring, "the string representation is"])
    printstring = " ".join([printstring, str(var)])
    try:
        printstring = "\n".join([printstring, "the vars are"])
        printstring = " ".join([printstring, vars(var)])
    except:
        pass
    printstring = "\n".join([printstring, "------"])
    print(printstring)