import elements_db_functions
import csv
from datetime import datetime
import subprocess
from dotenv import dotenv_values


def main():
    creds = dotenv_values()

    # 90 days
    new_ninety_day_pub_records = elements_db_functions.get_new_lbl_pub_records(
        creds, "lbl-new-pub-records-ninety-days.sql")
    ninety_day_file = write_csv_file(new_ninety_day_pub_records, "LBL-90-Day-pub-records")

    # 1 fiscal year
    new_fiscal_year_pub_records = elements_db_functions.get_new_lbl_pub_records(
        creds, "lbl-new-pub-records-one-fiscal-year.sql")
    three_year_file = write_csv_file(new_fiscal_year_pub_records, "LBL-one-fiscal-year-pub-records")

    # New 90-day pubs with preprint files available
    new_pubs_with_preprints = elements_db_functions.get_new_lbl_pub_records(
        creds, "lbl-new-pubs-with-preprint-files-available.sql")
    with_preprint_file = write_csv_file(new_pubs_with_preprints, "LBL-90-day-pubs-with-preprint-files")

    # Embargoed pubs pubs
    new_embargoed_pubs = elements_db_functions.get_new_lbl_pub_records(
        creds, "lbl-embargoed-pubs.sql")
    embargoed_file = write_csv_file(new_embargoed_pubs, "lbl-embargoed-pubs")

    # Set up the mail process with attachment and email recipients
    subprocess_setup = ['mail',
                        '-s', 'New LBL pub records without eSchol deposits',
                        '-a', ninety_day_file,
                        '-a', three_year_file,
                        '-a', with_preprint_file,
                        '-a', embargoed_file]
    subprocess_setup += [creds['DEVIN'], creds['GEOFF'], creds['ALAINNA']]

    # Text in the email body
    input_byte_string = b'''The attached CSV files show:
    
LBL-90-Day-pub-records:
- Pubs without eScholarship records having an associated file deposit.
  - eSchol OA location URLS are listed where present. 
- with EuroPMC or arXive publication records
- with a Publication "Reporting Date 1" from the past 90 days.
- The sheet is ordered by "most likely candidates" first:
  -  Pub type Journal Article > Preprint
  -  Claimed authors > Pending authors


LBL-one-fiscal-year-pub-records:
- Same as above, but without the 90-day cutoff.
- Records are pulled from the start of the previous fiscal year.


LBL-90-day-pubs-with-preprint-files:
- New LBL publications
- Created in the past 90 days
- Without file deposits (OA Locations are noted when available)
- And have a related "preprint" publication with a file.


LBL-embargoed-pubs:
- Any pubs claimed by an LBL author with an embargo date after "now."
- Funding info included where available.
'''

    # Run the subprocess with EOT input to send
    subprocess.run(subprocess_setup, input=input_byte_string, capture_output=True)


# Writes the CSV and returns the filename for email attachment
def write_csv_file(data, filename):
    filename_with_date = "output/" + filename + "-" + datetime.today().strftime('%Y-%m-%d') + ".csv"
    with open(filename_with_date, "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(data[0].keys())
        for row in data:
            csv_writer.writerow(row.values())
    return filename_with_date


# Stub for main
if __name__ == '__main__':
    main()
