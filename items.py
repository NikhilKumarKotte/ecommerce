"""
Product catalog, search, multi-faceted filtering, and product card display for ApexCommerce.
"""
import math
import streamlit as st
import pandas as pd
from data_manager import load_items, load_categories, save_cart_csv

# Category icon mapping for rich visual cues
CATEGORY_ICONS = {
    "Beading & Jewelry Making": "💎",
    "Fabric Decorating": "🎨",
    "Knitting & Crochet Supplies": "🧶",
    "Printmaking Supplies": "🖨️",
    "Scrapbooking & Stamping Supplies": "📜",
    "Sewing Products": "🧵",
    "Craft & Hobby Fabric": "✂️",
    "Needlework Supplies": "🪡",
    "Arts, Crafts & Sewing Storage": "📦",
    "Painting, Drawing & Art Supplies": "🖌️",
    "Craft Supplies & Materials": "🛠️",
    "Gift Wrapping Supplies": "🎁",
    "Party Decorations": "🎉",
    "Automotive Paint & Paint Supplies": "🚗",
    "Heavy Duty & Commercial Vehicle Equipment": "🚚",
    "Automotive Tires & Wheels": "🛞",
    "Automotive Tools & Equipment": "🔧",
    "Automotive Performance Parts & Accessories": "🏎️",
    "Car Care": "🧼",
    "Beauty & Personal Care": "✨",
    "Makeup": "💄",
}


def get_category_icon(cat_name: str) -> str:
    """Return icon matching the category name or fallback."""
    for key, icon in CATEGORY_ICONS.items():
        if key.lower() in cat_name.lower():
            return icon
    return "🛍️"


def render_star_rating(rating: float) -> str:
    """Format star rating with filled/empty stars."""
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return "★" * full + ("½" if half else "") + "☆" * empty


