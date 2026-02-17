# WordPress to G-Labs Migration Guide

## 0. Accessing Your WordPress Admin
Before you can export, you need to log in. If you have forgotten your password, use **Method B**.

**Method A: Direct Link (Easiest)**
1.  Go to `www.g-labs.software/wp-admin` (or `www.g-labs.software/wp-login.php`).
2.  Enter your username and password.

**Method B: Via Hosting (Namecheap/cPanel)**
1.  Log in to your Namecheap Dashboard.
2.  Go to **Hosting List** -> **Go to cPanel**.
3.  Scroll down to the bottom to **WordPress Manager by Softaculous** (or just "Softaculous Apps Installer").
4.  Click the **WordPress** icon.
5.  Scroll down to "Current Installations".
6.  Click the **"Login"** (Person Icon) next to your website. **This logs you in automatically as Admin without needing a password.**

---

This guide will help you safely extract all your critical data (Products, Customers, Orders) from your existing WordPress/WooCommerce site before you replace it with the new G-Labs platform.

## 1. Export Your Data (Do this immediately)

Since you plan to delete the old site, you must secure your data first.

### A. Export Products (WooCommerce)
1. Log in to your WordPress Dashboard.
2. Go to **Products > All Products**.
3. Click the **Export** button at the top.
4. Select **"Export all columns"** and **"Export all products"**.
5. Click **Generate CSV**.
6. **Save this file** to `Websites/G_Labs/Legacy_Backup/products.csv`.

### B. Export Orders & Subscriptions (CRITICAL)
Data is often split between **Orders** (one-time) and **Subscriptions** (recurring). You need to export **BOTH** to ensure you don't miss any active users.

1. **Install Plugin:** Go to Plugins > Add New > Search for **"Advanced Order Export For WooCommerce"** (free version). Install & Activate.

2. **Export 1: Standard Orders**
   - Go to **WooCommerce > Export Orders**.
   - In the **"Filter data"** section (top), ensure "Post Type" is set to **Orders**.
   - In the **"Set up fields to export"** section (bottom):
     - Look for **"Custom Fields"** or **"Item Metadata"** on the right.
     - Drag fields like `tradingview_id`, `username`, or `_billing_woocmr_custom_field` into the list.
   - Click **Export** and save as `orders.csv`.

3. **Export 2: Subscriptions (If you have them)**
   - Stay on the same "Export Orders" page.
   - In the **"Filter data"** section, change "Post Type" to **Subscriptions**.
   - *Note: If you don't see "Subscriptions", you might not have the Subscriptions plugin active, or you only have standard orders.*
   - Ensure the same **Custom Fields** (TradingView ID) are in the export list.
   - Click **Export** and save as `subscriptions.csv`.

4. **Move Files:** Place both `orders.csv` and `subscriptions.csv` into `Websites/G_Labs/Legacy_Backup/`.

### C. Export Customers (WooCommerce)
1. Go to **Users > All Users** (or use the Order Export plugin above).
2. Export your customer list (Name, Email, Billing Address).
3. **Save this file** to `Websites/G_Labs/Legacy_Backup/customers.csv`.
   * *You will need this list to import into Mailchimp/ConvertKit for future marketing.*

### D. Download Media Library (Optional but Recommended)
1. Use an FTP client (like FileZilla) or a file manager plugin.
2. Download the folder `/wp-content/uploads/`.
3. Save it locally. This ensures you keep all your original product images and banners.

---

## 2. Extracting TradingView Usernames (New Script)

I have created a special script called `extract_usernames.py` to help you find your users.

**How to use it:**
1. Ensure your detailed `orders.csv` (from Step 1B) is in the `Legacy_Backup` folder.
2. Run the script: `python extract_usernames.py`
3. The script will show you the column names it found.
4. **Type the number** of the column that contains the TradingView ID.
5. It will generate a clean list called `customer_access_list.csv` containing just: **Email, Name, TradingView ID, Products**.

This list is exactly what you need to manually grant access or move them to a new system.

---

## 3. Automating the Content Migration

I have created a script called `import_products.py` in this folder.

**How it works:**
If you place your exported `products.csv` into the `Legacy_Backup` folder, running this script will:
1. Read your old product names, descriptions, and prices.
2. Automatically update `tradingview.html` and `mql5.html` with your real content.
3. This saves you from manually copying and pasting text for every product!

**To run it:**
1. Ensure `products.csv` is in `Websites/G_Labs/Legacy_Backup/`.
2. Open a terminal in `Websites/G_Labs/`.
3. Run: `python import_products.py`

---

## 4. Switching the Domain (Go Live)

Once you have your data backed up and the new site is ready:

1. **Upload the New Site:**
   - Upload the contents of `Websites/G_Labs/` to your hosting server (public_html).
   - *Ensure you delete or rename the old `wp-config.php` and `index.php` first.*

2. **Test:**
   - Visit `www.g-labs.software`.
   - Verify all links and images work.
   - Verify the Stripe payment links (once added).

3. **Cancel Old Hosting (Optional):**
   - Only cancel the WordPress hosting plan *after* you have confirmed the new site is working and you have all your backups secure.
