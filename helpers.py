def make_table(input) -> str:
    column_widths = []

    for i,column in enumerate(input):
        column_widths.append(0)
        for subitem in input[i]:
            if len(subitem) > column_widths[i]:
                column_widths[i] = len(subitem)

    #top line
    table = "+"
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
            table = " ".join([table, column[0]])
            table = "".join([table, " "*(column_widths[i] + 1 - len(column[0]))])
            del column[0]
        table = "".join([table, "|\n"])
    
    #bottom line
    table = "".join([table, "+"])
    for column_width in column_widths:
        table = "".join([table, "-"*(column_width+2)])
        table = "".join([table, "+"])
    
    return(table)