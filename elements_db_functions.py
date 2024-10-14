import pyodbc


def get_new_lbl_pub_records(creds, input_file):

    # Load SQL file
    sql_file = open(input_file)
    sql_query = sql_file.read()

    # Connect to Elements reporting db
    conn = pyodbc.connect(
        driver=creds['ELEMENTS_REPORTING_DB_DRIVER'],
        server=(creds['ELEMENTS_REPORTING_DB_SERVER'] + ',' + creds['ELEMENTS_REPORTING_DB_PORT']),
        database=creds['ELEMENTS_REPORTING_DB_DATABASE'],
        uid=creds['ELEMENTS_REPORTING_DB_USER'],
        pwd=creds['ELEMENTS_REPORTING_DB_PASSWORD'],
        trustservercertificate='yes')

    print(f"Connected to Elements reporting DB, querying: {input_file}")
    conn.autocommit = True  # Required when queries use TRANSACTION
    cursor = conn.cursor()
    cursor.execute(sql_query)

    # pyodbc doesn't return dicts automatically, we have to make them ourselves
    columns = [column[0] for column in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return rows
