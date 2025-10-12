from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_order_mail(subject, to_email, template_name, context):
    message = render_to_string(template_name, context)
    sent_count = send_mail(
    subject=subject,
    message='',  # plain text version not needed
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[to_email],
    html_message=message,
    fail_silently=False  # IMPORTANT: Let errors raise if any
    )

    if sent_count:
        print("✅ Mail sent successfully")
    else:
        print("❌ Mail not sent")
   
