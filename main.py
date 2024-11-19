import streamlit as st
from datetime import datetime
import sqlite3
import os
from PIL import Image

# Set page configuration
st.set_page_config(page_title="Lost and Found Item Management System", layout="centered")

# Database connection
conn = sqlite3.connect("lost_and_found.db", check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
c.execute(''' 
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        category TEXT,
        description TEXT,
        date_found TEXT,
        status TEXT,
        photo_path TEXT
    )
''')

c.execute(''' 
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
''')

# Initialize default admin credentials if none exist
c.execute("SELECT * FROM admin")
if not c.fetchall():
    c.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("admin", "admin"))
    conn.commit()

# Function to add item to the database
def add_item(item_name, category, description, photo_path):
    date_found = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(''' 
        INSERT INTO items (item_name, category, description, date_found, status, photo_path) 
        VALUES (?, ?, ?, ?, ?, ?) 
    ''', (item_name, category, description, date_found, "Unclaimed", photo_path))
    conn.commit()
    st.success(f"Item '{item_name}' added successfully!")

# Function to update item status
def update_item_status(item_id, new_status):
    c.execute("UPDATE items SET status = ? WHERE id = ?", (new_status, item_id))
    conn.commit()
    st.success(f"Item ID {item_id} status updated to '{new_status}'!")

# Function to delete an item
def delete_item(item_id):
    c.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    st.success(f"Item ID {item_id} deleted successfully!")

# Function to search items
def search_items(query):
    c.execute("SELECT * FROM items WHERE item_name LIKE ?", ('%' + query + '%',))
    return c.fetchall()

# Function to retrieve all items with sorting
def get_all_items(sort_by="id", ascending=True):
    order = "ASC" if ascending else "DESC"
    c.execute(f"SELECT * FROM items ORDER BY {sort_by} {order}")
    return c.fetchall()

# Function to validate admin login
def validate_admin(username, password):
    c.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

# Function to resize image (smaller size)
def resize_image(image, width=150):
    img = Image.open(image)
    aspect_ratio = img.height / img.width
    height = int(aspect_ratio * width)
    img = img.resize((width, height))
    return img

# Initialize session state if not yet initialized
if "admin_mode" not in st.session_state:
    st.session_state["admin_mode"] = False
if "admin_username" not in st.session_state:
    st.session_state["admin_username"] = ""
if "admin_password" not in st.session_state:
    st.session_state["admin_password"] = ""
if "show_settings" not in st.session_state:
    st.session_state["show_settings"] = False  # Initialize the settings visibility state

# Sidebar Admin Login
st.sidebar.title("🔑 Admin Access")

if not st.session_state["admin_mode"]:
    # Admin login form
    username = st.sidebar.text_input("Username", value=st.session_state["admin_username"])
    password = st.sidebar.text_input("Password", type="password", value=st.session_state["admin_password"])

    if st.sidebar.button("Login"):
        if validate_admin(username, password):
            st.session_state["admin_mode"] = True
            st.session_state["admin_username"] = username
            st.session_state["admin_password"] = password
            st.sidebar.success("Logged in as Admin!")
            st.rerun()  # Force re-render after login
        else:
            st.sidebar.error("Invalid credentials!")
else:
    # Admin mode, Settings & Logout
    st.sidebar.success(f"Logged in as {st.session_state['admin_username']}")
    
    # Toggle settings visibility on button click
    settings_button = st.sidebar.button("⚙️ Settings")
    if settings_button:
        st.session_state["show_settings"] = not st.session_state["show_settings"]  # Toggle settings visibility
    
    # Show settings form if `show_settings` is True
    if st.session_state["show_settings"]:
        with st.sidebar.form(key="admin_form"):
            new_username = st.text_input("New Admin Username", value=st.session_state["admin_username"])
            new_password = st.text_input("New Admin Password", type="password", value=st.session_state["admin_password"])
            submit_button = st.form_submit_button(label="Save Changes")
            if submit_button:
                c.execute("UPDATE admin SET username = ?, password = ? WHERE username = ?", (new_username, new_password, st.session_state["admin_username"]))
                conn.commit()
                st.session_state["admin_username"] = new_username
                st.session_state["admin_password"] = new_password
                st.sidebar.success("Admin credentials updated!")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state["admin_mode"] = False
        st.session_state["admin_username"] = ""
        st.session_state["admin_password"] = ""
        st.session_state["show_settings"] = False  # Hide settings on logout
        st.sidebar.success("Logged out successfully.")
        st.rerun()  # Force re-render after logout

