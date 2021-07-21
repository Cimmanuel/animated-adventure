# Realtime chat app using Docker, Django, DRF and Channels

## Usage
- Clone the repository 
```
git clone https://github.com/Cimmanuel/animated-adventure
```
- Navigate into the just downloaded folder
```
cd animated-adventure/
```
- Create a .env file from the existing .env.example
```
mv .env.example .env
```
- Build and start docker containers
```
docker-compose up -d --build
```
- Check the ID of the container named **api**
```
docker ps -a
```
- Attach a shell to the container. Be sure to replace <CONTAINER_ID> with the actual ID of the **api** container
```
docker exec -it <CONTAINER_ID> bash
```
- Create superuser. Follow the prompt till creation is successful
```
python manage.py createsuperuser
```
- Login to the admin site
```
http://127.0.0.1:8000/admin/
```
- Open a tab in your browser and visit the docs page (generated by Swagger) - this way you have access to the available endpoints
```
http://127.0.0.1:8000/docs/
```
- After registering, logging in, creating rooms and adding members, you can then visit the chat page. Make sure you replace <CHATROOM_ID> with an
ID of a room you created or are a member of.
```
http://127.0.0.1:8000/chat/chatroom/<CHATROOM_ID>/
```