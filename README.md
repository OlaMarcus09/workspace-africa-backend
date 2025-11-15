# Workspace Africa Backend

Django REST API backend for Workspace Africa platform.

## Features

- **User Management**: Subscribers, Partners, Team Admins
- **Team Management**: Team creation, member invitations, subscription management
- **Space Management**: Partner spaces with check-in system
- **Subscription & Billing**: Plan management with Paystack integration
- **Authentication**: JWT-based authentication system

## API Endpoints

### Team Admin Endpoints
- `GET /api/team/dashboard/` - Team overview
- `GET /api/team/members/` - Team members management
- `GET /api/team/billing/` - Subscription and billing
- `POST /api/team/invites/` - Invite team members
- `POST /api/team/add-subscription/` - Add subscription to team

## Setup

1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver`

## Deployment

Deployed on Render at: `https://workspace-africa-backend.onrender.com`
