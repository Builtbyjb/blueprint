dev:
	python manage.py runserver

css:
	npx tailwindcss -i ./main/static/main/input.css -o ./main/static/main/style.css --watch

migrate:
	python manage.py makemigrations main && python manage.py migrate