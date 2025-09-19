# api/services/delhivery_service.py
import json
import requests
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

# PDF generation (reportlab)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128

from api.models import Order, OrderItem, OrderTracking  # models from your uploaded file

# helper: build payload from your Order
def build_delhivery_payload(order: Order):
    sa = order.shipping_address  # ShippingAddress model fields exist. :contentReference[oaicite:7]{index=7}
    products = []
    for item in order.items.all():  # OrderItem model. :contentReference[oaicite:8]{index=8}
        prod = item.product
        products.append({
            "name": prod.name,
            "sku": prod.sku,
            "hsn_code": prod.hsn_code or "",
            "quantity": int(item.quantity),
            "price": str(item.price),
        })

    payload = {
        # minimum useful keys - adjust per Delhivery docs if you need extra keys
        "pickup_location": settings.DELHIVERY_PICKUP_LOCATION,
        "order_id": str(order.order_number),
        "order_date": order.created_at.strftime("%d-%m-%Y %H:%M:%S") if order.created_at else "",
        "payment_mode": "Prepaid",  # or "COD" if your payment model says COD
        "total_amount": str(order.total_amount or "0.00"),
        "seller_gst_tin": getattr(settings, "DELHIVERY_SELLER_GST_TIN", ""),
        "client_gst_tin": getattr(settings, "DELHIVERY_CLIENT_GST_TIN", ""),
        "invoice_reference": f"INV-{order.order_number}",
        "consignee": {
            "name": sa.contact_person_name or order.user.username,
            "phone": sa.phone or order.phone,
            "add": (sa.address_line1 or "") + " " + (sa.address_line2 or ""),
            "city": sa.city or "",
            "state": sa.state or "",
            "pin": sa.postal_code or "",
            "country": sa.country or "India"
        },
        "products": products
    }
    return payload

# helper: robust AWB extractor (Delhivery response varies)
def extract_awb(resp_json):
    # try common places
    if not resp_json:
        return None
    # flat
    for k in ("waybill", "awb", "awb_number", "awb_no"):
        if k in resp_json:
            return resp_json[k]
    # nested lists/dicts
    if isinstance(resp_json, dict):
        # often result is in ['packages'] or ['result']
        for key in ("packages", "result", "data"):
            v = resp_json.get(key)
            if isinstance(v, list) and v:
                first = v[0]
                for k in ("waybill","awb","awb_number"):
                    if isinstance(first, dict) and k in first:
                        return first[k]
    # fallback None
    return None

# generate simple PDF label/invoice using reportlab (contains AWB barcode + full invoice lines)
def generate_label_pdf_bytes(order: Order, awb: str) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, h - 40, f"Shipping Label / Invoice - Order {order.order_number}")
    c.setFont("Helvetica", 10)
    c.drawString(30, h - 58, f"AWB : {awb}")

    # Barcode (Code128)
    try:
        barcode = code128.Code128(awb, barHeight=20*mm, barWidth=0.5)
        barcode.drawOn(c, 30, h - 120)
    except Exception:
        # ignore barcode errors; continue
        pass

    # Addresses
    sa = order.shipping_address
    y = h - 150
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30, y, "Ship To:")
    c.setFont("Helvetica", 10)
    y -= 14
    c.drawString(35, y, f"{sa.contact_person_name or order.user.username}")
    y -= 12
    addr_lines = []
    if sa.address_line1: addr_lines.append(sa.address_line1)
    if sa.address_line2: addr_lines.append(sa.address_line2)
    if sa.city: addr_lines.append(f"{sa.city} - {sa.postal_code or ''}")
    if sa.state: addr_lines.append(sa.state)
    for ln in addr_lines:
        c.drawString(35, y, ln)
        y -= 12
    c.drawString(35, y, f"Phone: {sa.phone or order.phone}")
    y -= 20

    # Simple items table
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y, "Items (name | HSN | Qty | Price)")
    y -= 14
    c.setFont("Helvetica", 9)
    for item in order.items.all():
        prod = item.product
        line = f"{prod.name[:40]} | {prod.hsn_code or '-'} | {item.quantity} | {item.price}"
        c.drawString(35, y, line)
        y -= 12
        if y < 60:
            c.showPage()
            y = h - 60

    # Totals & invoice ref
    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y, f"Total: ₹{order.total_amount}")
    y -= 14
    c.setFont("Helvetica", 9)
    c.drawString(30, y, f"Invoice Ref: INV-{order.order_number}")

    # Finish
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# main: create order in Delhivery and attach label PDF locally to OrderTracking
def create_delhivery_order_and_get_label(order_id, use_staging=False):
    order = Order.objects.get(pk=order_id)  # Order fields in your models. :contentReference[oaicite:9]{index=9}
    payload = build_delhivery_payload(order)

    url = settings.DELHIVERY_STAGING_URL if use_staging else settings.DELHIVERY_PROD_URL

    # Delhivery requires "format=json&data=" wrapper
    body = "format=json&data=" + json.dumps(payload)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # token can be passed as query param or in headers depending on account
    params = {}
    if getattr(settings, "DELHIVERY_TOKEN", None):
        params["token"] = settings.DELHIVERY_TOKEN
        headers["Authorization"] = settings.DELHIVERY_TOKEN  # harmless if ignored

    resp = requests.post(url, data=body, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    resp_json = resp.json()

    # Save raw response
    awb = extract_awb(resp_json)
    # If Delhivery returned no AWB immediately, you may still get it later — handle that in tracking jobs.
    if not awb:
        # try look inside nested response keys quickly
        awb = extract_awb(resp_json.get("result") if isinstance(resp_json, dict) else None)

    # create/update OrderTracking
    if awb:
        tracking, created = OrderTracking.objects.get_or_create(order=order, defaults={"awb_number": awb, "raw_data": resp_json})
        if not created:
            tracking.awb_number = awb
            tracking.raw_data = resp_json
            tracking.save()
    else:
        # still create placeholder tracking with unique id if you want (optional)
        tracking, _ = OrderTracking.objects.get_or_create(order=order, defaults={"awb_number": f"TMP-{order.order_number}", "raw_data": resp_json})

    # Try to fetch Delhivery packing_slip JSON (optional) - documented endpoint:
    # GET https://staging-express.delhivery.com/api/p/packing_slip?wbns=XXXXXXXX
    # Note: packing_slip returns JSON only (you need to render PDF yourself). :contentReference[oaicite:10]{index=10}
    try:
        if awb:
            base = "https://staging-express.delhivery.com" if use_staging else "https://track.delhivery.com"
            packing_url = base + "/api/p/packing_slip"
            p_params = {"wbns": awb}
            if getattr(settings, "DELHIVERY_TOKEN", None):
                p_params["token"] = settings.DELHIVERY_TOKEN
            pack_resp = requests.get(packing_url, params=p_params, timeout=15)
            # packing API returns JSON describing packing layout; but many clients just create own PDF
            # we'll ignore pack_resp for now and create our own label pdf
    except Exception:
        pass

    # Generate label PDF (reportlab) with AWB, addresses, items, HSN etc
    pdf_bytes = generate_label_pdf_bytes(order, awb or f"TMP-{order.order_number}")
    filename = f"label_{order.order_number}_{awb or 'TMP'}.pdf"
    tracking.label_file.save(filename, ContentFile(pdf_bytes), save=True)

    return {"awb": awb, "tracking_id": tracking.id, "label_file_url": tracking.label_file.url}
