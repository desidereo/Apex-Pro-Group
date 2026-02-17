import os
import stripe
from flask import Flask, request, jsonify
from tv_bot import TradingViewBot
from dotenv import load_dotenv
import database
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)

# Initialize Database
database.init_db()

# Stripe Configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

# TradingView Bot Configuration
TV_USERNAME = os.getenv('TV_USERNAME')
TV_PASSWORD = os.getenv('TV_PASSWORD')
# Map Product IDs to Script URLs
PRODUCT_SCRIPT_MAP = {
    "prod_Qwerty123": "https://www.tradingview.com/script/Example1-StateEngine/",
    "prod_Asdfgh456": "https://www.tradingview.com/script/Example2-Scanner/"
}

bot = TradingViewBot(TV_USERNAME, TV_PASSWORD)

@app.route('/api/verify_license', methods=['GET', 'POST'])
def verify_license():
    """
    Endpoint for MT5 EAs to check license status.
    Expected params: account_number, product_id
    """
    if request.method == 'POST':
        data = request.form
    else:
        data = request.args
        
    account = data.get('account_number')
    product_id = data.get('product_id')
    
    if not account or not product_id:
        return jsonify(valid=False, message="Missing parameters"), 400
        
    is_valid = database.check_mt5_license(account, product_id)
    
    if is_valid:
        return jsonify(valid=True, message="License Active")
    else:
        return jsonify(valid=False, message="License Invalid or Expired")

@app.route('/download/<product_key>')
def download_file(product_key):
    """
    Simple download link for products.
    In production, you should secure this (e.g., signed URLs or login).
    """
    # Map product keys to actual filenames in a 'downloads' folder
    # For now, we'll just mock it or assume files are named {product_key}.ex5
    
    # Security check: prevent directory traversal
    if '..' in product_key or '/' in product_key:
        return "Invalid filename", 400
        
    file_path = os.path.join("downloads", f"{product_key}.ex5")
    
    if os.path.exists(file_path):
        from flask import send_file
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found. Please contact support.", 404

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_completed(session)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_ended(subscription)
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)

    return jsonify(success=True)

def handle_checkout_completed(session):
    """
    Triggered when a customer pays.
    1. Get TradingView Username OR MT5 Account from Custom Fields.
    2. Get Product ID.
    3. Call Bot to Add User (if TV) or Just Save to DB (if MT5).
    4. Save to Database.
    """
    tv_username = None
    mt5_account = None
    
    # Extract Custom Fields
    if session.get('custom_fields'):
        for field in session['custom_fields']:
            if field['key'] == 'tv_username': 
                tv_username = field['text']['value']
            elif field['key'] == 'mt5_account':
                mt5_account = field['text']['value']
    
    # Fallback: Check metadata
    if not tv_username:
        tv_username = session.get('metadata', {}).get('tv_username')
    if not mt5_account:
        mt5_account = session.get('metadata', {}).get('mt5_account')

    if not tv_username and not mt5_account:
        logging.error("No TradingView username OR MT5 Account found in checkout session.")
        return

    # Extract Stripe IDs
    stripe_customer_id = session.get('customer')
    stripe_subscription_id = session.get('subscription')

    # Determine product key
    product_key = session.get('metadata', {}).get('product_key', 'default')
    
    # --- Action 1: TradingView ---
    tv_success = True # Default to true if not applicable
    if tv_username:
        script_url = PRODUCT_SCRIPT_MAP.get(product_key)
        if not script_url:
            script_url = list(PRODUCT_SCRIPT_MAP.values())[0]
            logging.warning(f"Product key '{product_key}' not found. using default script.")
    
        logging.info(f"Granting access for {tv_username} to {script_url}")
        tv_success = bot.manage_access(script_url, tv_username, action="add")
        if not tv_success:
            logging.error(f"Failed to add {tv_username} to TradingView.")

    # --- Action 2: Save to Database (MT5 & TV) ---
    # We save if at least one action was valid/successful
    if tv_success:
        if mt5_account:
            logging.info(f"Registering MT5 License for Account {mt5_account} (Product: {product_key})")
            
        database.add_order(
            stripe_customer_id, 
            stripe_subscription_id, 
            tv_username, 
            mt5_account, 
            product_key, 
            status="active"
        )

def handle_subscription_ended(subscription):
    """
    Triggered when subscription is cancelled/expired.
    """
    sub_id = subscription.get('id')
    
    # 1. Look up user in Database
    order = database.get_user_by_subscription(sub_id)
    
    if not order:
        logging.error(f"Subscription {sub_id} ended, but no matching order found in DB.")
        return

    tv_username = order['tv_username']
    product_key = order['product_id']
    
    script_url = PRODUCT_SCRIPT_MAP.get(product_key)
    if not script_url:
        script_url = list(PRODUCT_SCRIPT_MAP.values())[0]

    logging.info(f"Revoking access for {tv_username} (Sub: {sub_id})")
    
    # 2. Remove from TradingView
    success = bot.manage_access(script_url, tv_username, action="remove")
    
    # 3. Update Database Status
    database.update_order_status(sub_id, "cancelled")

def handle_payment_failed(invoice):
    """
    Triggered when payment fails (e.g. card declined on renewal).
    """
    sub_id = invoice.get('subscription')
    if not sub_id:
        return

    logging.info(f"Payment failed for Subscription {sub_id}. Treating as cancellation.")
    
    # Reuse logic for ending subscription (or you might want a different logic for 'past_due')
    # For now, let's just log and update status to 'past_due' without immediate removal 
    # (usually you give a grace period). 
    # If you want immediate removal, call handle_subscription_ended(invoice)
    
    database.update_order_status(sub_id, "past_due")

if __name__ == '__main__':
    app.run(port=4242)
