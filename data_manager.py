"""
Data management module for ApexCommerce.
Handles CSV persistence, stock tracking, catalog updates, carts, and order fulfillment.
"""
import os
import random
import datetime
import pandas as pd
import streamlit as st

ITEMS_FILE = "item_management.csv"
CAT_FILE = "cat.csv"
CART_FILE = "cart.csv"
ORDERS_FILE = "orders.csv"

# Predefined discount coupons
COUPONS = {
    "SAVE15": {"type": "percent", "value": 0.15, "desc": "15% Off Your Order", "min_spend": 0.0},
    "WELCOME10": {"type": "percent", "value": 0.10, "desc": "10% Welcome Customer Discount", "min_spend": 0.0},
    "FREESHIP": {"type": "shipping", "value": 0.0, "desc": "Free Standard Express Delivery", "min_spend": 0.0},
    "VIP25": {"type": "percent", "value": 0.25, "desc": "25% VIP Discount (Orders over $75)", "min_spend": 75.0},
}


def load_categories() -> pd.DataFrame:
    """Load categories dataframe from cat.csv."""
    if os.path.exists(CAT_FILE):
        df = pd.read_csv(CAT_FILE, encoding="utf-8")
        # Ensure proper column names
        if "category_id" in df.columns and "category_name" in df.columns:
            return df
    # Fallback default categories
    return pd.DataFrame([
        {"category_id": 1, "category_name": "Beading & Jewelry Making"},
        {"category_id": 2, "category_name": "Fabric Decorating"},
        {"category_id": 3, "category_name": "Craft Supplies & Materials"},
    ])


def load_items() -> pd.DataFrame:
    """
    Load items dataframe. Ensures stock column exists and price defaults are sanitized.
    """
    if not os.path.exists(ITEMS_FILE):
        # Fallback empty dataframe with standard columns
        return pd.DataFrame(columns=[
            "title", "price", "category_id", "stars", "reviews", "isBestSeller", "category_name", "stock"
        ])

    df = pd.read_csv(ITEMS_FILE, encoding="utf-8")

    # Clean Unnamed: 0 if present
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # Ensure price is positive numeric
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(9.99)
    df.loc[df["price"] <= 0, "price"] = 7.99
    df["price"] = df["price"].round(2)

    # Ensure stars is float
    if "stars" in df.columns:
        df["stars"] = pd.to_numeric(df["stars"], errors="coerce").fillna(4.5).round(1)
    else:
        df["stars"] = 4.5

    # Ensure reviews is int
    if "reviews" in df.columns:
        df["reviews"] = pd.to_numeric(df["reviews"], errors="coerce").fillna(120).astype(int)
    else:
        df["reviews"] = 120

    # Ensure isBestSeller is boolean
    if "isBestSeller" in df.columns:
        df["isBestSeller"] = df["isBestSeller"].astype(bool)
    else:
        df["isBestSeller"] = False

    # Seed stock column if not present
    if "stock" not in df.columns:
        random.seed(42)  # Deterministic seed for consistency
        stocks = []
        for i in range(len(df)):
            if i in [3, 14, 25, 48, 72, 105]:
                # Realistic low stock items
                stocks.append(random.randint(2, 5))
            elif i in [9, 33]:
                # Out of stock demo items
                stocks.append(0)
            else:
                # Normal healthy stock
                stocks.append(random.randint(18, 65))
        df["stock"] = stocks
        # Save back to CSV so stock persists
        df.to_csv(ITEMS_FILE, index=False)
    else:
        df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(20).astype(int)

    # Ensure category_name matches category_id
    cat_df = load_categories()
    cat_dict = dict(zip(cat_df["category_id"], cat_df["category_name"]))
    if "category_name" not in df.columns or df["category_name"].isna().any():
        df["category_name"] = df["category_id"].map(cat_dict).fillna("General Merchandise")

    return df


def save_items(df: pd.DataFrame):
    """Save items dataframe to CSV."""
    df.to_csv(ITEMS_FILE, index=False, encoding="utf-8")


def add_product(title: str, category_id: int, price: float, stars: float, reviews: int, is_bestseller: bool, stock: int):
    """Add a new product to the catalog."""
    df = load_items()
    cat_df = load_categories()
    cat_name = cat_df.loc[cat_df["category_id"] == category_id, "category_name"].values
    category_name = cat_name[0] if len(cat_name) > 0 else "General Merchandise"

    new_row = {
        "title": title.strip(),
        "price": round(float(price), 2),
        "category_id": int(category_id),
        "stars": round(float(stars), 1),
        "reviews": int(reviews),
        "isBestSeller": bool(is_bestseller),
        "category_name": category_name,
        "stock": int(stock),
    }

    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_items(updated_df)
    return True


