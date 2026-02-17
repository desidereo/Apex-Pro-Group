import pandas as pd
import os
import logging
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tv_bot import TradingViewBot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
# ---------------------------------------------------------
# Path to your WooCommerce Export CSV
CSV_FILE = "woocommerce_subscriptions_export.csv"

# Column Names in your CSV (Change these to match your export!)
    COL_ORDER_ID = "Order ID"       # To check if it's a valid order
    COL_STATUS = "Status"           # e.g., 'status', 'subscription_status'
    COL_USERNAME = "TV Username"    # The meta field where you captured their ID
    COL_PRODUCT = "Product Name"    # To know which script to remove them from
    COL_EMAIL = "Customer Email"    # New: Need email to send warnings

# Columns for State Tracking (Script will add these if missing)
COL_WARNING_SENT = "Warning Sent Date"
COL_REMOVED = "Removed Date"

# Map Product Names (from CSV) to TradingView Script URLs
PRODUCT_SCRIPT_MAP = {
    "BTMM State Engine": "https://www.tradingview.com/script/Example1-StateEngine/",
    "BTMM Multi-Pair Scanner": "https://www.tradingview.com/script/Example2-Scanner/",
    "Default": "https://www.tradingview.com/script/YOUR_DEFAULT_SCRIPT_ID/"
}

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)
SUPPORT_EMAIL = "support@g-labs.software"

# ---------------------------------------------------------

def send_warning_email(to_email, username, product_name):
    """Sends a warning email to the user."""
    if not SMTP_USER or not SMTP_PASS:
        logging.error("SMTP Credentials not set. Skipping email.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"Action Required: Your G-Labs Access is Expiring ({product_name})"

        body = f"""
        <html>
          <body>
            <p>Hi {username},</p>
            <p>We noticed your subscription for <strong>{product_name}</strong> has ended or was cancelled.</p>
            <p>Your access to the TradingView indicator will be removed in <strong>48 hours</strong>.</p>
            <p>If you believe this is a mistake, or if you have renewed your subscription, please contact us immediately so we don't cut you off!</p>
            <p><strong>Contact Support:</strong> <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
            <br>
            <p>Regards,<br>The G-Labs Team</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        
        logging.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
        return False

def clean_up_cancelled_users():
    if not os.path.exists(CSV_FILE):
        logging.error(f"File {CSV_FILE} not found! Please place your CSV in this folder.")
        return

    logging.info(f"Reading {CSV_FILE}...")
    try:
        df = pd.read_csv(CSV_FILE)
    except Exception as e:
        logging.error(f"Failed to read CSV: {e}")
        return

    # Add tracking columns if they don't exist
    if COL_WARNING_SENT not in df.columns:
        df[COL_WARNING_SENT] = ""
    if COL_REMOVED not in df.columns:
        df[COL_REMOVED] = ""

    target_statuses = ['cancelled', 'expired', 'trash', 'failed', 'on-hold']
    
    if COL_STATUS not in df.columns or COL_USERNAME not in df.columns:
        logging.error(f"Columns '{COL_STATUS}' or '{COL_USERNAME}' not found in CSV.")
        return

    # Initialize Bot only if we need to remove someone
    bot = None
    tv_username = os.getenv('TV_USERNAME')
    tv_password = os.getenv('TV_PASSWORD')
    
    rows_processed = 0
    removals_count = 0
    warnings_count = 0

    for index, row in df.iterrows():
        status = str(row[COL_STATUS]).lower()
        user_tv = str(row[COL_USERNAME]).strip()
        user_email = str(row.get(COL_EMAIL, "")).strip()
        order_id = str(row.get(COL_ORDER_ID, "")).strip()
        product_name = str(row.get(COL_PRODUCT, "Default")).strip()
        warning_date_str = str(row[COL_WARNING_SENT]).strip()
        removed_date_str = str(row[COL_REMOVED]).strip()

        # Skip invalid rows, already removed users, or MANUAL entries (missing Order ID or Email)
        if status not in target_statuses or not user_tv or user_tv.lower() == 'nan' or removed_date_str:
            continue

        # SAFETY CHECK: If Order ID or Email is missing, assume it's a manual/special user -> SKIP
        if not order_id or order_id.lower() == 'nan' or not user_email or user_email.lower() == 'nan':
            logging.info(f"Skipping {user_tv} (Missing Order ID or Email - assumed manual entry).")
            continue
        
        rows_processed += 1
        today = datetime.date.today()
        
        # Determine Script URL
        script_url = PRODUCT_SCRIPT_MAP.get("Default")
        for key, url in PRODUCT_SCRIPT_MAP.items():
            if key in product_name:
                script_url = url
                break

        # Check if warning has been sent
        if not warning_date_str or warning_date_str == 'nan':
            # CASE 1: Send Warning
            logging.info(f"User {user_tv} needs warning. Sending email...")
            if send_warning_email(user_email, user_tv, product_name):
                df.at[index, COL_WARNING_SENT] = str(today)
                warnings_count += 1
            else:
                logging.warning(f"Could not send email. Skipping warning flag.")
        
        else:
            # CASE 2: Check if 2 days have passed
            try:
                warning_date = datetime.datetime.strptime(warning_date_str, "%Y-%m-%d").date()
                days_diff = (today - warning_date).days
                
                if days_diff >= 2:
                    # Proceed to Remove
                    logging.info(f"User {user_tv} warned {days_diff} days ago. Removing access...")
                    
                    if not bot and tv_username and tv_password:
                        bot = TradingViewBot(tv_username, tv_password)
                        bot.start_driver()
                        bot.login()
                    
                    if bot:
                        success = bot.manage_access(script_url, user_tv, action="remove")
                        if success:
                            df.at[index, COL_REMOVED] = str(today)
                            removals_count += 1
                else:
                    logging.info(f"User {user_tv} warned {days_diff} days ago. Waiting for 2 days.")
            except ValueError:
                 logging.error(f"Invalid date format for {user_tv}: {warning_date_str}")

    if bot:
        bot.close_driver()

    # Save changes back to CSV
    df.to_csv(CSV_FILE, index=False)
    logging.info(f"Process Complete. Warnings Sent: {warnings_count}, Users Removed: {removals_count}")

if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        data = {
            "Order ID": [101, 102, 103],
            "Status": ["cancelled", "cancelled", "active"],
            "Product Name": ["BTMM State Engine", "BTMM State Engine", "Multi-Pair Scanner"],
            "TV Username": ["TraderJoe", "PaperHands69", "CryptoKing"],
            "Customer Email": ["joe@example.com", "paper@example.com", "king@example.com"]
        }
        pd.DataFrame(data).to_csv(CSV_FILE, index=False)
        print(f"Created template file: {CSV_FILE}. Please replace it with your actual data.")
    else:
        clean_up_cancelled_users()
