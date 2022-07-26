import kivy
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
import psycopg2
import os

def init_cursor_connection():

    connection = psycopg2.connect(
        host="ec2-3-222-74-92.compute-1.amazonaws.com",
        database="d13c1bqtsscttg",
        user="qvylxhkqjibady",
        port="5432",
        password=os.environ.get('PROJECTSQLPASSWD_1'),

    )

    c = connection.cursor()
    return c, connection


def getMDDataTable(col_names,data):
    table = MDDataTable(
        pos_hint = {'center_x': .5, 'center_y': .5},
        size_hint = (.9, .6),
        check = True,
        use_pagination = True,
        background_color = [1,0,.9,1],
        column_data = [(col_names[i], dp(30)) for i in range(len(col_names))],
        row_data = data,

    )
    return table

def is_integer(A):#A-string
    for char in A:
        if not (ord(char) >= 48 and ord(char) <= 57):
            return False
    return True



def creating_table(current_table, colums2add, types_of_columns):
    c, conn = init_cursor_connection()
    sql_table_create_Q = "CREATE TABLE if not exists {} ( "

    for i in range(len(colums2add)):
        sql_table_create_Q = sql_table_create_Q + colums2add[i] + ' ' + types_of_columns[i] + ', '

    sql_table_create_Q = sql_table_create_Q[:-2]
    sql_table_create_Q = sql_table_create_Q + ')'
    c.execute(sql_table_create_Q.format(current_table))

    conn.commit()

    conn.close()

def fetching_tables():
    cursor, connection = init_cursor_connection()
    tables = []
    cursor.execute("""SELECT table_name FROM information_schema.tables
                   WHERE table_schema = 'public'""")

    for table in cursor.fetchall():
        tables.append(table[0])

    return tables

def get_datatypes(name_of_table):
    cursor, connection = init_cursor_connection()
    cursor.execute(
        "SELECT data_type FROM information_schema.columns WHERE table_name = '{}';".format(name_of_table)
    )

    data_types = cursor.fetchall()
    result = []
    for i in range(len(data_types)):
        result.append(data_types[i][0])
    return result

def building_command_adding_row(current_table, col_names, txtRowInputs):
    c, conn = init_cursor_connection()
    # Add a record
    data_types = get_datatypes(current_table)

    sql_command = "INSERT INTO {} (".format(current_table)  # VALUES (%s)"

    for col_name in col_names:
        sql_command = sql_command + col_name + ","

    sql_command = sql_command[:-1]
    sql_command = sql_command + ") VALUES ("

    for i, txtinpt in enumerate(txtRowInputs):
        if data_types[i] == 'text':
            sql_command = sql_command + "\'" + txtinpt.text + "\'" + ","
        elif is_integer(txtinpt.text):
            sql_command = sql_command + txtinpt.text + ","
        else:
            for txtinpt in txtRowInputs:
                txtinpt.text = ""
            return True


    sql_command = sql_command[:-1]
    sql_command = sql_command + ")"

    c.execute(sql_command)

    # Commit changes
    conn.commit()
    conn.close()

    return False

def selecting_table(selected_name, tables,):

    cursor, connection = init_cursor_connection()
    col_names = []
    txtRowInputs = []
    there_is = False

    for table in tables:
        if selected_name == table:
            there_is = True
            break

    if not there_is:
        return True, None, col_names, txtRowInputs#invalid input
    else:

        cursor.execute("Select * FROM {} LIMIT 0".format(selected_name))
        col_names = [desc[0] for desc in cursor.description]
        txtRowInputs = [TextInput(font_size=32, multiline=False, ) for _ in range(len(col_names))]
        return False, selected_name, col_names, txtRowInputs



def deleting_table(name):
    cursor, connection = init_cursor_connection()
    sql_command = "DROP TABLE {};".format(name)
    cursor.execute(sql_command)

    connection.commit()
    connection.close()

class Tables(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.current_table = None
        self.colums2add = []
        self.types_of_columns = []
        self.tables = []
        self.col_names = []
        self.txtRowInputs = []
        self.input_error  = False
        self.table2show = None

        return Builder.load_file("nmy.kv")


    def show_records(self):

        c, conn = init_cursor_connection()

        # Grab records from database
        c.execute("SELECT * FROM {}".format(self.current_table))
        records = c.fetchall()
        self.table2show = getMDDataTable(self.col_names, records)
        conn.commit()
        conn.close()

    def set_table_name(self,name):
        all_words = name.split()
        if len(all_words) == 0 or is_integer(all_words[0]):
            self.input_error = True
            return
        name = all_words[0]
        self.current_table = name


    def add_column_type(self, name, type):
        all_words = name.split()
        if len(all_words) == 0 or is_integer(all_words[0]):
            self.input_error = True
            return
        name = all_words[0]
        self.colums2add.append(name)
        self.types_of_columns.append(type)


    def create_table(self):
        creating_table(self.current_table, self.colums2add, self.types_of_columns)
        self.current_table = None
        self.colums2add = []
        self.types_of_columns = []


    def set_tables(self):
        self.tables = fetching_tables()


    def select_this_table(self, name):
        self.input_error, self.current_table, self.col_names, self.txtRowInputs = selecting_table(name, self.tables)


    def addRecord(self):
        self.input_error = building_command_adding_row(self.current_table, self.col_names, self.txtRowInputs)
        for inpt in self.txtRowInputs:
            inpt.text = ""

    def delete_table(self):
        deleting_table(self.current_table)




if __name__ == '__main__':
    Tables().run()