def update_product(original_title: str, new_title: str, category_id: int, price: float, stars: float, stock: int, is_bestseller: bool):
    """Update an existing product."""
    df = load_items()
    match = df[df["title"] == original_title]
    if match.empty:
        return False

    cat_df = load_categories()
    cat_name = cat_df.loc[cat_df["category_id"] == category_id, "category_name"].values
    category_name = cat_name[0] if len(cat_name) > 0 else "General Merchandise"

    idx = match.index[0]
    df.at[idx, "title"] = new_title.strip()
    df.at[idx, "category_id"] = int(category_id)
    df.at[idx, "category_name"] = category_name
    df.at[idx, "price"] = round(float(price), 2)
    df.at[idx, "stars"] = round(float(stars), 1)
    df.at[idx, "stock"] = int(stock)
    df.at[idx, "isBestSeller"] = bool(is_bestseller)

    save_items(df)
    return True


def delete_product(title: str):
    """Delete a product from catalog."""
    df = load_items()
    df = df[df["title"] != title]
    save_items(df)
    return True


def update_stock(title: str, new_stock: int):
    """Update stock level for a single product."""
    df = load_items()
    if title in df["title"].values:
        df.loc[df["title"] == title, "stock"] = max(0, int(new_stock))
        save_items(df)
        return True
    return False


def batch_restock(titles: list, add_quantity: int):
    """Add quantity to multiple products."""
    df = load_items()
    for title in titles:
        if title in df["title"].values:
            curr = df.loc[df["title"] == title, "stock"].values[0]
            df.loc[df["title"] == title, "stock"] = int(curr) + int(add_quantity)
    save_items(df)


# ---------------- ORDERS & FULFILLMENT ----------------

