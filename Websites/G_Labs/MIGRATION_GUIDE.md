# WordPress to G-Labs Migration Guide

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

### B. Export Orders (WooCommerce)
1. Go to **WooCommerce > Orders**.
2. If you don't see an "Export" button, install the free plugin **"Advanced Order Export For WooCommerce"**.
3. Export all orders to CSV.
4. **Save this file** to `Websites/G_Labs/Legacy_Backup/orders.csv`.
   * *This is critical for tax purposes and historical records.*

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

## 2. Automating the Content Migration

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

## 3. Switching the Domain (Go Live)

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
