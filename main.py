"""
ApexCommerce - Professional Commerce & Inventory Management Portal
Streamlit-ready application with full role-based access, demo credentials, stock tracking, and orders.
"""
import streamlit as st
import pandas as pd
from auth import (
    authenticate,
    init_auth_state,
    login_user,
    logout_user,
    is_authenticated,
    get_current_user,
    render_demo_credentials_card,
    render_signup_form,
    register_user,
    get_all_users,
    DEMO_USERS,
)
from data_manager import (
    load_cart_csv,
    save_cart_csv,
    load_orders,
    create_order,
    validate_coupon,
    COUPONS,
)
from items import render_storefront
from manager import render_admin_dashboard

# ---------------- STREAMLIT PAGE CONFIG ----------------
st.set_page_config(
    page_title="ApexCommerce | Smart Stock & Retail Engine",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- CUSTOM CSS STYLING ----------------
st.markdown(
    """
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Navbar container */
    .top-nav {
        background: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
        padding: 0.75rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Badges */
    .badge-role {
        background: #EEF2FF;
        color: #4338CA;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        border: 1px solid #C7D2FE;
    }
    
    /* Metrics override */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #64748B;
        font-size: 0.85rem;
    }
    
    [data-testid="stMetricValue"] {
        font-weight: 800;
        color: #0F172A;
    }
    
    /* Buttons */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(67, 56, 202, 0.15);
    }
    
    /* Containers & Cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        border-color: #E2E8F0;
        background: #FFFFFF;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- INITIALIZE STATE ----------------
init_auth_state()

if "cart" not in st.session_state:
    st.session_state.cart = load_cart_csv()

if "page" not in st.session_state:
    # Default to storefront if authenticated, else login
    st.session_state.page = "login"

if "applied_coupon" not in st.session_state:
    st.session_state.applied_coupon = None

if "coupon_discount" not in st.session_state:
    st.session_state.coupon_discount = 0.0

if "guest_mode" not in st.session_state:
    st.session_state.guest_mode = False


# ---------------- NAVIGATION & HEADER ----------------
def render_navbar():
    """Render top persistent navigation bar and role indicator."""
    cart_count = sum(item["qty"] for item in st.session_state.cart.values())
    user = get_current_user()

    with st.container():
        nav_col1, nav_col2, nav_col3 = st.columns([3, 4, 3])

        with nav_col1:
            st.markdown(
                """
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.8rem;">🛍️</span>
                    <div>
                        <div style="font-weight: 800; font-size: 1.2rem; color: #1E1B4B; letter-spacing: -0.5px;">ApexCommerce</div>
                        <div style="font-size: 0.75rem; color: #6366F1; font-weight: 600;">ENTERPRISE STOCK & RETAIL</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with nav_col2:
            # Navigation buttons
            btn_cols = st.columns(4)
            with btn_cols[0]:
                if st.button("🏪 Storefront", use_container_width=True, key="nav_store"):
                    st.session_state.page = "storefront"
                    st.rerun()

            with btn_cols[1]:
                cart_label = f"🧺 Cart ({cart_count})" if cart_count > 0 else "🧺 Cart"
                if st.button(cart_label, use_container_width=True, key="nav_cart"):
                    st.session_state.page = "cart"
                    st.rerun()

            with btn_cols[2]:
                if st.button("📦 Orders", use_container_width=True, key="nav_orders"):
                    st.session_state.page = "orders"
                    st.rerun()

            with btn_cols[3]:
                # If Admin or Manager, show Admin Hub button
                if user["role"] in ["Admin", "Manager"]:
                    if st.button("📊 Admin Hub", use_container_width=True, key="nav_admin"):
                        st.session_state.page = "admin_dashboard"
                        st.rerun()
                else:
                    if st.button("🔐 Sign In / Sign Up", use_container_width=True, key="nav_login_switch"):
                        st.session_state.page = "login"
                        st.rerun()

        with nav_col3:
            # User profile or guest chip
            if user["authenticated"]:
                role_icon = "👑" if user["role"] == "Admin" else ("📦" if user["role"] == "Manager" else "🛒")
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px;">
                        <span class="badge-role">{role_icon} {user['role']}</span>
                        <span style="font-weight: 700; font-size: 0.88rem; color: #1E293B;">{user['name']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Log out ↩", key="top_logout", help="Log out of current session"):
                    logout_user()
                    st.rerun()
            else:
                st.markdown(
                    """
                    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px;">
                        <span style="background: #F1F5F9; color: #475569; padding: 4px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600;">
                            👤 Guest Shopper
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🔐 Sign In / Sign Up", key="top_signin", help="Sign in with demo credentials or create an account"):
                    st.session_state.page = "login"
                    st.rerun()

    st.markdown("<hr style='margin: 0.5rem 0 1.25rem 0; border: none; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)


# ---------------- SIDEBAR CONTROLS ----------------
def render_sidebar():
    """Render sidebar navigation and quick switcher."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
                <div style="font-size: 2.2rem;">🛍️</div>
                <h3 style="margin: 0; color: #1E1B4B; font-weight: 800;">ApexCommerce</h3>
                <div style="font-size: 0.78rem; color: #6366F1; font-weight: 600;">Smart Stock & Retail Portal</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user = get_current_user()

        # Session profile card
        if user["authenticated"]:
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
                    <div style="font-size: 0.75rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Active Session</div>
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">{user['name']}</div>
                    <div style="font-size: 0.8rem; color: #4338CA; font-weight: 600;">{user['role']} Account</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">{user['email']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
                    <div style="font-weight: 700; color: #92400E; font-size: 0.88rem;">Browsing as Guest</div>
                    <div style="font-size: 0.75rem; color: #B45309;">Log in to checkout, track your orders, or access admin features.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 🧭 Navigation")
        cart_count = sum(item["qty"] for item in st.session_state.cart.values())

        nav_options = ["🛍️ Storefront", f"🧺 Cart ({cart_count})", "📦 My Orders"]
        if user["role"] in ["Admin", "Manager"]:
            nav_options.append("📊 Admin & Stock Hub")
        nav_options.append("🔐 Sign In / Sign Up")

        # Determine current selection index
        current_map = {
            "storefront": "🛍️ Storefront",
            "cart": f"🧺 Cart ({cart_count})",
            "orders": "📦 My Orders",
            "admin_dashboard": "📊 Admin & Stock Hub",
            "login": "🔐 Sign In / Sign Up",
        }
        curr_label = current_map.get(st.session_state.page, "🛍️ Storefront")
        if curr_label not in nav_options:
            curr_label = nav_options[0]

        selected_nav = st.radio(
            "Go to:",
            options=nav_options,
            index=nav_options.index(curr_label),
            label_visibility="collapsed",
        )

        if selected_nav == "🛍️ Storefront" and st.session_state.page != "storefront":
            st.session_state.page = "storefront"
            st.rerun()
        elif selected_nav.startswith("🧺 Cart") and st.session_state.page != "cart":
            st.session_state.page = "cart"
            st.rerun()
        elif selected_nav == "📦 My Orders" and st.session_state.page != "orders":
            st.session_state.page = "orders"
            st.rerun()
        elif selected_nav == "📊 Admin & Stock Hub" and st.session_state.page != "admin_dashboard":
            st.session_state.page = "admin_dashboard"
            st.rerun()
        elif selected_nav == "🔐 Sign In / Sign Up" and st.session_state.page != "login":
            st.session_state.page = "login"
            st.rerun()

        st.markdown("---")

        # Quick Switcher for evaluators
        st.markdown("#### ⚡ 1-Click Role Switch")
        st.markdown("<div style='font-size: 0.8rem; color: #64748B; margin-bottom: 8px;'>Instantly switch persona to test features:</div>", unsafe_allow_html=True)

        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("🛒 Shopper", key="sb_cust", use_container_width=True):
                login_user("customer", DEMO_USERS["customer"])
                st.session_state.page = "storefront"
                st.rerun()
        with sc2:
            if st.button("👑 Admin", key="sb_admin", use_container_width=True):
                login_user("admin", DEMO_USERS["admin"])
                st.session_state.page = "admin_dashboard"
                st.rerun()

        if st.button("📦 Inventory Lead", key="sb_mgr", use_container_width=True):
            login_user("manager", DEMO_USERS["manager"])
            st.session_state.page = "admin_dashboard"
            st.rerun()

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 0.75rem; color: #94A3B8; text-align: center;">
                ApexCommerce Enterprise v2.4<br/>
                Streamlit + Pandas + Plotly Ready
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------- AUTH & SIGNUP VIEW ----------------
def render_auth_page():
    """Render professional authentication screen with Sign In, Demo Access, and Sign Up."""
    st.markdown(
        """
        <div style="text-align: center; max-width: 680px; margin: 0 auto 1.25rem auto;">
            <div style="font-size: 2.8rem; margin-bottom: 4px;">🔐</div>
            <h2 style="font-weight: 800; color: #1E1B4B; margin: 0 0 6px 0;">ApexCommerce Access Portal</h2>
            <p style="color: #64748B; margin: 0; font-size: 1rem;">
                Sign in with demo personas, use manual credentials, or create a new temporary profile instantly.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Center container
    _, center_col, _ = st.columns([1, 4, 1])

    with center_col:
        tab_signin, tab_signup = st.tabs(["🔐 Sign In & Demo Access", "✨ Create New Account (Sign Up)"])

        with tab_signin:
            # Render Demo Credentials Card
            render_demo_credentials_card()

            # Manual Login Form Card
            with st.container(border=True):
                st.markdown("#### ✍️ Manual Sign In")
                with st.form("manual_login_form"):
                    username = st.text_input("Username", placeholder="e.g. customer, admin, manager, or your new username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("Sign In to Portal", use_container_width=True)

                    if submitted:
                        user_info = authenticate(username, password)
                        if user_info:
                            login_user(username, user_info)
                            st.success(f"Welcome back, {user_info['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please verify credentials or switch to the Sign Up tab.")

            # Guest mode option
            st.markdown("<div style='text-align: center; margin-top: 1rem;'>", unsafe_allow_html=True)
            if st.button("🌐 Continue as Guest (Browse Storefront)", use_container_width=True, key="guest_from_login"):
                st.session_state.authenticated = False
                st.session_state.guest_mode = True
                st.session_state.page = "storefront"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_signup:
            # Render dedicated sign up form
            render_signup_form()

            # Display active temporary accounts in this session if any
            reg_users = st.session_state.get("registered_users", {})
            if reg_users:
                st.markdown("---")
                st.markdown("#### 👥 Temporary Accounts Active in this Session")
                for u_name, u_data in reg_users.items():
                    st.markdown(
                        f"""
                        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{u_data['name']}</strong> (<code>{u_name}</code>) - <span style="color: #4338CA; font-weight: 600;">{u_data['role']}</span>
                            </div>
                            <div style="font-size: 0.8rem; color: #16A34A; font-weight: 600;">Active in Memory</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# ---------------- CART & CHECKOUT VIEW ----------------
def render_cart_page():
    """Render interactive shopping cart, coupon codes, and simulated checkout."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h2 style="font-weight: 800; color: #1E1B4B; margin: 0;">🧺 Shopping Cart & Checkout</h2>
            <p style="color: #64748B; margin: 0;">Review items, apply promo coupons, and complete your order.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cart = st.session_state.cart

    if not cart:
        with st.container(border=True):
            st.markdown(
                """
                <div style="text-align: center; padding: 2.5rem 1rem;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">🧺</div>
                    <h3 style="color: #1E293B; margin: 0 0 8px 0;">Your shopping cart is empty</h3>
                    <p style="color: #64748B; max-width: 420px; margin: 0 auto 1.5rem auto;">
                        Explore our comprehensive verified catalog to add craft supplies, automotive goods, and tools.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b2:
                if st.button("🛍️ Browse Product Catalog", use_container_width=True, type="primary"):
                    st.session_state.page = "storefront"
                    st.rerun()
        return

    # Two column layout: Cart Items (left) + Order Summary & Checkout (right)
    col_cart, col_summary = st.columns([3, 2])

    with col_cart:
        st.markdown("### Cart Items")
        subtotal = 0.0

        for title, details in list(cart.items()):
            price = details["price"]
            qty = details["qty"]
            line_total = price * qty
            subtotal += line_total

            with st.container(border=True):
                c_info, c_qty, c_del = st.columns([3, 1, 1])
                with c_info:
                    st.markdown(f"**{title}**")
                    st.markdown(f"<span style='color: #64748B; font-size: 0.85rem;'>${price:.2f} each</span>", unsafe_allow_html=True)
                with c_qty:
                    new_qty = st.number_input(
                        "Qty",
                        min_value=1,
                        max_value=99,
                        value=int(qty),
                        key=f"cart_qty_{title[:20]}",
                        label_visibility="collapsed",
                    )
                    if new_qty != qty:
                        st.session_state.cart[title]["qty"] = new_qty
                        save_cart_csv(st.session_state.cart)
                        st.rerun()
                with c_del:
                    st.markdown(f"<div style='font-weight: 700; color: #0F172A;'>${line_total:.2f}</div>", unsafe_allow_html=True)
                    if st.button("🗑️ Remove", key=f"del_{title[:20]}", help="Remove item from cart"):
                        del st.session_state.cart[title]
                        save_cart_csv(st.session_state.cart)
                        st.rerun()

        # Cart actions row
        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("🗑️ Clear Entire Cart"):
                st.session_state.cart = {}
                save_cart_csv(st.session_state.cart)
                st.rerun()
        with ca2:
            if st.button("⬅ Continue Shopping"):
                st.session_state.page = "storefront"
                st.rerun()

    with col_summary:
        with st.container(border=True):
            st.markdown("### 📋 Order Summary")

            # Coupon Code Section
            st.markdown("#### Promo & Coupon Codes")
            promo_col1, promo_col2 = st.columns([2, 1])
            with promo_col1:
                coupon_input = st.text_input(
                    "Coupon Code",
                    placeholder="e.g. SAVE15, WELCOME10",
                    value=st.session_state.applied_coupon or "",
                    label_visibility="collapsed",
                )
            with promo_col2:
                if st.button("Apply", use_container_width=True):
                    is_valid, msg, discount = validate_coupon(coupon_input, subtotal)
                    if is_valid:
                        st.session_state.applied_coupon = coupon_input.strip().upper()
                        st.session_state.coupon_discount = discount
                        st.success(msg)
                    else:
                        st.session_state.applied_coupon = None
                        st.session_state.coupon_discount = 0.0
                        st.error(msg)

            # Available coupon pills
            st.markdown(
                """
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">
                    Available Codes: <code style="color: #4338CA;">SAVE15</code> (15% off) | <code style="color: #4338CA;">FREESHIP</code> | <code style="color: #4338CA;">WELCOME10</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Financial Calculations
            discount_val = st.session_state.coupon_discount
            if st.session_state.applied_coupon == "SAVE15":
                discount_val = subtotal * 0.15
            elif st.session_state.applied_coupon == "WELCOME10":
                discount_val = subtotal * 0.10

            is_free_ship = (subtotal >= 50.0) or (st.session_state.applied_coupon == "FREESHIP")
            shipping_val = 0.0 if is_free_ship else 5.00
            taxable_amount = max(0.0, subtotal - discount_val)
            tax_val = taxable_amount * 0.07  # 7% standard sales tax
            grand_total = taxable_amount + shipping_val + tax_val

            st.markdown("---")
            st.markdown(
                f"""
                <div style="font-size: 0.95rem; line-height: 2;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Items Subtotal:</span>
                        <strong>${subtotal:.2f}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; color: #166534;">
                        <span>Discount ({st.session_state.applied_coupon or 'None'}):</span>
                        <strong>-${discount_val:.2f}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Estimated Shipping:</span>
                        <strong>{'FREE' if is_free_ship else f'${shipping_val:.2f}'}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Estimated Tax (7%):</span>
                        <strong>${tax_val:.2f}</strong>
                    </div>
                    <hr style="margin: 8px 0; border: none; border-top: 1px solid #CBD5E1;"/>
                    <div style="display: flex; justify-content: space-between; font-size: 1.25rem; font-weight: 800; color: #0F172A;">
                        <span>Grand Total:</span>
                        <span>${grand_total:.2f}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

            # Checkout Expander / Form
            with st.expander("💳 Complete Shipping & Payment (Instant Checkout)", expanded=True):
                user = get_current_user()

                default_name = user["name"] or "Alex Mercer"
                default_email = user["email"] or "alex.mercer@example.com"

                with st.form("checkout_form"):
                    cust_name = st.text_input("Full Name", value=default_name)
                    cust_email = st.text_input("Email Address", value=default_email)
                    shipping_addr = st.text_input("Shipping Address", value="742 Evergreen Terrace, Springfield, OR 97477")
                    payment_method = st.selectbox(
                        "Payment Method",
                        options=[
                            "Credit Card (Visa / Mastercard)",
                            "PayPal Express",
                            "Apple Pay / Google Pay",
                            "Cash on Delivery (COD)",
                        ],
                    )

                    st.markdown("<div style='font-size: 0.78rem; color: #64748B;'>🔒 Secure 256-Bit SSL Mock Checkout. Stock decrements upon placement.</div>", unsafe_allow_html=True)
                    checkout_submitted = st.form_submit_button("🚀 Place Order & Complete Purchase", use_container_width=True, type="primary")

                    if checkout_submitted:
                        if not cust_name.strip() or not shipping_addr.strip():
                            st.error("Please provide both name and shipping address.")
                        else:
                            active_username = user["username"] if user["authenticated"] else "guest_customer"
                            new_oid = create_order(
                                username=active_username,
                                customer_name=cust_name.strip(),
                                email=cust_email.strip(),
                                address=shipping_addr.strip(),
                                payment_method=payment_method,
                                cart=cart,
                                subtotal=subtotal,
                                discount=discount_val,
                                shipping=shipping_val,
                                tax=tax_val,
                                total=grand_total,
                            )
                            # Clear cart
                            st.session_state.cart = {}
                            save_cart_csv(st.session_state.cart)
                            st.session_state.applied_coupon = None
                            st.session_state.coupon_discount = 0.0

                            st.session_state.latest_order_id = new_oid
                            st.session_state.page = "orders"
                            st.success(f"🎉 Order {new_oid} successfully placed!")
                            st.rerun()


# ---------------- ORDERS & TRACKING VIEW ----------------
def render_orders_page():
    """Render customer past order tracking with status timeline."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h2 style="font-weight: 800; color: #1E1B4B; margin: 0;">📦 My Orders & Tracking</h2>
            <p style="color: #64748B; margin: 0;">Track current package delivery progress and review purchase history.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user = get_current_user()
    all_orders = load_orders()

    if all_orders.empty:
        st.info("No orders placed yet.")
        return

    # Filter to user's orders if logged in as customer, else show all
    if user["authenticated"] and user["role"] == "Customer":
        user_orders = all_orders[all_orders["username"] == user["username"]]
    else:
        user_orders = all_orders

    if user_orders.empty:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 2rem; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">📦</div>
                <h4 style="margin: 0 0 6px 0;">No orders found for '{user['name']}'</h4>
                <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 1rem;">You haven't completed any orders yet.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🛍️ Start Shopping Now", type="primary"):
            st.session_state.page = "storefront"
            st.rerun()
        return

    # Highlight latest order banner if recently placed
    if "latest_order_id" in st.session_state and st.session_state.latest_order_id:
        st.balloons()
        st.success(f"🎉 Congratulations! Order **{st.session_state.latest_order_id}** has been confirmed and is being processed by warehouse staff.")
        st.session_state.latest_order_id = None

    for _, ord_row in user_orders.iterrows():
        oid = ord_row["order_id"]
        status = ord_row.get("status", "Pending")

        # Color badges & progress
        if status == "Delivered":
            badge_color = "#10B981"
            progress_pct = 100
        elif status == "Shipped":
            badge_color = "#8B5CF6"
            progress_pct = 75
        elif status == "Processing":
            badge_color = "#3B82F6"
            progress_pct = 40
        else:
            badge_color = "#F59E0B"
            progress_pct = 15

        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            with h1:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: baseline; gap: 12px;">
                        <span style="font-size: 1.15rem; font-weight: 800; color: #1E293B;">Order {oid}</span>
                        <span style="color: #64748B; font-size: 0.85rem;">{ord_row.get('order_date')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with h2:
                st.markdown(
                    f"""
                    <div style="text-align: right;">
                        <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 700;">
                            {status}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Progress bar for fulfillment
            st.progress(progress_pct / 100)

            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748B; margin-top: -8px; margin-bottom: 12px;">
                    <span>Order Placed</span>
                    <span>Processing</span>
                    <span>Shipped & In Transit</span>
                    <span>Delivered</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            d_col1, d_col2 = st.columns([2, 1])
            with d_col1:
                st.markdown(f"**Items:** {ord_row.get('items_summary', 'N/A')}")
                st.markdown(f"**Ship to:** `{ord_row.get('shipping_address', 'N/A')}`")
            with d_col2:
                st.markdown(
                    f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; font-size: 0.85rem;">
                        <div>Subtotal: <strong>${float(ord_row.get('subtotal', 0)):.2f}</strong></div>
                        <div style="color: #166534;">Discount: <strong>-${float(ord_row.get('discount', 0)):.2f}</strong></div>
                        <div style="font-size: 1rem; font-weight: 800; color: #0F172A; margin-top: 4px;">
                            Total: ${float(ord_row.get('total_amount', 0)):.2f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ---------------- MAIN APPLICATION ROUTER ----------------
def main():
    # Render persistent sidebar
    render_sidebar()

    # Render top navbar
    render_navbar()

    # Route based on current page state
    current_page = st.session_state.page

    if current_page in ["login", "signup"]:
        render_auth_page()
    elif current_page == "storefront":
        render_storefront()
    elif current_page == "cart":
        render_cart_page()
    elif current_page == "orders":
        render_orders_page()
    elif current_page == "admin_dashboard":
        user = get_current_user()
        if user["authenticated"] and user["role"] in ["Admin", "Manager"]:
            render_admin_dashboard()
        else:
            st.warning("🔒 Administrative access requires Store Admin or Inventory Lead login.")
            render_auth_page()
    else:
        render_storefront()


if __name__ == "__main__":
    main()
