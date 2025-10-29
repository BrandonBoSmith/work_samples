import config
import logging.config
import pprint
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.client import HTTPMessage
from urllib.parse import urlsplit

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

try:
    from email.mime.text import MIMEText
    import base64
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    logger.info("Gmail modules loaded successfully")
except Exception as err:
    logger.error(f"Error importing modules {str(err)}")


class SMTP:
    """
    A class to send emails over smtp.
    
    Attributes:
        config (dict): A dictionary containing configuration settings.
        sender (str): The sender's email address.
        password (str): The sender's email password.
        recipient (str): The recipient's email address.
        subject (str): The email subject.
        body (str or HTTPMessage): The email body, either as a string or an HTTPMessage object.
    """

    def __init__(self, config):
        self.config = config
        if not 'sender' in config:
            raise ValueError("Sender's email address is missing from configuration.")
        if not 'password' in config or not config['password']:
            raise ValueError("Sender's email password is missing from configuration.")
        if not 'recipient' in config:
            raise ValueError("Recipient's email address is missing from configuration.")
        if not 'subject' in config:
            raise ValueError("Email subject is missing from configuration.")
        if not 'body' in config or not config['body']:
            raise ValueError("Email body is missing from configuration.")
        self.body = f"""
        <p>Hello {first_name},</p>
        <p>Thank you for choosing ACS.  We look forward to serving you.</p>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verification_link}">{verification_link}</a></p>
        """
        self.sender = config['sender']
        self.password = config['password']
        self.recipient = config['recipient']
        self.subject = config['subject']
        self.body = config['body']
        logger.debug('Email Config:')
        logger.debug(pprint.pformat(self.config))

    def send_email(self):
        """
        Send the email using smtp.
        
        Returns:
            bool: True if the email is sent successfully, False otherwise.
        """

        # Create a message
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = self.subject

        try:
            # Add the body of the email
            if isinstance(self.body, str):
                if self.config.get('http_body'):
                    # If http_body is True, convert the string to an HTTPMessage object
                    import urllib.parse
                    from email.mime.http import MIMEHttp
                    msg.attach(MIMEHttp(urlsplit(self.body).path, 'text/html'))
                else:
                    msg.attach(MIMEText(self.body, 'plain'))
            elif isinstance(self.body, HTTPMessage):
                # If body is an HTTPMessage object, attach it to the message
                if self.config.get('http_body'):
                    msg.attach(self.body)
                else:
                    raise ValueError("Cannot attach HTTPMessage to email without http_body enabled")

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        try:
            # Set up the smtp server
            if self.config.get('smtp_server'):
                server = smtplib.SMTP(self.config['smtp_server'], 587)
                server.starttls(context=ssl.create_default_context())
            else:
                raise ValueError("SMTP server is missing from configuration.")

            if self.config.get('smtp_username'):
                server.login(self.sender, self.password)

            # Send the email
            text = msg.as_string()
            server.sendmail(msg['From'], [self.recipient], text)
            server.quit()
            logger.info(f'Email sent successfully to {self.recipient}')
            return True

        except Exception as e:
            print(f"An error occurred: {e}")
            logger.error(f"Error: {e}")
            return False


class Gmail:
    """
    A class to send emails via gmail api.

    Requirements:
        Google cloud project (free)
        Gmail API Enabled (free)
        Service Account w/json key

    Attributes:
        config (dict): A dictionary containing configuration settings.
        sender (str): The sender's email address.
        password (str): The sender's email password.
        recipient (str): The recipient's email address.
        subject (str): The email subject.
        body (str or HTTPMessage): The email body, either as a string or an HTTPMessage object.
    """


    def __init__(self, client, delegate, body, svcaccount="key.json"):
        """
        Initialize Gmail class
        """

        self.body = body
        self.delegate = delegate
        self.svcaccount = svcaccount
        self.client = client
        self.scopes = ["https://www.googleapis.com/auth/gmail.send"]
        self.creds = service_account.Credentials.from_service_account_file(
            self.svcaccount, scopes=self.scopes
        ).with_subject(self.delegate)
        self.service = build("gmail", "v1", credentials=self.creds)
        logger.info("Gmail initialized")


    def send_email(self):
        """
        Send email to the client
        """
        msg = MIMEText(self.body, "html")
        msg["to"] = self.client
        msg["from"] = self.delegate
        msg["subject"] = "Welcome to ACS!"

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        body = {"raw": raw}

        try:
            self.service.users().messages().send(
                userId=self.delegate, body=body
            ).execute()
            logger.info(f"Email sent successfully to {self.client}")
        except Exception as err:
            logger.error(f"Error occurred sending email: {str(err)}")
