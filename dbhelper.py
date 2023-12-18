import sqlite3 as sl
con = sl.connect('DB-ChartMogul.db')
def table_exists(table_name):
    cursor = con.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    rows = cursor.fetchall()
    return len(rows) > 0

def insert_record(table_name, values):
    cursor = con.cursor()
    cursor.execute(f"INSERT INTO {table_name} VALUES (?, ?)", values)
    con.commit()

def insert_array(table_name, array):
    if array:
        length =  len(array[0])
        s = (length * "?,").strip(",")
        cursor = con.cursor()
        cursor.executemany(f"INSERT INTO {table_name} VALUES (%s)"%s, array)
        con.commit()        
def create_table(table_name, schema):
    cursor = con.cursor()
    if not table_exists(table_name):
        cursor.execute(f"CREATE TABLE {table_name} {schema}")  

def isCustomerExist(email):
    cursor = con.cursor()
    cursor.execute(f"SELECT cmID FROM users WHERE email='{email}'")
    rows = cursor.fetchone()
    return rows

def getInvoiceID(email):
    cursor = con.cursor()
    cursor.execute(f"SELECT cmInvoiceID FROM invoices WHERE email='{email}' ORDER BY created_at DESC")
    invID = cursor.fetchone()
    return invID

def isInvoiceExists(gumID):
    cursor = con.cursor()
    cursor.execute(f"SELECT gumroadID FROM invoices WHERE gumroadID='{gumID}'")
    rows = cursor.fetchone()
    return rows

def isTransactionExists(gumID):
    cursor = con.cursor()
    cursor.execute(f"SELECT gumroadID FROM transactions WHERE gumroadID='{gumID}'")
    rows = cursor.fetchone()
    return rows

def getCustomers():
    cursor = con.cursor()
    cursor.execute(f"select DISTINCT(email) from gumroad_data;")
    rows = cursor.fetchall()
    return rows

def getDelCustomers():
    cursor = con.cursor()
    cursor.execute(f"select cmID from users;")
    rows = cursor.fetchall()
    return rows 

def getDelCustomersByEmail(email):
    cursor = con.cursor()
    cursor.execute(f"select cmID from users where email='{email}';")
    rows = cursor.fetchall()
    print(rows)
    return rows     

def init():
    if not table_exists('users'):
        create_table('users', '(email TEXT PRIMARY KEY, cmID TEXT)')        
    if not table_exists('invoices'):
        create_table('invoices', '(gumroadID TEXT PRIMARY KEY, email, cmInvoiceID TEXT, created_at timestamp DEFAULT CURRENT_TIMESTAMP)')
    if not table_exists('transactions'):
        create_table('transactions', '(email , gumroadID TEXT PRIMARY KEY, created_at timestamp  default CURRENT_TIMESTAMP)')        
        
init()