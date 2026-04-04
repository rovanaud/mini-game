# mini-game

## Production deploy on Ubuntu 24.04 (AWS EC2)

This repo now includes Dockerized production services:
- `frontend` (Nginx + built Vue app)
- `backend` (Django + Channels via Daphne)
- `db` (PostgreSQL)
- `redis` (Channels backing store)

## Files added for deployment
- `docker-compose.yml`
- `backend/Dockerfile`
- `backend/entrypoint.sh`
- `backend/requirements.txt`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `.env.example`
- `.dockerignore`

## 1) Prepare EC2 host (Ubuntu 24.04)

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Log out and back in so Docker group permissions apply.

## 2) Pull project and configure environment

```bash
git clone <your-repo-url> mini-game
cd mini-game
cp .env.example .env
```

Edit `.env` and set at least:
- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_ALLOWED_HOSTS` (EC2 public IP / DNS / domain)
- `CSRF_TRUSTED_ORIGINS` (your public HTTP/HTTPS origins)

## 3) Start the stack

```bash
docker compose up -d --build
```

Then open:
- App: `http://<ec2-public-ip>/`
- Django admin: `http://<ec2-public-ip>/admin/`

## 4) Useful operations

```bash
# See container status

docker compose ps

# Stream logs

docker compose logs -f backend frontend

# Run Django management command

docker compose exec backend python manage.py createsuperuser

# Stop stack

docker compose down
```

## Notes
- Backend migrations and `collectstatic` run automatically at backend startup.
- WebSockets are proxied by Nginx at `/ws/*`.
- For HTTPS in production, place a TLS terminator (ALB, CloudFront, or reverse proxy like Caddy/Nginx) in front and set secure cookie / redirect flags accordingly.
