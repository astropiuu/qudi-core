import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from argparse import ArgumentParser

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT= '587'
EMAIL_USER = 'mohitya125@gmail.com'
EMAIL_PASSWORD = 'twip iblb zbck uwpn'
EMAIL_TO = 'mohit.shah@uni-ulm.de'

parser = ArgumentParser()
parser.add_argument('-p', '--python_version', metavar='', required=True, help="python version of workflow")
parser.add_argument('-d', '--diff_file', metavar='', required=True, help="dependency diff dump")
args = parser.parse_args()
python_version = args.python_version
diff_file = args.diff_file

with open(diff_file) as diff:
    dep_diff = ''.join(diff.readlines())

smtp_server = SMTP_SERVER
smtp_port = SMTP_PORT
email_user = EMAIL_USER
email_password = EMAIL_PASSWORD
email_to = EMAIL_TO

# Email content
subject = "❗ GitHub Actions: Test Job Failure Alert"
body = f"""
Hello,

This is an automated message to notify you that the GitHub Actions test job has failed for {python_version}.

The tests failed because of the following dependencies

{dep_diff}

Best regards,
Your GitHub Actions Bot
"""

print(body)
# Create the email
message = MIMEMultipart()
message["From"] = email_user
message["To"] = email_to
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))


try:
    # Establish SSL connection with the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Secure the connection
    # Log in to the SMTP server
    server.login(email_user, email_password)

    # Send the email
    server.sendmail(email_user, email_to, message.as_string())
    print(f"Email sent to {email_to}")

    # Close the connection
    server.quit()

except Exception as e:
    print(f"Failed to send email: {e}")

