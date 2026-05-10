import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(to, subject, body):
    """
    Send an email using SMTP.

    Args:
        to (str): Recipient email.
        subject (str): Email subject.
        body (str): Email body.

    Note: Requires EMAIL_USER and EMAIL_PASS in environment.
    """
    user = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASS')
    if not user or not password:
        return "Email credentials not set."

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        text = msg.as_string()
        server.sendmail(user, to, text)
        server.quit()
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"