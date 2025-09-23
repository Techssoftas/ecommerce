import base64
import requests
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.conf import settings
class Command(BaseCommand):
    def __init__(self):
        self.token = settings.DELHIVERY_TOKEN

    help = "Download Delhivery shipping label, overlay Size/Color and save"

    def add_arguments(self, parser):
        parser.add_argument("--waybill", type=str, required=True, help="Waybill number")
        parser.add_argument("--size", type=str, required=True, help="Product size")
        parser.add_argument("--color", type=str, required=True, help="Product color")

    def handle(self, *args, **options):
        waybill = options["waybill"]
        size = options["size"]
        color = options["color"]

        # 🔹 Step 1: Request label from Delhivery API
        API_URL = "https://ltl-clients-api.delhivery.com/label/get_urls/<size>/<lrn>"  # Update endpoint
        # url = "https://ltl-clients-api-dev.delhivery.com/label/get_urls/std/220041149"

        headers = {
            'Authorization': f'Token {self.token}',
            "Content-Type": "application/json",
        }
        data = {"waybill": waybill, "pdf": "N", "png": "Y"}  # or "pdf": "Y" if PDF needed

        # self.stdout.write(self.style.NOTICE(f"Fetching label for {waybill}..."))
        response = requests.post(API_URL, headers=headers, json=data)
        print("Response Status Code:", response)
        if response.status_code != 200:
            self.stderr.write(self.style.ERROR(f"Error: {response.text}"))
            return

        result = response.json()
        label_base64 = result.get("packages", [{}])[0].get("png")  # <-- adjust key if different
        if not label_base64:
            self.stderr.write(self.style.ERROR("Label not found in response"))
            return

        # 🔹 Step 2: Decode Base64 → Image
        label_bytes = base64.b64decode(label_base64)
        image = Image.open(BytesIO(label_bytes))

        # 🔹 Step 3: Overlay Size/Color
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()

        text = f"Size: {size} | Color: {color}"
        draw.text((50, 50), text, fill="black", font=font)

        # 🔹 Step 4: Save final label
        file_name = f"label_{waybill}.png"
        image.save(file_name)

        self.stdout.write(self.style.SUCCESS(f"✅ Label saved as {file_name}"))
