"""
Email service providers for Celestia
Switch between different email providers easily
"""
import smtplib
import os
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailProvider:
    """Base email provider class"""
    
    def send_email(self, to_email: str, subject: str, html_content: str):
        raise NotImplementedError

class SendGridProvider(EmailProvider):
    """SendGrid email provider"""
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL')
    
    def send_email(self, to_email: str, subject: str, html_content: str):
        try:
            if not self.api_key or not self.sender_email:
                print(f"❌ Missing SendGrid configuration")
                return False
                
            message = Mail(
                from_email=self.sender_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ SendGrid EMAIL SENT TO: {to_email}")
                return True
            else:
                print(f"❌ SendGrid failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ SendGrid email failed: {str(e)}")
            return False

class BrevoProvider(EmailProvider):
    """Brevo (Sendinblue) email provider - FREE 300 emails/day"""
    
    def __init__(self):
        self.api_key = os.environ.get('BREVO_API_KEY')  # Get from brevo.com
        self.sender_email = os.environ.get('SENDER_EMAIL')
    
    def send_email(self, to_email: str, subject: str, html_content: str):
        try:
            import requests
            
            if not self.api_key or not self.sender_email:
                print(f"❌ Missing Brevo configuration")
                return False
            
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            data = {
                "sender": {"email": self.sender_email, "name": "Celestia Astrology"},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 201:
                print(f"✅ Brevo EMAIL SENT TO: {to_email}")
                return True
            else:
                print(f"❌ Brevo failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Brevo email failed: {str(e)}")
            return False

class GmailSMTPProvider(EmailProvider):
    """Gmail SMTP provider - FREE 500 emails/day"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.environ.get('GMAIL_EMAIL')  # Your Gmail address
        self.sender_password = os.environ.get('GMAIL_APP_PASSWORD')  # App-specific password
    
    def send_email(self, to_email: str, subject: str, html_content: str):
        try:
            if not self.sender_email or not self.sender_password:
                print(f"❌ Missing Gmail SMTP configuration - need GMAIL_EMAIL and GMAIL_APP_PASSWORD")
                print(f"📧 Gmail SMTP Provider: Using {self.sender_email} (app password needed)")
                return False
            
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Celestia Astrology <{self.sender_email}>"
            msg['To'] = to_email
            
            # Add HTML content
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, to_email, msg.as_string())
            server.quit()
            
            print(f"✅ Gmail SMTP EMAIL SENT TO: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Gmail SMTP email failed: {str(e)}")
            print(f"📧 Gmail SMTP Provider: Using {self.sender_email} (check app password configuration)")
            return False

class MailgunProvider(EmailProvider):
    """Mailgun email provider - FREE 5000 emails/month for 3 months"""
    
    def __init__(self):
        self.api_key = os.environ.get('MAILGUN_API_KEY')
        self.domain = os.environ.get('MAILGUN_DOMAIN')
        self.sender_email = os.environ.get('SENDER_EMAIL')
    
    def send_email(self, to_email: str, subject: str, html_content: str):
        try:
            import requests
            
            if not self.api_key or not self.domain or not self.sender_email:
                print(f"❌ Missing Mailgun configuration")
                return False
            
            url = f"https://api.mailgun.net/v3/{self.domain}/messages"
            
            data = {
                "from": f"Celestia Astrology <{self.sender_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
            
            response = requests.post(
                url,
                auth=("api", self.api_key),
                data=data
            )
            
            if response.status_code == 200:
                print(f"✅ Mailgun EMAIL SENT TO: {to_email}")
                return True
            else:
                print(f"❌ Mailgun failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Mailgun email failed: {str(e)}")
            return False

# Email provider factory
def get_email_provider():
    """Get the configured email provider"""
    provider_name = os.environ.get('EMAIL_PROVIDER', 'sendgrid').lower()
    
    providers = {
        'sendgrid': SendGridProvider,
        'brevo': BrevoProvider,
        'gmail': GmailSMTPProvider,
        'mailgun': MailgunProvider
    }
    
    provider_class = providers.get(provider_name, SendGridProvider)
    print(f"📧 Using email provider: {provider_name.upper()}")
    return provider_class()

def send_email(to_email: str, subject: str, html_content: str):
    """Send email using the configured provider"""
    provider = get_email_provider()
    return provider.send_email(to_email, subject, html_content)