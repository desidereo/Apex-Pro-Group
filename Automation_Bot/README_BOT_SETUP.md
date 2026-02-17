# TradingView Access Automation Bot

This system automatically grants/revokes access to your Invite-Only TradingView scripts based on Stripe payments.

## How It Works
1. **User Buys on Stripe**: They enter their TradingView Username in a custom field during checkout.
2. **Stripe Sends Webhook**: Your server receives the `checkout.session.completed` event.
3. **Bot Wakes Up**: The Python script launches a hidden Chrome browser.
4. **Access Granted**: The bot logs into TradingView, goes to your script, and adds the username.

## Setup Instructions

### 1. Install Dependencies
```bash
cd Automation_Bot
pip install -r requirements.txt
```

### 2. Configure Environment
Edit the `.env` file with your keys:
- `STRIPE_SECRET_KEY`: From Stripe Dashboard > Developers > API Keys.
- `STRIPE_WEBHOOK_SECRET`: From Stripe Dashboard > Developers > Webhooks (after you create one).
- `TV_USERNAME` / `TV_PASSWORD`: Your TradingView credentials.
- `SMTP_USER` / `SMTP_PASS`: Your email credentials for sending warnings (Use App Passwords for Gmail).

### 3. Stripe Setup
1. Create a **Product** in Stripe.
2. Create a **Payment Link** or **Checkout Session**.
3. **CRITICAL**: In the Checkout settings, add a **Custom Field**.
   - Type: `Text`
   - Label: `TradingView Username`
   - Key (Optional/API ID): `tv_username` (This must match the code in `server.py`).

### 4. Running the Bot
**First Run (Manual Login):**
The bot needs to save your login session (cookies) to avoid CAPTCHAs.
1. Run the bot script directly: `python tv_bot.py`
2. A Chrome window will open.
3. Manually log in to TradingView.
4. Close the window. The session is now saved in the `chrome_profile` folder.

**Start the Server:**
```bash
python server.py
```
The server will run on `http://localhost:4242`.

### 5. Expose to Internet (For Webhooks)
Stripe needs to send data to your local machine. Use **ngrok**:
```bash
ngrok http 4242
```
Copy the `https://xxxx.ngrok.io` URL and paste it into Stripe Webhooks settings, appending `/webhook` (e.g., `https://xxxx.ngrok.io/webhook`).

## 📂 Database
The system automatically creates a local database (`orders.db`) to track active subscriptions.
- Stores: Stripe Customer ID, Subscription ID, TV Username, **MT5 Account Number**, Product, Status.
- **Why?** This ensures that when a "Subscription Cancelled" webhook comes in, we know exactly which TradingView username to remove, even if the webhook payload is minimal.
- **Backup:** You can periodically back up `orders.db` if you wish to keep a history.

## 📈 MT5 Licensing System (New!)

You can now sell MT5 EAs/Indicators directly via Stripe and enforce licensing.

### 1. Stripe Setup for MT5
- Add a Custom Field to your Checkout:
  - Label: `MT5 Account Number`
  - Key: `mt5_account` (Must match this exactly!)

### 2. MQL5 Code Implementation
- Open `MQL5_License_Example.mq5` to see how to implement the license check in your EA.
- **Key Logic**: The EA sends a web request to your server (`/api/verify_license`) with its Account Number. The server checks the database and returns `Valid` or `Invalid`.

### 3. Delivering the File
- Place your `.ex5` files in the `downloads` folder.
- Rename them to match your Product Key (e.g., `prod_Qwerty123.ex5`) or customize the logic in `server.py`.
- Users can download via: `http://your-site.com/download/prod_Qwerty123` (You can email this link automatically via Stripe or Zapier).

## 🧹 Cleanup Tool (WooCommerce Migration)

If you are moving from WooCommerce and want to remove users who have cancelled/expired:

1. **Export Orders/Subscriptions**: Go to WooCommerce > Analytics > Downloads (or use a CSV export plugin).
   - Ensure your CSV has columns for **Order ID**, **Status**, **TradingView Username**, and **Customer Email**.
2. **Rename File**: Save your export as `woocommerce_subscriptions_export.csv` in this folder.
3. **Configure Columns**: Open `woo_cleanup.py` and edit the `COL_STATUS`, `COL_USERNAME`, `COL_EMAIL`, and `PRODUCT_SCRIPT_MAP` variables to match your CSV headers and Script URLs.
4. **Run Cleanup**:
   ```bash
   python woo_cleanup.py
   ```
   **How the logic works:**
   - **First Run**: It scans for cancelled users. It sends them a warning email ("Access removed in 48 hours") and marks the date in the CSV. It does **NOT** remove them yet.
   - **Wait 2 Days**: Run the script again (or daily).
   - **Subsequent Runs**: It checks the date. If 2 days have passed since the warning, it removes them from TradingView and marks them as "Removed".

## Limitations
- **TradingView UI Changes**: Since this uses "Screen Scraping" (Selenium), if TradingView changes their website layout, the bot might break and need updating.
- **2FA**: If you have 2-Factor Auth on TradingView, the automated login might struggle. It's best to use the "Saved Session" method described above.
