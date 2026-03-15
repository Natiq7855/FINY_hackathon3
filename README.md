# PeerWeave

A community relationship engine that automatically creates peer-to-peer connections, prevents member isolation, and helps communities grow through smart matchmaking and AI-powered insights.

Built with Django 5, Bootstrap 5, and Google Gemini AI.

---

## Features

### Peer Matchmaking
Automatically connect members based on shared skills, interests, and timezone compatibility.

**Matching score formula:**
```
score = shared_interests × 2 + shared_skills × 1 + timezone_match × 1
```

### Buddy Onboarding
Every new member gets a buddy automatically assigned via Django signals when they join a community. No one joins alone.

### Community Chat (Discord-style)
Real-time community chat with a dark-themed Discord-like interface. Two channels per community:
- **#general** — everyday conversation
- **#help** — peer support and Q&A

Uses JavaScript polling (2.5s interval) for message updates.

### AI-Powered Insights (Google Gemini)
- **Member Analysis** — detects likely challenges each member faces and recommends the best peer to help
- **Match Explanation** — explains why two members are a good match with collaboration ideas and ice-breaker questions
- **Community Health Insights** — interprets the health score and suggests prioritized action plans

### Relationship Network Graph
Interactive vis-network visualization showing all connections in a community. Spot isolated members at a glance.

### Community Health Score
Real-time health metric for every community:
```
score = 0.3 × activity + 0.3 × connections + 0.2 × helpSolved − 0.2 × isolationPenalty
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Django 5.x |
| Database | SQLite |
| Frontend | Bootstrap 5, Vanilla JS, vis-network |
| AI | Google Gemini 2.0 Flash |
| Auth | Django built-in auth |

---

## Project Structure

```
peerweave/         — Django project settings, URLs, WSGI/ASGI, mixins
accounts/          — Profile model, signup/login/profile/dashboard views, signals
communities/       — Community + Membership models, health score service, seed command
matchmaking/       — Match, BuddyAssignment, Connection, Interaction models + service
helpboard/         — HelpRequest, HelpResponse models + expert matching
network/           — Graph JSON endpoint + vis-network visualization page
chat/              — Community chat rooms (Message model, polling-based)
ai/                — Gemini AI integration (member analysis, match explain, insights)
templates/         — base.html + per-app templates
static/            — Static assets
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Natiq7855/FINY_hackathon3.git
cd FINY_hackathon3

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed demo data (6 users + 1 community + sample messages)
python manage.py seed_demo

# Start the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin1234 | Superuser (access /admin/) |
| alice | demo1234 | python, django, data science |
| bob | demo1234 | react, js, design |
| carol | demo1234 | marketing, content, seo |
| dave | demo1234 | python, ml, data science |
| eve | demo1234 | design, figma, ux |

---

## Key Pages

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/dashboard/` | User dashboard with health scores and recent matches |
| `/communities/` | Browse and join communities |
| `/communities/<id>/` | Community detail with members and health score |
| `/match/` | Peer matchmaking page |
| `/chat/<id>/general/` | Community chat (#general channel) |
| `/chat/<id>/help/` | Community chat (#help channel) |
| `/ai/insights/<id>/` | AI-powered community insights |
| `/network/` | Relationship graph visualization |
| `/admin/` | Django admin panel |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/<id>/<channel>/messages/` | GET | Fetch new messages (polling) |
| `/chat/<id>/<channel>/send/` | POST | Send a chat message |
| `/ai/match-explain/?peer_id=<id>` | GET | AI match explanation (JSON) |
| `/network/data/<id>/` | GET | Graph data for vis-network (JSON) |

---

## Configuration

### Gemini AI

The API key is configured in `peerweave/settings.py`:

## License

This project was built for a hackathon.
