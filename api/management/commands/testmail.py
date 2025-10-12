import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException

# Create logger
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send test mail to check SMTP config'

    def handle(self, *args, **kwargs):
        subject = 'Test Email from Django'
        message = 'This is a test email sent via Django management command.'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = 'suriyathaagam@gmail.com'  # Replace with your real email

        logger.info("📤 Attempting to send test email to %s", to_email)

        try:
            sent = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )
            if sent:
                self.stdout.write(self.style.SUCCESS('✅ Email sent successfully to ' + to_email))
                logger.info("✅ Email sent successfully to %s", to_email)
            else:
                self.stdout.write(self.style.ERROR('❌ Email failed to send'))
                logger.error("❌ Email failed to send to %s", to_email)
        except SMTPException as e:
            self.stdout.write(self.style.ERROR(f'❌ SMTP Exception: {e}'))
            logger.exception("❌ SMTPException while sending email to %s", to_email)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            logger.exception("❌ Unexpected exception while sending email to %s", to_email)
