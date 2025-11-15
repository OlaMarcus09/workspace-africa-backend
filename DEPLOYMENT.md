# Backend Deployment

## Environment Variables Required:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL database URL
- `ALLOWED_HOSTS`: Allowed hostnames
- `DEBUG`: Debug mode (False in production)

## Deployment Steps:
1. Connect GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy automatically on git push
4. Run migrations on deployment

## API Health Check:
- `GET /health/` - Basic health check
- `GET /api/team/dashboard/` - Team admin endpoint test
