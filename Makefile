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