def init_orders():
    """Seed orders.csv with realistic commerce demo history if not present."""
    if not os.path.exists(ORDERS_FILE) or os.path.getsize(ORDERS_FILE) < 10:
        sample_orders = [
            {
                "order_id": "ORD-7192",
                "username": "customer",
                "customer_name": "Alex Mercer",
                "email": "alex.mercer@example.com",
                "order_date": (datetime.datetime.now() - datetime.timedelta(days=3, hours=4)).strftime("%Y-%m-%d %H:%M"),
                "items_summary": "Paxcoo 1mm Elastic String (x2), Zenacolor 20 Fabric Markers (x1)",
                "total_items": 3,
                "subtotal": 21.97,
                "discount": 3.30,
                "shipping": 0.00,
                "tax": 1.31,
                "total_amount": 19.98,
                "shipping_address": "742 Evergreen Terrace, Springfield, OR 97477",
                "payment_method": "Credit Card (•••• 4242)",
                "status": "Delivered",
            },
            {
                "order_id": "ORD-8451",
                "username": "customer",
                "customer_name": "Alex Mercer",
                "email": "alex.mercer@example.com",
                "order_date": (datetime.datetime.now() - datetime.timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M"),
                "items_summary": "DIY Tie Dye Kit for Kids & Adults (x1), Tulip One-Step Tie-Dye Party (x1)",
                "total_items": 2,
                "subtotal": 38.33,
                "discount": 3.83,
                "shipping": 5.00,
                "tax": 2.76,
                "total_amount": 42.26,
                "shipping_address": "742 Evergreen Terrace, Springfield, OR 97477",
                "payment_method": "PayPal (alex.mercer@example.com)",
                "status": "Shipped",
            },
            {
                "order_id": "ORD-9304",
                "username": "user1",
                "customer_name": "Jordan Lee",
                "email": "jordan.lee@example.com",
                "order_date": (datetime.datetime.now() - datetime.timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
                "items_summary": "Duufin 120 Pieces Acrylic Keychain Blanks Set (x2)",
                "total_items": 2,
                "subtotal": 19.98,
                "discount": 0.00,
                "shipping": 5.00,
                "tax": 1.40,
                "total_amount": 26.38,
                "shipping_address": "100 Pine Crest Way, Seattle, WA 98101",
                "payment_method": "Apple Pay",
                "status": "Processing",
            },
        ]
        df = pd.DataFrame(sample_orders)
        df.to_csv(ORDERS_FILE, index=False, encoding="utf-8")


def load_orders() -> pd.DataFrame:
    """Load orders dataframe."""
    init_orders()
    try:
        return pd.read_csv(ORDERS_FILE, encoding="utf-8")
    except Exception:
        return pd.DataFrame(columns=[
            "order_id", "username", "customer_name", "email", "order_date",
            "items_summary", "total_items", "subtotal", "discount", "shipping",
            "tax", "total_amount", "shipping_address", "payment_method", "status"
        ])


def save_orders(df: pd.DataFrame):
    """Save orders dataframe to CSV."""
    df.to_csv(ORDERS_FILE, index=False, encoding="utf-8")


def create_order(username: str, customer_name: str, email: str, address: str, payment_method: str,
                 cart: dict, subtotal: float, discount: float, shipping: float, tax: float, total: float):
    """
    Process order: generates order ID, decrements stock in catalog, and persists order.
    """
    df_items = load_items()
    order_id = f"ORD-{random.randint(10000, 99999)}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Item summary string and decrement stock
    summary_parts = []
    total_qty = 0
    for title, details in cart.items():
        qty = details["qty"]
        total_qty += qty
        summary_parts.append(f"{title[:35]} (x{qty})")

        # Decrement stock in catalog
        if title in df_items["title"].values:
            curr_stock = df_items.loc[df_items["title"] == title, "stock"].values[0]
            df_items.loc[df_items["title"] == title, "stock"] = max(0, int(curr_stock) - qty)

    # Save decremented stock
    save_items(df_items)

    new_order = {
        "order_id": order_id,
        "username": username,
        "customer_name": customer_name,
        "email": email,
        "order_date": now_str,
        "items_summary": ", ".join(summary_parts),
        "total_items": total_qty,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping": round(shipping, 2),
        "tax": round(tax, 2),
        "total_amount": round(total, 2),
        "shipping_address": address,
        "payment_method": payment_method,
        "status": "Processing",
    }

    df_orders = load_orders()
    updated_orders = pd.concat([pd.DataFrame([new_order]), df_orders], ignore_index=True)
    save_orders(updated_orders)

    return order_id


def update_order_status(order_id: str, new_status: str):
    """Update order fulfillment status."""
    df_orders = load_orders()
    if order_id in df_orders["order_id"].values:
        df_orders.loc[df_orders["order_id"] == order_id, "status"] = new_status
        save_orders(df_orders)
        return True
    return False


# ---------------- CART HELPERS ----------------

def load_cart_csv() -> dict:
    """Load cart dictionary from CSV."""
    if not os.path.exists(CART_FILE):
        return {}
    try:
        df = pd.read_csv(CART_FILE, encoding="utf-8")
        cart = {}
        for _, row in df.iterrows():
            cart[str(row["title"])] = {
                "price": float(row["price"]),
                "qty": int(row["qty"]),
            }
        return cart
    except Exception:
        try:
            df = pd.read_csv(CART_FILE, encoding="latin1")
            cart = {}
            for _, row in df.iterrows():
                cart[str(row["title"])] = {
                    "price": float(row["price"]),
                    "qty": int(row["qty"]),
                }
            return cart
        except Exception:
            return {}


def save_cart_csv(cart: dict):
    """Save cart dictionary to CSV."""
    if not cart:
        pd.DataFrame(columns=["title", "price", "qty"]).to_csv(CART_FILE, index=False, encoding="utf-8")
        return
    rows = [{"title": k, "price": v["price"], "qty": v["qty"]} for k, v in cart.items()]
    pd.DataFrame(rows).to_csv(CART_FILE, index=False, encoding="utf-8")


def validate_coupon(coupon_code: str, subtotal: float) -> tuple[bool, str, float]:
    """
    Validate coupon code. Returns (is_valid, message, discount_amount).
    """
    if not coupon_code:
        return False, "", 0.0

    code = coupon_code.strip().upper()
    if code not in COUPONS:
        return False, "❌ Invalid coupon code.", 0.0

    promo = COUPONS[code]
    if subtotal < promo.get("min_spend", 0.0):
        return False, f"❌ Requires minimum spend of ${promo['min_spend']:.2f}.", 0.0

    if promo["type"] == "percent":
        discount = subtotal * promo["value"]
        return True, f"✅ Applied: {promo['desc']}", discount
    elif promo["type"] == "shipping":
        return True, f"✅ Applied: {promo['desc']}", 0.0

    return False, "Invalid promo rule.", 0.0
