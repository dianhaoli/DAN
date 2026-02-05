# Environment Variables Setup

## Required Environment Variable

Add this to your `web/.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

This tells the web app where to find the FastAPI backend.

## Default Behavior

If `NEXT_PUBLIC_API_URL` is not set, the app defaults to `http://localhost:8000/api`.

## For Production

When deploying, set this environment variable to your production FastAPI URL:
- Render: `https://your-app.onrender.com/api`
- Railway: `https://your-app.railway.app/api`
- Custom domain: `https://api.yourdomain.com/api`
