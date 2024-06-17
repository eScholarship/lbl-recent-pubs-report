import creds
import elements_db_functions
import csv
from datetime import datetime
import subprocess


def main():
    sql_creds = creds.elements_reporting_db_server_prod

    # 90 days
    new_ninety_day_pub_records = elements_db_functions.get_new_lbl_pub_records(
        sql_creds, "lbl-new-pub-records-ninety-days.sql")

    ninety_day_file = "LBL-90-Day-pub-records-" + datetime.today().strftime('%Y-%m-%d') + ".csv"

    with open("output/" + ninety_day_file, "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(new_ninety_day_pub_records[0].keys())
        for row in new_ninety_day_pub_records:
            csv_writer.writerow(row.values())

    # 3 fiscal years
    new_three_year_pub_records = elements_db_functions.get_new_lbl_pub_records(
        sql_creds, "lbl-new-pub-records-three-fiscal-year.sql")

    three_year_file = "LBL-three-fiscal-year-pub-records-" + datetime.today().strftime('%Y-%m-%d') + ".csv"
            
    with open("output/" + three_year_file, "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(new_three_year_pub_records[0].keys())
        for row in new_three_year_pub_records:
            csv_writer.writerow(row.values())

    # Set up the mail process with attachment and email recipients
    subprocess_setup = ['mail',
                        '-s', 'New DOE-funded pub records w/o eSchol deposits',
                        '-a', 'output/' + ninety_day_file,
                        '-a', 'output/' + three_year_file
                        ]
    subprocess_setup += creds.email_recipients

    input_byte_string = b'''The attached CSV file includes:

- DOE-funded publications
- without eScholarship publication records
- with EuroPMC or arXive publication records
- with a Publication "Reporting Date 1" from the past 90 days.'''

    # Run the subprocess with EOT input to send
    subprocess.run(subprocess_setup, input=input_byte_string, capture_output=True)


# Stub for main
if __name__ == '__main__':
    main()
