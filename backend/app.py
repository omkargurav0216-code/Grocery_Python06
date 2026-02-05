
from db import create_tables
from products import add_product, get_all_products, delete_product, get_product, update_product
from orders import get_all_orders, create_order, get_order_details

import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db import get_connection

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = 'super_secret_key_for_grocery_store_app' # Required for session

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore

# User Model
class User(UserMixin):
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    user_data = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['password_hash'], user_data['role'])
    return None

# Authorization Decorators
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return "403 Forbidden: Admins only", 403
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'customer':
            return "403 Forbidden: Customers only", 403
        return f(*args, **kwargs)
    return decorated_function

create_tables()

def init_db_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if admin exists
    admin_user = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    if not admin_user:
        hashed_password = generate_password_hash("admin123")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ('admin', hashed_password, 'admin'))
        print("Admin user created.")

    # Check if customer exists
    customer_user = conn.execute("SELECT * FROM users WHERE username = 'customer'").fetchone()
    if not customer_user:
        hashed_password = generate_password_hash("custom123")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ('customer', hashed_password, 'customer'))
        print("Customer user created.")

    conn.commit()
    conn.close()

init_db_data()

@app.route("/")
@login_required
def index():
    orders = get_all_orders()
    return render_template("index.html", orders=orders)

@app.route("/products", methods=["GET", "POST"])
@admin_required
def products():
    if request.method == "POST":
        add_product(
            request.form["name"],
            request.form["price"],
            request.form["unit"],
            float(request.form.get("stock", 0)), # type: ignore
            float(request.form.get("discount", 0)) # type: ignore
        )
        return redirect("/products?success=product_added")

    products = get_all_products()
    return render_template("products.html", products=products)

@app.route("/new_order", methods=["GET", "POST"])
@customer_required
def new_order():
    products = get_all_products()

    if request.method == "POST":
        customer_name = request.form["customer_name"]
        customer_address = request.form["customer_address"]

        items = []
        for p in products:
            qty = request.form.get(f"qty_{p['product_id']}")
            if qty and float(qty) > 0:
                items.append({
                    "product_id": p["product_id"],
                    "price": p["price"],
                    "quantity": float(qty)
                })
        
        if not items:
            return render_template(
                "new_order.html", 
                products=products, 
                error="Order cannot be empty. Please select at least one product.",
                customer_name=customer_name,
                customer_address=customer_address
            )

        try:
            create_order(customer_name, customer_address, items)
            return redirect("/?success=new_order")
        except ValueError as e:
            return render_template("new_order.html", products=products, error=str(e))
    
    error = request.args.get("error")
    return render_template("new_order.html", products=products, error=error)

@app.route("/order/<int:order_id>")
@login_required
def order_details(order_id):
    from orders import get_order 
    details = get_order_details(order_id)
    order = get_order(order_id)
    return render_template("order_details.html", details=details, order=order)

@app.route("/delete_product/<int:product_id>")
@admin_required
def remove_product(product_id):
    delete_product(product_id)
    return redirect("/products")

@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    if request.method == "POST":
        update_product(
            product_id,
            request.form["name"],
            request.form["price"],
            request.form["unit"],
            float(request.form.get("stock", 0)),
            float(request.form.get("discount", 0))
        )
        return redirect("/products")

    product = get_product(product_id)
    product = get_product(product_id)
    return render_template("edit_product.html", product=product)

@app.route("/login", methods=["GET", "POST"])
def login():
    role_mode = request.args.get('role')
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_connection()
        user_data = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['password_hash'], user_data['role'])
            login_user(user)
            if user.role == 'admin':
                return redirect("/products")
            else:
                return redirect("/new_order")
        else:
            return render_template("login.html", error="Invalid username or password", is_admin=(role_mode == 'admin'))
            
    return render_template("login.html", is_admin=(role_mode == 'admin'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        conn = get_connection()
        existing_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if existing_user:
            conn.close()
            return render_template("register.html", error="Username already exists")

        password_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       (username, password_hash, 'customer'))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Auto login
        user = User(user_id, username, password_hash, 'customer')
        login_user(user)
        return redirect("/new_order")

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)