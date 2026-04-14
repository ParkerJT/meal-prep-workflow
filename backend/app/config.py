from dotenv import load_dotenv
import os

# Loading .env file
load_dotenv()

class Settings:
    """Cleanly loads environment variables as app settings"""

    # OpenAI API Key
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # OpenAI model for extraction + conversion (`extraction.py`, `conversion.py`)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Firebase Project ID
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    # Firebase Service Account
    FIREBASE_SERVICE_ACCOUNT: str = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")

    # CORS Allowed Origins
    CORS_ALLOWED_ORIGINS: list[str] = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

    # Stripe (Phase 3: Checkout, webhooks, Customer Portal). See BUILD_PLAN §3.1.
    # Secret key: Dashboard → Developers → API keys (sk_test_... / sk_live_...).
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    # Webhook signing secret: Dashboard → Developers → Webhooks → endpoint → Signing secret (whsec_...).
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    # Publishable key: same API keys page (pk_test_... / pk_live_...). Optional until client-side Stripe.js.
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    # Subscription prices from Product catalog (price_...); not secret but environment-specific.
    STRIPE_PRICE_MONTHLY: str = os.getenv("STRIPE_PRICE_MONTHLY", "")
    STRIPE_PRICE_ANNUAL: str = os.getenv("STRIPE_PRICE_ANNUAL", "")

    # Stripe Checkout + Billing Portal redirect URLs (full URLs, e.g. http://localhost:3000/dashboard)
    STRIPE_CHECKOUT_SUCCESS_URL: str = os.getenv("STRIPE_CHECKOUT_SUCCESS_URL", "")
    STRIPE_CHECKOUT_CANCEL_URL: str = os.getenv("STRIPE_CHECKOUT_CANCEL_URL", "")
    STRIPE_BILLING_PORTAL_RETURN_URL: str = os.getenv("STRIPE_BILLING_PORTAL_RETURN_URL", "")