def render_storefront():
    """Main customer storefront view with search, filters, and product grid."""
    items_df = load_items()
    cats_df = load_categories()

    # ---- STORE HEADER & BANNER ----
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
                    border-radius: 16px; padding: 1.8rem 2rem; color: white; margin-bottom: 1.5rem;
                    box-shadow: 0 4px 20px -2px rgba(67, 56, 202, 0.25);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <span style="background: rgba(255,255,255,0.18); padding: 4px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">
                        ⚡ Verified Merchant Catalog
                    </span>
                    <h1 style="color: white; margin: 10px 0 6px 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.5px;">
                        Explore Premium Supplies & Inventory
                    </h1>
                    <p style="color: #C7D2FE; margin: 0; font-size: 1rem; max-width: 650px;">
                        Browse verified items across crafts, automotive, studio equipment, and retail goods with real-time stock sync.
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.25); border-radius: 12px; padding: 12px 18px; text-align: right;">
                    <div style="font-size: 0.8rem; color: #E0E7FF; font-weight: 500;">SPECIAL OFFER</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #FDE047;">Use code SAVE15</div>
                    <div style="font-size: 0.75rem; color: #C7D2FE;">15% OFF your next order</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- FILTER CONTROLS & SEARCH BAR ----
    with st.container():
        col_search, col_sort = st.columns([3, 1])

        with col_search:
            search_query = st.text_input(
                "🔍 Search products by name, keyword, or category...",
                placeholder="e.g. Elastic cord, Fabric markers, Acrylic, Keychain...",
                label_visibility="collapsed",
            )

        with col_sort:
            sort_by = st.selectbox(
                "Sort by:",
                options=[
                    "Featured / Best Sellers",
                    "Price: Low to High",
                    "Price: High to Low",
                    "Highest Rated",
                    "Most Reviews",
                ],
                label_visibility="collapsed",
            )

    # Detailed filter expander
    with st.expander("⚙️ Refine Search & Filters (Category, Price Range, Stock, Rating)", expanded=False):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            cat_list = ["All Categories"] + sorted(items_df["category_name"].dropna().unique().tolist())
            selected_cat = st.selectbox("Category", options=cat_list)

        with f_col2:
            min_price = float(items_df["price"].min())
            max_price = float(items_df["price"].max())
            selected_price = st.slider(
                "Max Price ($)",
                min_value=min_price,
                max_value=max(100.0, max_price),
                value=max(100.0, max_price),
                step=5.0,
            )

        with f_col3:
            rating_choice = st.selectbox(
                "Minimum Rating",
                options=["Any Rating", "4.0★ & above", "4.5★ & above", "4.8★ & above"],
            )

        with f_col4:
            st.write("Availability & Badges")
            in_stock_only = st.checkbox("In-Stock Only", value=False)
            bestseller_only = st.checkbox("Best Sellers Only", value=False)

    # ---- APPLY FILTERS ----
    filtered_df = items_df.copy()

    # Search filter
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["title"].str.lower().str.contains(q, na=False)
            | filtered_df["category_name"].str.lower().str.contains(q, na=False)
        ]

    # Category filter
    if selected_cat != "All Categories":
        filtered_df = filtered_df[filtered_df["category_name"] == selected_cat]

    # Price filter
    filtered_df = filtered_df[filtered_df["price"] <= selected_price]

    # Rating filter
    if rating_choice == "4.0★ & above":
        filtered_df = filtered_df[filtered_df["stars"] >= 4.0]
    elif rating_choice == "4.5★ & above":
        filtered_df = filtered_df[filtered_df["stars"] >= 4.5]
    elif rating_choice == "4.8★ & above":
        filtered_df = filtered_df[filtered_df["stars"] >= 4.8]

    # In stock filter
    if in_stock_only:
        filtered_df = filtered_df[filtered_df["stock"] > 0]

    # Best seller filter
    if bestseller_only:
        filtered_df = filtered_df[filtered_df["isBestSeller"] == True]

    # Sorting
    if sort_by == "Featured / Best Sellers":
        filtered_df = filtered_df.sort_values(by=["isBestSeller", "stars", "reviews"], ascending=[False, False, False])
    elif sort_by == "Price: Low to High":
        filtered_df = filtered_df.sort_values(by="price", ascending=True)
    elif sort_by == "Price: High to Low":
        filtered_df = filtered_df.sort_values(by="price", ascending=False)
    elif sort_by == "Highest Rated":
        filtered_df = filtered_df.sort_values(by=["stars", "reviews"], ascending=[False, False])
    elif sort_by == "Most Reviews":
        filtered_df = filtered_df.sort_values(by="reviews", ascending=False)

    total_results = len(filtered_df)

    # ---- RESULTS SUMMARY & QUICK COUNTS ----
    c_meta, c_cart_btn = st.columns([3, 1])
    with c_meta:
        st.markdown(
            f"<div style='color: #64748B; font-size: 0.95rem; margin-bottom: 12px;'>"
            f"Showing <strong>{total_results}</strong> products matching your criteria"
            f"{f' in <em>{selected_cat}</em>' if selected_cat != 'All Categories' else ''}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c_cart_btn:
        cart_count = sum(item["qty"] for item in st.session_state.cart.values())
        if st.button(f"🧺 View Cart ({cart_count})", use_container_width=True, key="view_cart_top"):
            st.session_state.page = "cart"
            st.rerun()

    if total_results == 0:
        st.info("No products match your current search or filter combination. Try loosening the filters.")
        return

    # ---- PAGINATION ----
    items_per_page = 12
    total_pages = max(1, math.ceil(total_results / items_per_page))

    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    # Keep page in bounds
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = 1

    curr_p = st.session_state.current_page
    start_idx = (curr_p - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = filtered_df.iloc[start_idx:end_idx]

    # ---- PRODUCT GRID (3 COLUMNS) ----
    cols = st.columns(3)

    for idx, (_, row) in enumerate(page_items.iterrows()):
        col = cols[idx % 3]
        with col:
            render_product_card(row)

    # ---- PAGINATION BAR ----
    if total_pages > 1:
        st.markdown("---")
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if st.button("⬅ Previous Page", disabled=(curr_p <= 1), use_container_width=True):
                st.session_state.current_page -= 1
                st.rerun()
        with p_col2:
            st.markdown(
                f"<div style='text-align: center; color: #475569; font-weight: 600; padding-top: 8px;'>"
                f"Page {curr_p} of {total_pages} ({total_results} total items)"
                f"</div>",
                unsafe_allow_html=True,
            )
        with p_col3:
            if st.button("Next Page ➡", disabled=(curr_p >= total_pages), use_container_width=True):
                st.session_state.current_page += 1
                st.rerun()


def render_product_card(row: pd.Series):
    """Render an individual interactive modern product card."""
    title = str(row["title"])
    price = float(row["price"])
    stars = float(row.get("stars", 4.5))
    reviews = int(row.get("reviews", 0))
    stock = int(row.get("stock", 15))
    is_bestseller = bool(row.get("isBestSeller", False))
    cat_name = str(row.get("category_name", "General Merchandise"))
    icon = get_category_icon(cat_name)

    # Stock badge styling
    if stock <= 0:
        stock_badge = '<span style="background: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 999px; font-size: 0.72rem; font-weight: 700;">🔴 Out of Stock</span>'
        is_disabled = True
    elif stock <= 5:
        stock_badge = f'<span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 999px; font-size: 0.72rem; font-weight: 700;">🟡 Low Stock ({stock} left)</span>'
        is_disabled = False
    else:
        stock_badge = f'<span style="background: #DCFCE7; color: #166534; padding: 2px 8px; border-radius: 999px; font-size: 0.72rem; font-weight: 700;">🟢 In Stock ({stock})</span>'
        is_disabled = False

    bestseller_badge = (
        '<span style="background: #FEF08A; color: #854D0E; padding: 2px 8px; border-radius: 999px; font-size: 0.72rem; font-weight: 700;">🔥 Best Seller</span>'
        if is_bestseller
        else ""
    )

    card_container = st.container(border=True)
    with card_container:
        # Badges row
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div>{bestseller_badge}</div>
                <div>{stock_badge}</div>
            </div>
            <div style="font-size: 2.2rem; margin: 4px 0; text-align: center;">{icon}</div>
            <div style="font-size: 0.75rem; color: #6366F1; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">{cat_name[:28]}</div>
            <h4 style="margin: 0 0 8px 0; font-size: 0.98rem; font-weight: 700; color: #1E293B; height: 44px; overflow: hidden; text-overflow: ellipsis; line-height: 1.35;" title="{title}">
                {title[:65]}{'...' if len(title) > 65 else ''}
            </h4>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                <span style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">${price:.2f}</span>
                <span style="font-size: 0.8rem; color: #D97706; font-weight: 600;">
                    {render_star_rating(stars)} <span style="color: #64748B; font-weight: 400;">({reviews:,})</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Quantity and Add to Cart action row
        act_col1, act_col2 = st.columns([1, 2])
        qty_key = f"qty_{title[:20]}_{row.name}"
        cart_key = f"add_{title[:20]}_{row.name}"

        with act_col1:
            max_qty = max(1, min(10, stock)) if stock > 0 else 1
            chosen_qty = st.number_input(
                "Qty",
                min_value=1,
                max_value=max_qty,
                value=1,
                step=1,
                key=qty_key,
                disabled=is_disabled,
                label_visibility="collapsed",
            )

        with act_col2:
            btn_label = "➕ Add to Cart" if not is_disabled else "Out of Stock"
            if st.button(btn_label, key=cart_key, disabled=is_disabled, use_container_width=True):
                # Calculate currently in cart
                curr_in_cart = st.session_state.cart.get(title, {}).get("qty", 0)
                if curr_in_cart + chosen_qty > stock:
                    st.error(f"Cannot add {chosen_qty}. Only {stock - curr_in_cart} available!")
                else:
                    if title not in st.session_state.cart:
                        st.session_state.cart[title] = {"price": price, "qty": chosen_qty}
                    else:
                        st.session_state.cart[title]["qty"] += chosen_qty
                    save_cart_csv(st.session_state.cart)
                    st.toast(f"✅ Added {chosen_qty}x '{title[:25]}...' to cart!", icon="🛒")
                    st.rerun()

        # Quick View details expander
        with st.expander("🔍 Quick Details"):
            st.markdown(
                f"""
                - **Full Title:** {title}
                - **Category:** {cat_name}
                - **Unit Price:** ${price:.2f}
                - **Warehouse Stock:** {stock} units
                - **Rating:** {stars} / 5.0 ({reviews:,} verified ratings)
                - **Status:** {'Best Selling Item' if is_bestseller else 'Regular Catalog Item'}
                """
            )
