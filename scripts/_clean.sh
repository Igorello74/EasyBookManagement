#!/bin/bash
python manage.py flush --noinput &&\
echo ✅ Flushed database &&\
export DJANGO_SUPERUSER_PASSWORD="123" &&\
python manage.py createsuperuser --username admin --email admin@example.com --noinput > /dev/null &&\
echo ✅ Created superuser \"admin\" with password \"123\" &&\
rm -rf ./backups/ &&\
echo ✅ Removed backups directory