from django.core.management.base import BaseCommand
from dashboard.services.label_utils import generate_qr_datauri
import base64

class Command(BaseCommand):
    help = 'Generate a QR code and save it as a PNG file'

    def handle(self, *args, **kwargs):
        try:
            # Sample text to encode
            value = "https://example.com"

            # Generate data URI
            data_uri = generate_qr_datauri(value)

            # Decode base64 data
            header, encoded = data_uri.split(",", 1)
            img_bytes = base64.b64decode(encoded)

            # Save to file
            file_name = "sample_qr.png"
            with open(file_name, "wb") as f:
                f.write(img_bytes)

            self.stdout.write(self.style.SUCCESS(f"✅ QR code saved to {file_name}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to generate QR code: {e}"))
