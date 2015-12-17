import xlwt


def save_worksheet(filename, data):
    '''
    Saves data to an excel named filename
    :param filename: The name of the file to be created
    :param data: data is a list of lists. It's a list of lines, and each line is a list of fields
    :return:
    '''
    wb = xlwt.Workbook()
    ws = wb.add_sheet('sheet 1')

    for i, line in enumerate(data):
        for j, field in enumerate(line):
            ws.write(i, j, field)
    wb.save(filename)
