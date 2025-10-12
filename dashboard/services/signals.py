from django.db.models.signals import pre_save
from django.dispatch import receiver
from api.models import Order
from .email import send_order_mail  # adjust this path based on your project structure

@receiver(pre_save, sender=Order)
def order_delivered_mail(sender, instance, **kwargs):
    if instance.pk:  # existing order
        try:
            old_order = Order.objects.get(pk=instance.pk)
        except Order.DoesNotExist:
            return

        # 🔥 Only if status changes to Delivered
        if old_order.status != instance.status and instance.status == 'Delivered':
            send_order_mail(
                subject=f"Order #{instance.order_number} Delivered!",
                to_email=instance.email,
                template_name='emails/order_delivered.html',
                context={
                    'user': instance.user,
                    'order': instance
                }
            )
