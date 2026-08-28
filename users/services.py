import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(course):
    """Создает продукт в Stripe и возвращает его ID."""
    try:
        product = stripe.Product.create(
            name=course.title,
            description=course.description or '',
        )
        return product['id']
    except stripe.error.StripeError as e:
        raise Exception(f"Ошибка Stripe при создании продукта: {e.user_message}")


def create_stripe_price(product_id, amount_in_cents):
    """Создает цену в Stripe и возвращает ID цены."""
    try:
        price = stripe.Price.create(
            product=product_id,
            unit_amount=amount_in_cents,
            currency="rub",  # или "usd"
        )
        return price['id']
    except stripe.error.StripeError as e:
        raise Exception(f"Ошибка Stripe при создании цены: {e.user_message}")


def create_stripe_session(price_id, success_url, cancel_url):
    """Создает сессию оплаты и возвращает (session_id, url)."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session['id'], session['url']
    except stripe.error.StripeError as e:
        raise Exception(f"Ошибка Stripe при создании сессии: {e.user_message}")