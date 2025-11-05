# Sovereign Access Platform

A Django-based membership and wallet management system featuring mnemonic recovery, Telegram/Jabber notifications, crypto wallet integration, support ticketing, and administrative tooling.

## Features

- Custom user model without email requirement, BIP39-style mnemonic recovery, Telegram/Jabber-only notifications.
- Membership groups, tiered plans, upgrade pricing rules, wallet-based payments in BTC, XMR, USDT (self-hosted nodes).
- Internal wallet ledger with deposit address generation, withdrawal requests, Celery-based node polling.
- Notification templates, per-user channel preferences, delivery logs.
- Support ticket portal with staff queue, message threads, attachments.
- News/notice publishing targeted by membership group with scheduling controls.
- Admin console to manage currencies, nodes, memberships, notifications; infrastructure dashboard for service health and backups.
- Analytics dashboard summarizing memberships, wallet flow, support status.

## Requirements

- Python 3.12+
- PostgreSQL 15+
- Redis for caching and Celery broker
- Node endpoints for BTC, Monero, and USDT (TRC20) when enabling live integrations

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/dev.txt

cp .env.example .env
# adjust DATABASE_URL, CACHE_URL, BROKER_URL, TELEGRAM_BOT_TOKEN, etc.

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Celery worker and beat:

```bash
celery -A config worker -l info
celery -A config beat -l info
```

## Tests

```bash
pytest
```

## Deployment

- Configure Gunicorn + Nginx (see `Dockerfile` / `docker-compose.yml` when added).
- Run database migrations (`python manage.py migrate`) and collect static assets (`python manage.py collectstatic`).
- Ensure Celery worker/beat processes are supervised (systemd or similar).

## Pending Integrations

- Connect real node clients for BTC/XMR/USDT in `wallets.services`.
- Implement Telegram bot webhook (current dispatch assumes resolved `telegram_chat_id`).
- Provide theme assets once design finalized.
