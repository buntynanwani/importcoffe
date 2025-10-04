#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Backend/code')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print('Superusers:')
for u in User.objects.filter(is_superuser=True).values('username','email'):
    print(u)
