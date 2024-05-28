import creds
import elements_db_functions
import csv
from datetime import datetime
import subprocess


def main():
    sql_creds = creds.elements_reporting_db_server_prod

    new_lbl_pub_records = elements_db_functions.get_new_lbl_pub_records(sql_creds)

    filename = "LBL-90-Day-pub-records-" + datetime.today().strftime('%Y-%m-%d') + ".csv"

    with open("output/" + filename, "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(new_lbl_pub_records[0].keys())
        for row in new_lbl_pub_records:
            csv_writer.writerow(row.values())

    # Set up the mail process with attachment and email recipients
    subprocess_setup = ['mail',
                        '-s', 'New DOE-funded pub records w/o eSchol deposits',
                        '-a', 'output/' + filename]
    subprocess_setup += creds.email_recipients

    # Run the subprocess with EOT input to send
    subprocess.run(subprocess_setup, input=b'\x04')


# Stub for main
if __name__ == '__main__':
    main()
