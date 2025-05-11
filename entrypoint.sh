#!/bin/bash
# Ожидаем базу
/wait-for-it.sh db:5432 --timeout=30 --strict -- echo "PostgreSQL is up"
# Запускаем Django
python parser_marketplaces/manage.py migrate
python parser_marketplaces/manage.py runserver 0.0.0.0:8000
