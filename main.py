import streamlit as st
from datetime import datetime
import sqlite3
import os
from PIL import Image

# Set page configuration
st.set_page_config(page_title="Lost and Found Item Management System", layout="wide")

# Database connection
conn = sqlite3.connect("lost_and_found.db", check_same_thread=False)
c = conn.cursor()

# Create tables
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
    CREATE TABLE IF not EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
''')

# Initialize credentials 
c.execute("SELECT * FROM admin")
if not c.fetchall():
    c.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("admin", "admin")) #default
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

# Function to resize image into smaller size
def resize_image(image, width=150): 
    img = Image.open(image)
    aspect_ratio = img.height / img.width
    height = int(aspect_ratio * width)
    img = img.resize((width, height))
    return img

# Sidebar Admin Login
st.sidebar.title("🔑 Admin Access")

if 'admin_mode' not in st.session_state:
    st.session_state['admin_mode'] = False

if 'username' not in st.session_state:
    st.session_state['username'] = ''

if not st.session_state["admin_mode"]:
    # Admin login form
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if validate_admin(username, password):
            st.session_state["admin_mode"] = True
            st.session_state["username"] = username  
            st.sidebar.success(f"Logged in as Admin ({username}).")
            st.rerun()  
        else:
            st.sidebar.error("Invalid credentials!")
else:
    # Admin mode, Settings & Logout
    username = st.session_state["username"]  
    st.sidebar.success(f"Logged in as Admin ({username})")
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state["admin_mode"] = False
        st.session_state["username"] = ''  # Clear username from session_state
        st.sidebar.success("Logged out successfully.")
        st.rerun()  

    # Settings Button (add this code after the logout button)
    if 'settings_visible' not in st.session_state:
        st.session_state['settings_visible'] = False  # Initial state of settings panel

    # Toggle settings panel visibility
    if st.sidebar.button("Settings"):
        st.session_state['settings_visible'] = not st.session_state['settings_visible']

    # Show settings form if toggled
    if st.session_state['settings_visible']:
        st.sidebar.markdown("""<hr style="border-top: 1px solid #3498db; margin-top: 20px;">""", unsafe_allow_html=True)
        st.sidebar.markdown("<h3 style='text-align: center;'>⚙️Edit Admin Credentials</h3>", unsafe_allow_html=True)
        
        new_username = st.sidebar.text_input("New Username", value=username)
        new_password = st.sidebar.text_input("New Password", type="password")
        
        if st.sidebar.button("Save"):
            # Update credentials in the database
            c.execute("UPDATE admin SET username = ?, password = ? WHERE id = 1", (new_username, new_password))
            conn.commit()
            st.session_state["username"] = new_username  # Update session state with new username
            st.sidebar.success("Admin credentials updated successfully!")

# About section 
with st.sidebar.expander("ℹ️ About", expanded=True):
    st.markdown(
        """
        <div style="text-align: justify;">
        <strong>Lost and Found Item Management System</strong><br>
        Created by: <strong><span style="font-weight: bold; color: #1E90FF;">Mark Renier B. Fostanes</strong></span><br><br>

        A simple and efficient system to manage lost and found items. Quickly log, search, and update 
        item statuses with ease. Stay organized and connect lost items with their rightful owners. 
        Efficiency, simplicity, and ease of use.
        </div>
        """, unsafe_allow_html=True
    )

# Centered Content 
st.title("🔍 Lost and Found Item Management System")

if 'action' not in st.session_state:
    st.session_state['action'] = "Add Item"  

# CSS for styling 
st.markdown("""
<style>
    .action-button {
        font-size: 18px;
        cursor: pointer;
        padding: 8px;
        margin-right: 20px;
        transition: all 0.3s ease-in-out;
    }

    .action-button:hover {
        color: #3498db;
        text-decoration: underline;
    }

    .selected {
        color: #3498db;
        font-weight: bold;
        text-decoration: underline;
    }

    /* Underline between buttons and content */
    .underline {
        border-bottom: 2px solid #3498db;
        margin-top: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Action buttons with Markdown 
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("➕ Add Item", key="add_item"):
        st.session_state['action'] = "Add Item"
with col2:
    if st.button("🔎 Search Items", key="search_items"):
        st.session_state['action'] = "Search Items"
with col3:
    if st.button("👀 View All Items", key="view_all_items"):
        st.session_state['action'] = "View All Items"
with col4:
    if st.session_state["admin_mode"] and st.button("🔓 Admin Actions"):
        st.session_state['action'] = "Admin Actions"




# Add underline below the action buttons
st.markdown('<div class="underline"></div>', unsafe_allow_html=True)

if st.session_state['action'] == "Add Item":
    st.markdown("<h3 style='text-align: center;'>Add Item</h3>", unsafe_allow_html=True) #add line below buttons

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

elif st.session_state['action'] == "Search Items":
    st.markdown("<h3 style='text-align: center;'>Search Items</h3>", unsafe_allow_html=True)
    query = st.text_input("Enter item name or keyword to search")
    if st.button("Search"):
        if query:
            results = search_items(query)
            if results:
                for item in results:
                    item_id, item_name, category, description, date_found, status, photo_path = item

                    # Create two columns for the layout
                    col1, col2 = st.columns([3, 1]) 

                    with col1:
                        # Display the item's details
                        st.write(f"**Item Name:** {item_name}")
                        st.write(f"**Category:** {category}")
                        st.write(f"**Description:** {description}")
                        st.write(f"**Date Found:** {date_found}")
                        st.write(f"**Status:** {status}")

                    with col2:
                        # Display the item's photo
                        if photo_path and os.path.exists(photo_path):
                            img = resize_image(photo_path, width=150)  
                            st.image(img, use_container_width=False)
            else:
                st.write("No items found.")
        else:
            st.warning("Please enter a search query.")


elif st.session_state['action'] == "View All Items":
    st.markdown("<h3 style='text-align: center;'>All Found Items</h3>", unsafe_allow_html=True)

    # Sorting Options with SelectBox
    sort_by = st.selectbox(
        "Sort Items By:",
        options=["ID", "Item Name", "Date Found"],
        index=0,  # Default to the first option
    )

    # Map SelectBox values to actual sorting keys
    sort_key_mapping = {
        "ID": "id",
        "Item Name": "item_name",
        "Date Found": "date_found",
    }

    # Sort the item based on selected sorting choices
    selected_sort_key = sort_key_mapping[sort_by]
    try:
        items = get_all_items(sort_by=selected_sort_key, ascending=True)
        if items:
            for item in items:
                item_id, item_name, category, description, date_found, status, photo_path = item

                # Display item details
                st.markdown("---")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(
                    f"<span style='color: cyan; font-weight: bold; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>Item ID:</span> {item_id}",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<span style='color: cyan; font-weight: bold; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>Item Name:</span> {item_name}",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<span style='color: cyan; font-weight: bold; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>Category:</span> {category}",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<span style='color: cyan; font-weight: bold; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>Description:</span> {description}",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<span style='color: cyan; font-weight: bold; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>Date Found:</span> {date_found}",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<span style='color: cyan; font-weight: bold; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>Status:</span> {status}",
                    unsafe_allow_html=True
                )

                with col2:
                    if photo_path and os.path.exists(photo_path):
                        img = resize_image(photo_path, width=300)
                        st.image(img, use_container_width=False)
        else:
            st.write("No items found.")
    except sqlite3.OperationalError as e:
        st.error(f"Error fetching items: {e}")



elif st.session_state['action'] == "Admin Actions":
    st.markdown("<h3 style='text-align: center;'>Admin Actions</h3>", unsafe_allow_html=True)

    action_choice = st.selectbox("Choose Action", ["Update Item Status", "Delete Item"])

    if action_choice == "Update Item Status":
        # Display a dropdown list of all items
        items = get_all_items(sort_by="id", ascending=True)
        item_options = [f"{item[1]} (ID: {item[0]})" for item in items]  
        selected_item = st.selectbox("Select Item to Update", item_options)
        item_id = int(selected_item.split(" (ID: ")[1][:-1])  

        # Display item details
        c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = c.fetchone()
        if item:
            item_name, category, description, date_found, status, photo_path = item[1:]
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Item Name:** {item_name}")
                st.write(f"**Category:** {category}")
                st.write(f"**Description:** {description}")
                st.write(f"**Date Found:** {date_found}")
                st.write(f"**Status:** {status}")
            with col2:
                if photo_path and os.path.exists(photo_path):
                    img = resize_image(photo_path, width=150)  
                    st.image(img, use_container_width=False)
            
            new_status = st.selectbox("Select New Status", ["Unclaimed", "Claimed", "Returned"])
            if st.button("Update Status"):
                update_item_status(item_id, new_status)
        else:
            st.warning("Item ID not found.")
        
    elif action_choice == "Delete Item":
        # Display a dropdown list of all items
        items = get_all_items(sort_by="id", ascending=True)
        item_options = [f"{item[1]} (ID: {item[0]})" for item in items] 
        selected_item = st.selectbox("Select Item to Delete", item_options)
        item_id = int(selected_item.split(" (ID: ")[1][:-1])  

        # Fetch item details for preview
        c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = c.fetchone()
        if item:
            item_name, category, description, date_found, status, photo_path = item[1:]
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Item Name:** {item_name}")
                st.write(f"**Category:** {category}")
                st.write(f"**Description:** {description}")
                st.write(f"**Date Found:** {date_found}")
                st.write(f"**Status:** {status}")
            with col2:
                if photo_path and os.path.exists(photo_path):
                    img = resize_image(photo_path, width=150)
                    st.image(img, use_container_width=False)
                
            confirm_delete = st.checkbox("Are you sure you want to delete this item?")
            if confirm_delete and st.button("Delete Item"):
                delete_item(item_id)
        else:
            st.warning("Item ID not found.")
