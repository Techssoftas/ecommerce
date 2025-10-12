# services/delhivery_service.py
import requests
import json
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from api.models import Order, OrderTracking,Payment
from urllib.parse import urlencode


from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.core.files.base import ContentFile
from .label_utils import generate_qr_datauri, generate_code128_datauri
import datetime


logger = logging.getLogger(__name__)
class DelhiveryService:
    
    def __init__(self):
        self.token = settings.DELHIVERY_TOKEN
        self.base_url = "https://track.delhivery.com/api/cmu/create.json" # production URL  
        # self.base_url = "https://staging-express.delhivery.com/api/cmu/create.json" # staging URL  
        self.pickup_location = settings.DELHIVERY_PICKUP_LOCATION
        self.company_name = settings.DELHIVERY_COMPANY_NAME
        self.gst_tin = settings.DELHIVERY_SELLER_GST_TIN

        
    def create_shipment(self, order_id):
        try:
            order = Order.objects.get(id=order_id)

            # ---  payment method from Payment model ---
            try:
                is_cod = order.payment.payment_method == 'Cash on Delivery'
            except Payment.DoesNotExist:
                is_cod = False

            payment_mode_value = "COD" if is_cod else "Prepaid"
            cod_amount_value = str(order.total_amount) if is_cod else "0"


            # Calculate total weight & quantity
            total_weight = 0
            total_quantity = 0
            for item in order.items.all():
                weight = float(item.product.weight or 0.5)
                total_weight += weight * item.quantity
                total_quantity += item.quantity

            # Enforce minimum weight
            if total_weight < 0.5:
                total_weight = 0.5

            # Get dimensions (using first product or defaults)
            first_item = order.items.first()
            dimensions = {
                'length': float(27),
                'width': float(250),
                'height': float(1)
            }

            

            # Prepare shipment data
            shipment_data = {
                'shipments': [{
                    'name': order.shipping_address.contact_person_name or order.user.username,
                    'add': f"{order.shipping_address.address_line1}, {order.shipping_address.address_line2 or ''}".strip(', '),
                    'pin': order.shipping_address.postal_code,
                    'city': order.shipping_address.city,
                    'state': order.shipping_address.state,
                    'country': order.shipping_address.country or 'India',
                    'phone': order.shipping_address.contact_person_number or order.shipping_address.phone or order.phone,
                    'order': str(order.order_number),
                    'payment_mode': payment_mode_value,  # Change if COD
                    'cod_amount': cod_amount_value,
                    'return_pin': '641606',
                    'return_city': 'Tiruppur',
                    'return_phone': '9876543210',
                    'return_add': self.pickup_location,
                    'return_state': 'Tamil Nadu',
                    'return_country': 'India',
                    'products_desc': 'Clothing Items',
                    'hsn_code': first_item.product.hsn_code or '6109',
                    'order_date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_amount': str(order.total_amount),
                    'seller_add': self.pickup_location,
                    'seller_name': self.company_name,
                    'seller_cst': self.gst_tin,
                    'quantity': total_quantity,
                    'waybill': '',
                    'shipment_width': dimensions['width'],
                    'shipment_height': dimensions['height'],
                    'shipment_length': dimensions['length'],
                    'weight':  0.5,
                    'seller_gst_tin': self.gst_tin,
                    'shipping_mode': 'Surface',
                    'address_type': f"{order.shipping_address.type_of_address}",
                }],
                "pickup_location": {
                    "name": "M TEX"
                }
            }

            # API request payload
            payload = {
                'format': 'json',
                'data': json.dumps(shipment_data)
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Token {self.token}'
            }

            logger.info(f"Creating Delhivery shipment for order {order.order_number}")
            logger.info(f"Payload: {payload}")

            response = requests.post(
                self.base_url,
                headers=headers,
                data=payload,
                timeout=30
            )

            logger.info(f"Delhivery API response status: {response.status_code}")
            logger.info(f"Delhivery API response: {response.text}")

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    packages = result.get('packages', [])
                    if packages:
                        waybill = packages[0].get('waybill')

                        order.status = 'Ready to Ship'
                        order.save()
                        # Track the shipment
                        tracking, created = OrderTracking.objects.get_or_create(
                            order=order,
                            defaults={
                                'awb_number': waybill,
                                'current_status': 'Shipment Created',
                                'raw_data': result
                            }
                        )

                        if not created:
                            tracking.awb_number = waybill
                            tracking.current_status = 'Shipment Created'
                            tracking.raw_data = result
                            tracking.save()

                        logger.info(f"Shipment created successfully. Waybill: {waybill}")

                        # Generate label
                        label_success = render_label_html_and_save(tracking)

                        return {
                            'success': True,
                            'waybill': waybill,
                            'tracking_id': tracking.id,
                            'label_generated': label_success,
                            'message': 'Shipment created successfully'
                        }

                    else:
                        return {
                            'success': False,
                            'error': 'No packages found in Delhivery response',
                            'response': result
                        }
                else:
                    return {
                        'success': False,
                        'error': result.get('rmk', 'Unknown error from Delhivery'),
                        'response': result
                    }

            else:
                return {
                    'success': False,
                    'error': f'Delhivery API call failed ({response.status_code}): {response.text}'
                }

        except Order.DoesNotExist:
            return {'success': False, 'error': 'Order not found'}

        except Exception as e:
            logger.error(f"Exception in create_shipment: {str(e)}")
            return {'success': False, 'error': str(e)}

    
  
    def generate_shipping_label(self, tracking):
        """Generate and download shipping label PDF"""
        try:
            # Use GET method with wbns parameter as per documentation
            label_url = f"https://track.delhivery.com/api/p/packing_slip?wbns={tracking.awb_number}&pdf=flase&pdf_size=4R"
            # label_url = f"https://staging-express.delhivery.com/api/p/packing_slip?wbns={tracking.awb_number}&pdf=flase&pdf_size=4R"
            
            headers = {
                'Authorization': f'Token {self.token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Generating label for waybill: {tracking.awb_number}")
            logger.info(f"Label URL: {label_url}")
            
            response = requests.get(label_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Save PDF file
                file_name = f"shipping_label_{tracking.awb_number}.pdf"
                
                # Create ContentFile from PDF data
                pdf_file = ContentFile(response.content, name=file_name)
                
                # Save to model
                tracking.label_file = pdf_file
                tracking.save()
                
                logger.info(f"Shipping label generated successfully for {tracking.awb_number}")
                return True
            else:
                logger.error(f"Failed to generate label. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating shipping label: {str(e)}")
            return False
    
    def track_shipment(self, waybill):
        """Track shipment status"""
        try:
            track_url = f"https://track.delhivery.com/api/v1/packages/json/?waybill={waybill}"
            
            headers = {
                'Authorization': f'Token {self.token}'
            }
            
            response = requests.get(track_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Tracking failed. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error tracking shipment: {str(e)}")
            return None



 # print("order_items",order_items)
        # for it in order_items.items.all():
        #     print("it",it)
        # Prepare items list
        # items = []
        # for it in order_items.items.all():
        #     sku = it.product.sku or it.product.name
        #     size = it.size_variant.size or 'XL'
        #     color = it.variant.color_name or 'black'
        #     items.append({
        #         "sku": sku,
        #         "size": size,
        #         "qty": it.quantity,
        #         "color": color
        #     })
        # print("items",items)
def render_label_html_and_save(tracking):
    """
    Renders HTML template for label, generates barcode/qr images,
    converts to PDF (WeasyPrint), and saves to tracking.label_file.
    """
    try:
        order = tracking.order

        order_items = Order.objects.get(id=order.id)
        try:
            is_cod = order.payment.payment_method == 'Cash on Delivery'
        except Payment.DoesNotExist:
            is_cod = False
       
        awb = str(tracking.awb_number or order.order_number)
        order_no = str(order.order_number)

        # generate images as datauris
        qr_datauri = generate_qr_datauri(awb)
        barcode_datauri = generate_code128_datauri(order_no)

        context = {
            "name": order.shipping_address.contact_person_name or order.user.username,
            "addr_line1": order.shipping_address.address_line1 or "",
            "addr_line2": order.shipping_address.address_line2 or "",
            "city": order.shipping_address.city or "",
            "state": order.shipping_address.state or "",
            "postal": order.shipping_address.postal_code or "",
            "awb": awb,
            "order_no": order_no,
            # "items": items,
            "order_items": order_items,
            "qr_datauri": qr_datauri,
            "barcode_datauri": barcode_datauri,
            "order_date": order.created_at.strftime("%Y-%m-%d"),
            "invoice_no": f"INV-{order_no}",
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

        html_string = render_to_string("labels/shipping_label.html", context)

        # convert to PDF with WeasyPrint
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 10mm }')])

        # save to model
        file_name = f"shipping_label_{awb}.pdf"
        tracking.label_file.save(file_name, ContentFile(pdf_bytes))
        tracking.save()
        return True

    except Exception as e:
        logger.exception("Failed to render/save html->pdf label: %s", e)
        return False

