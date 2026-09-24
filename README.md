# 🛍️ ApexCommerce - Enterprise Retail & Smart Stock Management

ApexCommerce is a production-ready, full-featured e-commerce and stock management application built with **Streamlit**, **Pandas**, and **Plotly**. It features role-based access control, a seamless customer shopping experience, live inventory tracking, order fulfillment, and interactive analytics.

---

## 🔑 Demo Login Credentials

The application includes pre-configured demo personas with 1-click login buttons on the sign-in screen:

| Role | Username | Password | Persona | Primary Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Customer** | `customer` | `customer123` | Alex Mercer | Browse catalog, search & filter, cart, coupon discounts, simulated checkout, and personal order tracking. |
| **Store Admin** | `admin` | `admin123` | Sarah Chen | Executive KPI analytics, sales & stock visualizations, product catalog CRUD, order fulfillment status. |
| **Inventory Lead** | `manager` | `manager123` | Marcus Vance | Real-time stock monitoring, low-stock threshold alerts, batch restock, and inventory replenishment. |
| **Customer (Alt 1)** | `user1` | `user123` | Jordan Lee | Standard shopper access (backward compatible). |
| **Customer (Alt 2)** | `user2` | `user456` | Taylor Smith | Standard shopper access (backward compatible). |

> **Guest Mode & Custom Sign Up:** 
> - Click **"Continue as Guest"** to immediately explore the entire product catalog without entering credentials.
> - Switch to the **"✨ Create New Account (Sign Up)"** tab to register a new user with custom credentials. Account details are stored temporarily in memory for the active session, allowing the user to browse, add to cart, checkout, and track orders under their own name.

---

## ✨ Key Features

### 🏪 Customer Commerce Experience
- **Live Search & Discovery:** Search 240+ verified products by title, category, or keywords.
- **Multi-Faceted Filters:** Filter by category, maximum price slider, minimum star ratings (4.0+, 4.5+), in-stock availability, and best-seller badges.
- **Flexible Sorting:** Sort by Featured/Best Sellers, Price (Low to High / High to Low), Top Rated, and Review Counts.
- **Visual Product Cards:** Category tags, star ratings, review counts, stock health badges (`🟢 In Stock`, `🟡 Low Stock`, `🔴 Out of Stock`), quantity selector, and quick specs drawer.
- **Cart & Dynamic Pricing:** Line-item adjustments, subtotal, sales tax (7%), and progressive shipping fees (free shipping over $50).
- **Promo Coupon Engine:** Supports promo codes:
  - `SAVE15`: 15% off cart subtotal
  - `WELCOME10`: 10% off entire order
  - `FREESHIP`: Free standard express delivery
  - `VIP25`: 25% off orders over $75
- **Simulated Checkout & Stock Decrement:** Real-time stock deduction upon order placement, unique Order ID generation, and order confirmation.
- **Order Tracking ("My Orders"):** Visual 4-step delivery progress bar (`Order Placed` ➔ `Processing` ➔ `Shipped` ➔ `Delivered`) and itemized receipts.

### 🛠️ Executive Admin & Inventory Hub
- **Executive KPIs:** Live metrics for Total Revenue, Catalog Inventory Valuation, Active SKUs, Low Stock Warnings, and Order Counts.
- **Plotly Visualizations:**
  - Category Inventory Valuation (Horizontal Bar Chart)
  - Warehouse Stock Health Distribution (Donut Chart)
  - Price Distribution for Retail SKUs (Histogram)
  - Customer Order Pipeline (Fulfillment Bar Chart)
- **Inventory Workbench:** Filter low-stock (<10) or out-of-stock items, single-product replenishment, or **1-click batch restock (+25 units)**.
- **Product Catalog Management (CRUD):** Add new products with validation, edit price/stock/rating of existing items, and delete products.
- **Order Fulfillment Pipeline:** Review customer orders, shipping addresses, payment methods, and advance order statuses (`Processing`, `Shipped`, `Delivered`).
- **Category Explorer:** View category metrics, total items, average price, and aggregated stock.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.9+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run main.py
```
Open your browser at `http://localhost:8501`.

---

## 📁 Project Architecture

```plaintext
├── .streamlit/
│   └── config.toml          # Custom theme, primary colors, server settings
├── auth.py                  # Demo accounts, authentication, role verification
├── data_manager.py          # Data layer, CSV persistence, stock sync, orders, coupons
├── items.py                 # Customer catalog, filters, search, product card grid
├── manager.py               # Admin KPIs, Plotly analytics, inventory restock, CRUD
├── main.py                  # Core app router, top navbar, cart & checkout, order history
├── cat.csv                  # 51 retail & craft categories
├── item_management.csv      # Complete product catalog with stock counts
├── cart.csv                 # Persistent shopping cart state
├── orders.csv               # Historical & real-time customer orders
├── requirements.txt         # Project dependencies
└── README.md                # Documentation and setup guide
```

---

## 🔒 Security & Data Persistence
- All catalog edits, restock quantities, and customer orders persist safely to CSV format.
- Safe UTF-8 encoding is enforced across all file I/O operations.
- Dynamic session state ensures user isolation during active testing.
