include .env

all:
	docker compose up --build

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps -a

create:
	docker compose create --build

rmi:
	docker rmi ${DB_CONTAINER_NAME}
#docker rmi ${DJ_CONTAINER_NAME}

rm:
	docker rm ${DB_CONTAINER_NAME}

logs:
	docker compose logs -t

re:
	make down
	make create
	make up

reall:
	docker rm -f $(shell docker ps -qa)
	docker rmi $(shell docker images -qa)
	docker volume rm $(shell docker volume ls -q)
	docker network prune -f
	make create
	make up

#LONG METHOD THAT JUST ENSURES NO PREVIOUS DATA CAN MODIFY THE OUTCOME
just_in_case:
	docker rm -f $(shell docker ps -qa)
	docker rmi $(shell docker images -qa)
	docker volume rm $(shell docker volume ls -q)
	docker system prune -a -f
	docker network prune -f
	rm -rf history/code/history/migrations/
	rm -rf TwoFactorAuth/code/TwoFactorAuth/migrations/
	rm -rf UserMng/code/UserMng/migrations

.PHONY: up down ps create rmi rm logs re reall just_in_case

# Convenience targets to inspect sqlite DB
db-shell:
	docker run --rm -v "$(PWD)/Backend:/Backend" --workdir /Backend importcoffe-backend:latest /bin/bash -lc "sqlite3 /Backend/code/db.sqlite3"

db-tables:
	docker run --rm -v "$(PWD)/Backend:/Backend" --workdir /Backend importcoffe-backend:latest /bin/bash -lc "sqlite3 /Backend/code/db.sqlite3 '.tables'"

# Open the sqlite DB in the host GUI (cross-platform via Python)
open-db:
	python - <<PY
import os,sys,subprocess
p = os.path.abspath('Backend/code/db.sqlite3')
if not os.path.exists(p):
	print('DB not found:', p); sys.exit(1)
if os.name == 'nt':
	# Windows
	try:
		os.startfile(p)
	except Exception:
		subprocess.run(['powershell','-Command',"Start-Process -FilePath '%s'"%p])
elif sys.platform == 'darwin':
	subprocess.run(['open', p])
else:
	subprocess.run(['xdg-open', p])
PY

# PowerShell helper: run sqlite3 from PowerShell if installed, otherwise use docker-run fallback
ps-sqlite:
	powershell -NoProfile -Command "if (Get-Command sqlite3 -ErrorAction SilentlyContinue) { sqlite3 'Backend\\code\\db.sqlite3' } else { docker run --rm -v \"${PWD}/Backend:/Backend\" --workdir /Backend importcoffe-backend:latest /bin/bash -lc \"sqlite3 /Backend/code/db.sqlite3\" }"