# About section with styling improvements
with st.sidebar.expander("ℹ️ About", expanded=True):
    st.markdown(
        """
        **Lost and Found Item Management System**  
        Created by: **Mark Renier B. Fostanes**

        This project helps manage lost items efficiently, allowing users to log, search, and update the status of found belongings.
        """
    )


# Main Application
st.title("🔍 Lost and Found Item Management System")

if st.session_state["admin_mode"]:
    st.success(f"You are logged in as Admin ({st.session_state['admin_username']}). Admin actions are available.")
    
    # Admin Actions
    st.header("Admin Actions")

    # Hide the "View All Items" section when settings are shown
    if not st.session_state["show_settings"]:
        with st.expander("🔧 Update Item Status"):
            c.execute("SELECT id, item_name FROM items")
            items = c.fetchall()
            if items:
                item_id = st.selectbox("Select Item ID to Update", [item[0] for item in items])
                new_status = st.selectbox("New Status", ["Unclaimed", "Claimed"])
                if st.button("Update Status"):
                    update_item_status(item_id, new_status)
            else:
                st.warning("No items to update. Please add items first.")

        with st.expander("❌ Delete Item"):
            c.execute("SELECT id, item_name FROM items")
            items = c.fetchall()
            if items:
                item_id = st.selectbox("Select Item ID to Delete", [item[0] for item in items])
                if st.button("Delete Item"):
                    delete_item(item_id)
            else:
                st.warning("No items to delete. Please add items first.")

# User Actions
st.header("Actions")
with st.expander("➕ Add a New Item"):
    item_name = st.text_input("Item Name")
    category = st.selectbox("Category", ["Electronics", "Clothing", "Accessories", "Documents", "Other"])
    description = st.text_area("Description")
    photo = st.file_uploader("Upload Photo (Optional)", type=["png", "jpg", "jpeg"])
    photo_path = None
    if photo:
        photo_path = os.path.join("photos", photo.name)
        if not os.path.exists("photos"):
            os.makedirs("photos")
        with open(photo_path, "wb") as f:
            f.write(photo.read())
    if st.button("Add Item"):
        if item_name and category and description:
            add_item(item_name, category, description, photo_path)
        else:
            st.error("Please fill out all fields.")

with st.expander("🔍 Search Items"):
    query = st.text_input("Enter item name or keyword to search")
    if st.button("Search"):
        if query:
            results = search_items(query)
            if results:
                for item in results:
                    item_id, item_name, category, description, date_found, status, photo_path = item
                    st.write(f"**Item Name:** {item_name}")
                    st.write(f"**Category:** {category}")
                    st.write(f"**Description:** {description}")
                    st.write(f"**Date Found:** {date_found}")
                    st.write(f"**Status:** {status}")
                    if photo_path and os.path.exists(photo_path):
                        resized_image = resize_image(photo_path, width=150)  # Resize image to 150px wide
                        st.image(resized_image)
            else:
                st.warning("No items found.")
        else:
            st.warning("Please enter a search query.")

# View All Items Section (only visible when settings are not visible)
if not st.session_state["show_settings"]:
    with st.expander("📋 View All Items"):
        sort_by = st.selectbox("Sort By", ["id", "item_name", "date_found"])
        ascending = st.radio("Sort Order", ["Ascending", "Descending"]) == "Ascending"
        items = get_all_items(sort_by, ascending)
        if items:
            for item in items:
                item_id, item_name, category, description, date_found, status, photo_path = item
                st.write(f"**Item Name:** {item_name}")
                st.write(f"**Category:** {category}")
                st.write(f"**Description:** {description}")
                st.write(f"**Date Found:** {date_found}")
                st.write(f"**Status:** {status}")
                if photo_path and os.path.exists(photo_path):
                    resized_image = resize_image(photo_path, width=150)  # Resize image to 150px wide
                    st.image(resized_image)
        else:
            st.warning("No items available.")

