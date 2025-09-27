from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException

class Command(BaseCommand):
    help = 'Send test mail to check SMTP config'

    def handle(self, *args, **kwargs):
        subject = 'Test Email from Django'
        message = 'This is a test email sent via Django management command.'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = 'suriyathaagam@gmail.com'  # 🔁 Replace with your real email

        try:
            sent = send_mail(
                subject='Test Email from Django',
                message='Hello, this is a test.',
                from_email='fashion@mtex.in',
                recipient_list=['suriyathaagam@gmail.com'],
                fail_silently=False,
            )
            if sent:
                self.stdout.write(self.style.SUCCESS('✅ Email sent successfully to ' + to_email))
            else:
                self.stdout.write(self.style.ERROR('❌ Email failed to send'))
        except SMTPException as e:
            self.stdout.write(self.style.ERROR(f'❌ SMTP Exception: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
