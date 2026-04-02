import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen.settings')
django.setup()
from django.test import Client
c = Client()
c.login(username='admin', password='admin123')
res = c.get('/dashboard/')
print("STATUS CODE:", res.status_code)
if res.status_code == 500:
    import traceback
    print("Content:", res.content.decode()[:1000])
