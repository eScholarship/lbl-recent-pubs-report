import creds
import elements_db_functions
import csv
from datetime import datetime


def main():
    sql_creds = creds.elements_reporting_db_server_prod

    new_lbl_pub_records = elements_db_functions.get_new_lbl_pub_records(sql_creds)

    filename = "LBL-90-Day-pub-records-" + datetime.today().strftime('%Y-%m-%d')

    with open("output/" + filename, "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(new_lbl_pub_records[0].keys())
        for row in new_lbl_pub_records:
            csv_writer.writerow(row.values())


# Stub for main
if __name__ == '__main__':
    main()
