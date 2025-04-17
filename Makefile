css:
	npx @tailwindcss/cli -i ./static/input.css -o ./static/style.css --watch

dev:
	uvicorn main:app --reload --host 127.0.0.1 --port 3000

ngrok:
	ngrok http --url=admittedly-adequate-scorpion.ngrok-free.app 3000

env:
	export UV_PROJECT_ENVIRONMENT=~/documents/.mytaskie
