"""
Authentication and demo credential management for ApexCommerce.
Supports permanent demo credentials as well as temporary runtime signups.
"""
import streamlit as st
import re

# Permanent Demo Accounts with granular roles and profiles
DEMO_USERS = {
    "customer": {
        "password": "customer123",
        "role": "Customer",
        "name": "Alex Mercer",
        "email": "alex.mercer@example.com",
        "title": "Shopper / Retail Customer",
        "badge": "🛒 Customer",
        "description": "Full customer experience: browse catalog, filter, cart, coupon discounts, simulated checkout, and order tracking.",
        "is_temporary": False,
    },
    "admin": {
        "password": "admin123",
        "role": "Admin",
        "name": "Sarah Chen",
        "email": "sarah.admin@apexcommerce.com",
        "title": "Store Administrator & Executive",
        "badge": "👑 Store Admin",
        "description": "Complete administrative access: sales & stock KPI analytics, product CRUD, inventory control, and order fulfillment.",
        "is_temporary": False,
    },
    "manager": {
        "password": "manager123",
        "role": "Manager",
        "name": "Marcus Vance",
        "email": "marcus.stock@apexcommerce.com",
        "title": "Inventory & Warehouse Lead",
        "badge": "📦 Inventory Lead",
        "description": "Warehouse operations: low-stock monitoring, rapid batch replenishment, and inventory audits.",
        "is_temporary": False,
    },
    # Backward compatibility with existing user accounts
    "user1": {
        "password": "user123",
        "role": "Customer",
        "name": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "title": "Customer",
        "badge": "🛒 Customer",
        "description": "Standard retail customer account.",
        "is_temporary": False,
    },
    "user2": {
        "password": "user456",
        "role": "Customer",
        "name": "Taylor Smith",
        "email": "taylor.s@example.com",
        "title": "Customer",
        "badge": "🛒 Customer",
        "description": "Standard retail customer account.",
        "is_temporary": False,
    },
}

# Module-level registry for temporary runtime signups
TEMPORARY_USERS = {}


def get_all_users() -> dict:
    """Return all available users: demo credentials plus runtime registered accounts."""
    all_users = DEMO_USERS.copy()
    all_users.update(TEMPORARY_USERS)
    if "registered_users" in st.session_state and isinstance(st.session_state.registered_users, dict):
        all_users.update(st.session_state.registered_users)
    return all_users


def authenticate(username: str, password: str):
    """Validate username and password against all demo and temporary users."""
    username_clean = username.strip().lower()
    users = get_all_users()
    if username_clean in users:
        user_info = users[username_clean]
        if user_info["password"] == password:
            return user_info
    return None


def register_user(name: str, email: str, username: str, password: str, role: str = "Customer") -> tuple[bool, str, dict]:
    """
    Register a new user temporarily for this session / runtime.
    Returns (success: bool, message: str, user_dict: dict)
    """
    name_clean = name.strip()
    email_clean = email.strip().lower()
    username_clean = username.strip().lower()

    # Validation
    if not name_clean:
        return False, "Full Name cannot be blank.", {}
    if not email_clean or "@" not in email_clean or "." not in email_clean:
        return False, "Please enter a valid email address.", {}
    if not username_clean or len(username_clean) < 3:
        return False, "Username must be at least 3 characters.", {}
    if not re.match(r"^[a-zA-Z0-9_-]+$", username_clean):
        return False, "Username can only contain letters, numbers, hyphens, and underscores.", {}
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters.", {}

    users = get_all_users()
    if username_clean in users:
        return False, f"Username '{username_clean}' is already registered. Please choose another.", {}

    role_badge = "👑 Admin" if role == "Admin" else ("📦 Inventory Lead" if role == "Manager" else "🛒 Customer")

    user_record = {
        "password": password,
        "role": role,
        "name": name_clean,
        "email": email_clean,
        "title": f"Registered {role}",
        "badge": role_badge,
        "description": "Custom user account created during this active session.",
        "is_temporary": True,
    }

    # Store temporarily in module and session state
    TEMPORARY_USERS[username_clean] = user_record
    if "registered_users" in st.session_state:
        st.session_state.registered_users[username_clean] = user_record

    return True, f"Account '{username_clean}' registered successfully!", user_record


def init_auth_state():
    """Ensure authentication keys are initialized in st.session_state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "name" not in st.session_state:
        st.session_state.name = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "registered_users" not in st.session_state:
        st.session_state.registered_users = {}


def login_user(username: str, user_info: dict):
    """Log in the given user and initialize their session."""
    st.session_state.authenticated = True
    st.session_state.username = username.strip().lower()
    st.session_state.role = user_info["role"]
    st.session_state.name = user_info.get("name", username)
    st.session_state.email = user_info.get("email", f"{username}@apexcommerce.com")
    st.session_state.guest_mode = False

    # Set default landing page based on role
    if user_info["role"] in ["Admin", "Manager"]:
        st.session_state.page = "admin_dashboard"
    else:
        st.session_state.page = "storefront"


def logout_user():
    """Clear user session state and return to login screen."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.name = None
    st.session_state.email = None
    st.session_state.page = "login"


