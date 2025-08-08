VENV=.venv

run:
	python manage.py runserver

m:
	python manage.py migrate

mm:
	python manage.py makemigrations

shell:
	python manage.py shell

createsuperuser:
	python manage.py createsuperuser

test:
	python manage.py test

req:
	pip install -r requirements.txt

