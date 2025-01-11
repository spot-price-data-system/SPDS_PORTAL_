import sqlite3, openpyxl, os

scale_factor = 1000000

collumnfactors = [
    1,#time stamp
    scale_factor,#spot price
    1,#signal
    1,#connected
    scale_factor,#kw out
    scale_factor,#penstock pressure
    scale_factor,#flow
    scale_factor,#water_level
    scale_factor,#tb ds
    scale_factor,#tb nds
    scale_factor,#tb ax
    scale_factor,#tw u
    scale_factor,#tw v
    scale_factor,#tw w
    scale_factor,#v ds
    scale_factor,#v nds
    scale_factor,#v ax
    scale_factor,#hydraulic pressure
    scale_factor,#spot price cycle time
    scale_factor,#opcua cycle time
    1,#tailgate sensor
    scale_factor,#tailwater level
    scale_factor,#flowmeter flow
    scale_factor,#water count total
    scale_factor,#avg_battery_current
    scale_factor#max_battery_current
]

def excel(filepath,root):
    conn = sqlite3.connect(filepath)
    cursor = conn.cursor()

    #if there are any, fetch tables
    try:
        tables = [elem[0] for elem in cursor.execute("SELECT name FROM sqlite_master").fetchall()]
    except:
        tables = []
        
    spreadsheet = openpyxl.Workbook()#create new workbook
    
    for table in tables:
        with open("headings.txt","r") as file:
            headers = file.readline().strip().split(",")
        maxdata = len(headers)

        rows_query = "SELECT * FROM " + table#make query to fetch rows
        rows = cursor.execute(rows_query).fetchall()#fetch row data

        sheet = spreadsheet.create_sheet(table)#create new sheet
        sheet.title = table#set sheet title to table name

        x=1
        y=1

        #add headers to sheet
        for header in headers:
            sheet.cell(row=y,column=x,value=header)
            x+=1

        #add rows to sheet
        for row in rows:
            y+=1
            x=1
            for data in row:
                if x > maxdata:
                    break
                if data and type(data)!=str:
                    data = data / collumnfactors[x-1]
                sheet.cell(row=y,column=x,value=data)
                x+=1
    
    #delete blank sheet
    blank = spreadsheet["Sheet"]
    spreadsheet.remove(blank)

    conn.close()
    os.remove("portal_data.db")
    filepath = os.path.join(root,"portal_data.xlsx")
    if os.path.exists(filepath):
        os.remove(filepath)#if previous excel copy exists, delete it

    #save
    spreadsheet.save(os.path.join(root,"portal_data.xlsx"))
