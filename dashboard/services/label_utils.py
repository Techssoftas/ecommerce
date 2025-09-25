# utils/label_utils.py
import qrcode
import base64
from io import BytesIO
from PIL import Image
import barcode
from barcode.writer import ImageWriter
import logging
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPM
from reportlab.graphics.barcode import createBarcodeDrawing
logger = logging.getLogger(__name__)

def image_bytes_to_datauri(img_bytes, mime="image/png"):
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def generate_qr_datauri(text, box_size=6, border=2):
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return image_bytes_to_datauri(buf.getvalue())


import io
def generate_code128_datauri(text):
    try:
        buffer = io.BytesIO()

        # Get the Code128 class
        code128 = barcode.get_barcode_class('code128')

        # Create barcode object
        code = code128(text, writer=ImageWriter())

        # Write PNG to buffer
        code.write(buffer, {'write_text': False})  # 👈 disable text below barcode

        # Get PNG bytes
        img_bytes = buffer.getvalue()

        return image_bytes_to_datauri(img_bytes, mime="image/png")
    except Exception as e:
        print(f"Barcode generation failed for {text}: {e}")
        return ""

