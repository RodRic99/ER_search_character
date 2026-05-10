# Vercel Deployment Guide

This frontend is designed to be deployed from the `ER_front2` directory.

## Recommended Vercel settings

- Framework Preset: `Next.js`
- Root Directory: `ER_front2`
- Install Command: `npm install`
- Build Command: `npm run build`

## Required environment variable

- `BACKEND_PROXY_TARGET`

Example:

```env
BACKEND_PROXY_TARGET=http://52.78.209.177:8080
```

## Notes

- The app falls back to `http://localhost:8080` only for local development.
- Production deploys use same-origin `/api` requests and Vercel rewrites them to `BACKEND_PROXY_TARGET`.
- After changing `BACKEND_PROXY_TARGET`, trigger a redeploy so the rewrite target is updated.
