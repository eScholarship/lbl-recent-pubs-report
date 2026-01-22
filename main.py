from pub_oapi_tools_common import ucpms_db
from pub_oapi_tools_common import aws_lambda
from pub_oapi_tools_common.misc import log

import csv
from datetime import datetime
import subprocess
import requests


def main():

    # Input and output filenames
    sql_files = [
        {"input": "lbl-new-pub-records-ninety-days.sql",
         "output": "LBL-90-Day-pub-records"},
        {"input": "lbl-new-pub-records-ninety-days-oap-only.sql",
         "output": "LBL-90-Day-pub-records-OAP-only"},
        {"input": "lbl-new-pub-records-one-fiscal-year.sql",
         "output": "LBL-one-fiscal-year-pub-records"},
        {"input": "lbl-new-pubs-with-preprint-files-available.sql",
         "output": "LBL-90-Day-pub-records"},
        {"input": "lbl-new-pub-records-ninety-days.sql",
         "output": "LBL-90-day-pubs-with-preprint-files"},
        {"input": "lbl-embargoed-pubs.sql",
         "output": "lbl-embargoed-pubs"}]

    # Loops sql_files, saving .csvs and adding the filename for email attachments.
    for file in sql_files:
        records = get_new_lbl_pub_records(file['input'])
        file['output_file'] = write_csv_file(records, file['output'])

    # Set up the mail process with attachment and email recipients
    subprocess_setup = ['mail', '-s', 'New LBL pub records without eSchol deposits']
    for file in sql_files:
        subprocess_setup += ['-a', file['output_file']]

    email_creds = aws_lambda.get_parameters(
        {"email_addresses": {
            "folder": "pub-oapi-tools/emails",
            "names": ['devin', 'geoff', 'alainna']}})
    subprocess_setup += email_creds['email_addresses'].values()

    # Email body text
    input_byte_string = get_email_body_text()

    # Run the subprocess with EOT input to send
    subprocess.run(subprocess_setup,
                   input=input_byte_string,
                   capture_output=True)


# Writes the CSV and returns the filename for email attachment
def write_csv_file(data, filename):
    filename_with_date = "output/" + filename + "-" + datetime.today().strftime('%Y-%m-%d') + ".csv"
    with open(filename_with_date, "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(data[0].keys())
        for row in data:
            csv_writer.writerow(row.values())
    return filename_with_date


# Query the reporting DB and return the data
def get_new_lbl_pub_records(input_file):
    # Load the sql file data from Github
    github_raw_link = "https://raw.githubusercontent.com/eScholarship/lbl-recent-pubs-report/main/"
    response = requests.get(f"{github_raw_link}{input_file}")
    sql_query = response.text

    conn = ucpms_db.get_connection(env="prod")
    log("INFO", __name__,
        f"Connected to Elements reporting DB, querying: {input_file}")
    with conn.cursor() as cursor:
        cursor.execute(sql_query)
        rows = ucpms_db.get_dict_list(cursor)
        cursor.close()
    conn.close()

    return rows


def get_email_body_text():
    return(
        b'''The attached CSV files show:

    LBL-90-Day-pub-records:
    - Pubs without eScholarship records having an associated file deposit.
      - eSchol OA location URLS are listed where present. 
    - with EuroPMC or arXive publication records
    - with a Publication "Reporting Date 1" from the past 90 days.
    - The sheet is ordered by "most likely candidates" first:
      -  Pub type Journal Article > Preprint
      -  Claimed authors > Pending authors


    + The same report, but only items covered by LBL OA Policies.

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


    ---

    Future-proofing: This is an automated email sent from the pub-oapi-tools stack. 
    The Repo for this program is https://github.com/eScholarship/lbl-recent-pubs-report
    ''')


# Stub for main
if __name__ == '__main__':
    main()
