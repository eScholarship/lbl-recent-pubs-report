import csv
from datetime import datetime
import subprocess
import boto3
import pyodbc

# Get AWS session
session = boto3.Session()


def main():

    reporting_db_creds = get_ssm_parameters(
        folder="/pub-oapi-tools/elements-reporting-db/prod/",
        names=['driver', 'server', 'database', 'user', 'password'])

    # 90 days
    new_ninety_day_pub_records = get_new_lbl_pub_records(
        reporting_db_creds, "lbl-new-pub-records-ninety-days.sql")
    ninety_day_file = write_csv_file(
        new_ninety_day_pub_records, "LBL-90-Day-pub-records")

    new_ninety_day_pub_records = get_new_lbl_pub_records(
        reporting_db_creds, "lbl-new-pub-records-ninety-days-oap-only.sql")
    ninety_day_oap_file = write_csv_file(
        new_ninety_day_pub_records, "LBL-90-Day-pub-records-OAP-only")

    # 1 fiscal year
    new_fiscal_year_pub_records = get_new_lbl_pub_records(
        reporting_db_creds, "lbl-new-pub-records-one-fiscal-year.sql")
    three_year_file = write_csv_file(
        new_fiscal_year_pub_records, "LBL-one-fiscal-year-pub-records")

    # New 90-day pubs with preprint files available
    new_pubs_with_preprints = get_new_lbl_pub_records(
        reporting_db_creds, "lbl-new-pubs-with-preprint-files-available.sql")
    with_preprint_file = write_csv_file(
        new_pubs_with_preprints, "LBL-90-day-pubs-with-preprint-files")

    # Embargoed pubs pubs
    new_embargoed_pubs = get_new_lbl_pub_records(
        reporting_db_creds, "lbl-embargoed-pubs.sql")
    embargoed_file = write_csv_file(
        new_embargoed_pubs, "lbl-embargoed-pubs")

    # Set up the mail process with attachment and email recipients
    email_creds = get_ssm_parameters(
        folder="/pub-oapi-tools/emails",
        names=['devin', 'geoff', 'alainna'])

    subprocess_setup = ['mail',
                        '-s', 'New LBL pub records without eSchol deposits',
                        '-a', ninety_day_file,
                        '-a', ninety_day_oap_file,
                        '-a', three_year_file,
                        '-a', with_preprint_file,
                        '-a', embargoed_file]

    subprocess_setup += [
        email_creds['DEVIN'],
        email_creds['GEOFF'],
        email_creds['ALAINNA']]

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

Future-proofing: This is an automated email sent from the pub-oapi-tools stack. The Repo for this program is https://github.com/eScholarship/lbl-recent-pubs-report
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


# Parses data from parameter store
def get_ssm_parameters(folder, names):
    print("Connect to SSM for parameters")
    ssm_client = session.client(service_name='ssm', region_name='us-west-2')

    param_names = [f"{folder}{name}" for name in names]
    response = ssm_client.get_parameters(Names=param_names, WithDecryption=True)

    param_values = {
        (param['Name'].split('/')[-1]): param['Value']
        for param in response['Parameters']}

    return param_values


# Query the reporting DB and return the data
def get_new_lbl_pub_records(creds, input_file):

    # Load SQL file
    sql_file = open(input_file)
    sql_query = sql_file.read()

    # Connect to Elements reporting db
    conn = pyodbc.connect(
        driver=creds['driver'],
        server=(creds['server'] + ',1433'),
        database=creds['database'],
        uid=creds['user'],
        pwd=creds['password'],
        trustservercertificate='yes')

    print(f"Connected to Elements reporting DB, querying: {input_file}")
    conn.autocommit = True  # Required when queries use TRANSACTION
    cursor = conn.cursor()
    cursor.execute(sql_query)

    # pyodbc doesn't return dicts automatically, we have to make them ourselves
    columns = [column[0] for column in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return rows



# Stub for main
if __name__ == '__main__':
    main()
