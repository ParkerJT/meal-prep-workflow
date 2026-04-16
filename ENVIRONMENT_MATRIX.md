# Environment Matrix

Reference matrix for local development, staging, and production environments.

## Deployment Flow

- Develop on `feature/*` branches locally.
- Merge to `staging` branch to deploy and validate in staging.
- Merge `staging` into `main` to deploy to production (approval gate recommended).

## Core Environment Matrix

| Item | Local Dev | Staging | Production |
|---|---|---|---|
| Git branch | `feature/*` | `staging` | `main` |
| GCP/Firebase project | none (uses staging resources) | `meal-prep-staging` | `meal-prep-production` |
| Firebase Auth/Firestore | staging | staging | production |
| Backend runtime | local FastAPI (`http://localhost:8000`) | Cloud Run (staging project) | Cloud Run (production project) |
| Frontend runtime | Next.js local (`http://localhost:3000`) | Firebase Hosting (staging) | Firebase Hosting (production) |
| Stripe mode | test | test | live |
| Deploy trigger | manual local | push to `staging` | push to `main` (approval recommended) |

## Backend Environment Variables

| Variable | Local | Staging | Production |
|---|---|---|---|
| `OPENAI_API_KEY` | local secret | Secret Manager | Secret Manager |
| `OPENAI_MODEL` | `gpt-4o-mini` (or chosen model) | same as local unless changed | same as staging unless changed |
| `FIREBASE_PROJECT_ID` | staging project id | staging project id | production project id |
| `FIREBASE_SERVICE_ACCOUNT` | local file path | Secret Manager-backed credential | Secret Manager-backed credential |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` (+ optional staging URL) | staging frontend URL | production frontend URL(s) only |
| `STRIPE_SECRET_KEY` | `sk_test_...` | `sk_test_...` | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | local/test webhook secret | staging webhook secret | production webhook secret |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_...` | `pk_test_...` | `pk_live_...` |
| `STRIPE_PRICE_MONTHLY` | test price id | test price id | live price id |
| `STRIPE_PRICE_ANNUAL` | test price id | test price id | live price id |
| `STRIPE_CHECKOUT_SUCCESS_URL` | localhost dashboard URL | staging dashboard URL | production dashboard URL |
| `STRIPE_CHECKOUT_CANCEL_URL` | localhost dashboard URL | staging dashboard URL | production dashboard URL |
| `STRIPE_BILLING_PORTAL_RETURN_URL` | localhost dashboard URL | staging dashboard URL | production dashboard URL |

## Frontend Environment Variables

| Variable | Local | Staging | Production |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | staging Cloud Run/API URL | production Cloud Run/API URL |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | staging web app config | staging web app config | production web app config |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | staging web app config | staging web app config | production web app config |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | staging project id | staging project id | production project id |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | staging web app config | staging web app config | production web app config |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | staging web app config | staging web app config | production web app config |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | staging web app config | staging web app config | production web app config |

## Notes

- GCP project id cannot be renamed after creation; only display name can be changed.
- Firebase project and GCP project are the same environment boundary.
- Keep secret names consistent across staging/production to simplify CI/CD.
- Restrict production CORS to production domains only.
