from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
import os

from api.models import Order  # Adjust as per your model
from weasyprint import HTML
from dashboard.services.label_utils import generate_qr_datauri, generate_code128_datauri

class Command(BaseCommand):
    help = "Generate label/invoice PDF for given order ID"

    def add_arguments(self, parser):
        parser.add_argument('--order-id', type=int, required=True)

    def handle(self, *args, **kwargs):
        order_id = kwargs['order_id']

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            self.stderr.write(f"❌ No order found with ID {order_id}")
            return
        try:
            is_cod = order.payment.payment_method == 'Cash on Delivery'
        except Order.DoesNotExist:
            is_cod = False
       
        
        context = {
            "name": 'Suriya',
            "addr_line1": 'No 123, Some Street',
            "addr_line2": 'Some Area',
            "city": 'Some City',
            "state": 'Some State',
            "postal": '123456',
            "awb": 'AWB123456789',
            "barcode_datauri":generate_code128_datauri('BGIUI788'),  # assume these methods exist
            "qr_datauri": generate_qr_datauri('AWB123456789'),
            "order_items": order,
            "order_no": order.order_number,
            "invoice_no": 'INV' + str(order.order_number).zfill(6),
            "order_number": order.order_number,
            "order_date": order.created_at.strftime("%d-%m-%Y"),
            "cod_charge": {
                            "description": "Cash on Delivery Charge",
                            "hsn_code": "6211",
                            "qty": "N/A",
                            "discount": 0,
                            "taxable_value": 85.5,
                            "gst_rate": 5,
                            "gst_amount": 4.5,
                            "total": 90.0,
                        } if is_cod else None,
        }

        html = render_to_string("labels/shipping_label.html", context)

        output_dir = os.path.join(settings.BASE_DIR, "generated_labels")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"label_order_{order_id}.pdf")

        HTML(string=html).write_pdf(output_file)

        self.stdout.write(self.style.SUCCESS(f"✅ PDF generated: {output_file}"))
