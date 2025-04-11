css:
	npx tailwindcss -i ./static/input.css -o ./static/style.css --watch

dev:
	uvicorn server:app --reload --host 127.0.0.1 --port 3000
