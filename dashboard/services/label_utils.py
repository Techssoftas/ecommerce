# utils/label_utils.py
import qrcode
import base64
from io import BytesIO
from PIL import Image
import barcode
from barcode.writer import ImageWriter
import logging

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

def generate_code128_datauri(text, writer_options=None):
    # python-barcode Code128 -> PNG via ImageWriter
    writer_options = writer_options or {"module_height": 15.0, "module_width": 0.45, "font_size": 14, "text_distance": 1}
    CODE128 = barcode.get_barcode_class('code128')
    buf = BytesIO()
    try:
        CODE128(text, writer=ImageWriter()).write(buf, options=writer_options)
        return image_bytes_to_datauri(buf.getvalue(), mime="image/png")
    except Exception as e:
        logger.exception("Barcode generation failed: %s", e)
        return ""