def is_authenticated() -> bool:
    """Check if the user is currently authenticated."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict:
    """Return dict of current logged-in user information."""
    return {
        "username": st.session_state.get("username"),
        "role": st.session_state.get("role"),
        "name": st.session_state.get("name"),
        "email": st.session_state.get("email"),
        "authenticated": st.session_state.get("authenticated", False),
    }


def render_demo_credentials_card():
    """Render an interactive demo credentials card with quick 1-click login buttons."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%); 
                    border: 1px solid #C7D2FE; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-size: 1.4rem;">🔑</span>
                <h4 style="margin: 0; color: #3730A3; font-weight: 700;">Demo Login Credentials</h4>
            </div>
            <p style="margin: 0 0 12px 0; font-size: 0.9rem; color: #4338CA;">
                Click any persona below for <strong>instant 1-click access</strong> or use the manual login form:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem; text-align: center; height: 100%;">
                <div style="font-size: 1.5rem;">🛒</div>
                <div style="font-weight: 700; color: #1E293B; font-size: 0.95rem;">Customer</div>
                <div style="font-size: 0.78rem; color: #64748B; margin: 4px 0 8px 0;">Alex Mercer</div>
                <code style="font-size: 0.78rem; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">customer / customer123</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👉 Login as Customer", key="quick_customer", use_container_width=True):
            login_user("customer", DEMO_USERS["customer"])
            st.rerun()

    with col2:
        st.markdown(
            """
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem; text-align: center; height: 100%;">
                <div style="font-size: 1.5rem;">👑</div>
                <div style="font-weight: 700; color: #1E293B; font-size: 0.95rem;">Store Admin</div>
                <div style="font-size: 0.78rem; color: #64748B; margin: 4px 0 8px 0;">Sarah Chen</div>
                <code style="font-size: 0.78rem; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">admin / admin123</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👉 Login as Admin", key="quick_admin", use_container_width=True):
            login_user("admin", DEMO_USERS["admin"])
            st.rerun()

    with col3:
        st.markdown(
            """
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem; text-align: center; height: 100%;">
                <div style="font-size: 1.5rem;">📦</div>
                <div style="font-weight: 700; color: #1E293B; font-size: 0.95rem;">Inventory Lead</div>
                <div style="font-size: 0.78rem; color: #64748B; margin: 4px 0 8px 0;">Marcus Vance</div>
                <code style="font-size: 0.78rem; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">manager / manager123</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👉 Login as Manager", key="quick_manager", use_container_width=True):
            login_user("manager", DEMO_USERS["manager"])
            st.rerun()

    with st.expander("📋 View All Credentials & Permissions Breakdown"):
        st.markdown(
            """
            | Username | Password | Full Name | Role | Primary Permissions |
            | :--- | :--- | :--- | :--- | :--- |
            | `customer` | `customer123` | Alex Mercer | **Customer** | Browse catalog, Filter & Search, Add to Cart, Checkout, Order Tracking |
            | `admin` | `admin123` | Sarah Chen | **Admin** | KPI Metrics, Sales Visualizations, Add/Edit/Delete Products, Order Management |
            | `manager` | `manager123` | Marcus Vance | **Manager** | Inventory Monitoring, Low Stock Restocking, Stock Audits |
            | `user1` | `user123` | Jordan Lee | **Customer** | Standard shopper access |
            | `user2` | `user456` | Taylor Smith | **Customer** | Standard shopper access |
            """
        )


def render_signup_form():
    """Render a dedicated sign-up form allowing new users to create temporary accounts."""
    st.markdown(
        """
        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.3rem;">✨</span>
                <div style="font-weight: 700; color: #166534; font-size: 0.95rem;">Create a Temporary User Account</div>
            </div>
            <div style="font-size: 0.85rem; color: #15803D; margin-top: 4px;">
                Details are stored in-memory for this session so you can immediately explore the portal, checkout, and track orders.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", placeholder="e.g. Jordan Miller")
            email = st.text_input("Email Address *", placeholder="e.g. jordan@example.com")
        with col2:
            username = st.text_input("Choose Username *", placeholder="e.g. jmiller")
            role = st.selectbox(
                "Account Role",
                options=["Customer", "Admin", "Manager"],
                index=0,
                help="Customer allows full shopping and checkout. Admin and Manager allow catalog/stock control.",
            )

        col3, col4 = st.columns(2)
        with col3:
            password = st.text_input("Choose Password *", type="password", placeholder="At least 4 characters")
        with col4:
            confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Repeat password")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Create Account & Enter Portal", use_container_width=True, type="primary")

        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match. Please re-enter.")
            else:
                ok, msg, user_record = register_user(name, email, username, password, role)
                if ok:
                    # Automatically log in the newly registered user
                    login_user(username, user_record)
                    st.success(f"🎉 Welcome, {name}! Your temporary account '{username}' is active.")
                    st.rerun()
                else:
                    st.error(msg)
