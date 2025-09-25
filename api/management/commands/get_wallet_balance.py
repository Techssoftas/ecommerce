import requests
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fetch wallet balance from Delhivery API'

    
    def handle(self, *args, **options):
        api_token = 'd7c1fdb1b8ca98d9fd3fc884a771fd4e96ffaf1e'  # Replace with your actual token or use options['token']
        
        
        url = "https://ucp.delhivery.com/developer-portal/wallet/balance"
        headers = {"Authorization": f"Bearer {api_token}"}




        try:
            response = requests.get(url, headers=headers)
            print(response.status_code)
            print(response.text)

            
            
        except requests.RequestException as e:
            print(f"Error fetching wallet balance: {e}")
