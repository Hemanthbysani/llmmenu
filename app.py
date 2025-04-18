from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt  # Ensure this is from the pyjwt library
import datetime
import json
import re
import os
from functools import wraps
import litellm  
from litellm.caching.caching import Cache
from sqlalchemy import func  


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure litellm
litellm.set_verbose = True

# Configure the database URI and initialize SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Menu model
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    ingredients = db.Column(db.String(200))

    def __repr__(self):
        return f"<MenuItem {self.name}>"

# Define the Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    special_instructions = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=1)
    order_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    menu_item = db.relationship('MenuItem', backref=db.backref('orders', lazy=True))

    def __repr__(self):
        return f"<Order {self.table_number} - {self.menu_item.name}>"

# Define the Admin model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define the OrderHistory model
class OrderHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    order_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<OrderHistory {self.table_number} - {self.item_name}>"

# Define the ChatMessage model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.String(500), nullable=False)
    bot_response = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resulted_in_order = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<ChatMessage {self.id}>"

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('admin_login'))
        try:
            jwt.decode(token, app.secret_key, algorithms=["HS256"])
        except:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# Route for the landing page
@app.route('/')
def index():
    return render_template('llmenu_start.html')

# Route for the menu page
@app.route('/menu')
def menu():
    items = MenuItem.query.all()
    return render_template('menu.html', items=items)

# Route for the AI assistant menu after table number is provided
@app.route('/', methods=['POST'])
def set_table():
    if request.method == 'POST':
        table_number = request.form.get('table_number')
        if table_number:
            # Store table number in session
            session['table_number'] = table_number
            return redirect(url_for('llmenu'))
    return redirect(url_for('index'))

# Route for the llmenu page
@app.route('/llmenu')
def llmenu():
    table_number = session.get('table_number')
    if not table_number:
        return redirect(url_for('index'))
    items = MenuItem.query.all()
    return render_template('llmenu.html', items=items, table_number=table_number)

# Route for the admin login page
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            token = jwt.encode({'user': admin.username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.secret_key, algorithm="HS256")
            response = redirect(url_for('admin'))
            response.set_cookie('token', token)
            return response
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

# Route for the admin page
@app.route('/admin')
@token_required
def admin():
    items = MenuItem.query.all()
    orders = Order.query.all()
    return render_template('admin.html', items=items, orders=orders)

# Route to logout admin
@app.route('/admin_logout', methods=['POST'])
@token_required
def admin_logout():
    response = redirect(url_for('admin_login'))
    response.set_cookie('token', '', expires=0)
    return response

# Route to add/edit menu items
@app.route('/add_item', methods=['POST'])
@token_required
def add_item():
    name = request.form['name']
    price = request.form['price']
    ingredients = request.form['ingredients']
    
    new_item = MenuItem(name=name, price=price, ingredients=ingredients)
    db.session.add(new_item)
    db.session.commit()

    return redirect(url_for('admin'))

# Route to edit a menu item
@app.route('/edit_item/<int:id>', methods=['POST'])
@token_required
def edit_item(id):
    item = MenuItem.query.get(id)
    item.name = request.form['name']
    item.price = request.form['price']
    item.ingredients = request.form['ingredients']
    db.session.commit()
    return redirect(url_for('admin'))

# Route to handle deleting menu items
@app.route('/delete_item/<int:id>', methods=['POST'])
@token_required
def delete_item(id):
    item = MenuItem.query.get(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin'))

# Route to handle orders
@app.route('/order', methods=['POST'])
def order():
    item_ids = request.form.getlist('item')
    quantities = [int(request.form[f'quantity_{item_id}']) for item_id in item_ids]
    table_number = request.form['table_number']
    special_instructions = request.form.get('special_instructions', '')

    # Add the orders to the database
    for item_id, quantity in zip(item_ids, quantities):
        menu_item = MenuItem.query.get(item_id)
        new_order = Order(table_number=table_number, item_id=item_id, special_instructions=special_instructions, quantity=quantity, order_time=datetime.datetime.now())
        db.session.add(new_order)
        # Add to order history
        order_history = OrderHistory(
            table_number=table_number,
            item_name=menu_item.name,
            quantity=quantity,
            total_cost=menu_item.price * quantity,
            order_time=new_order.order_time
        )
        db.session.add(order_history)
    db.session.commit()

    # Return a success response
    return jsonify({'message': 'Order placed successfully!'})

# Route for the kitchen page
@app.route('/kitchen')
@token_required
def kitchen():
    orders = Order.query.all()
    grouped_orders = {}
    for order in orders:
        table_number = order.table_number
        if table_number not in grouped_orders:
            grouped_orders[table_number] = []
        grouped_orders[table_number].append(order)
    return render_template('kitchen.html', grouped_orders=grouped_orders)

# Route to clear kitchen orders
@app.route('/clear_orders', methods=['POST'])
@token_required
def clear_orders():
    Order.query.delete()
    db.session.commit()
    return redirect(url_for('kitchen'))

# Route for the orders page
@app.route('/orders')
def orders():
    orders = Order.query.all()
    grouped_orders = {}
    for order in orders:
        table_number = order.table_number
        if table_number not in grouped_orders:
            grouped_orders[table_number] = []
        grouped_orders[table_number].append(order)
    return render_template('orders.html', grouped_orders=grouped_orders)

# Route to delete an order
@app.route('/delete_order/<int:id>', methods=['POST'])
@token_required
def delete_order(id):
    order = Order.query.get(id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('orders'))

# API endpoint to handle chat messages
@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    table_number = session.get('table_number')
    
    # Get menu items for context
    menu_items = MenuItem.query.all()
    menu_context = "\n".join([f"\n {item.name}: ${item.price}" for item in menu_items])
    
    # Prepare the prompt with the menu context
    system_message = f"""You are a restaurant ordering chatbot. Help users order food from our menu. 
Here's our current menu:
{menu_context}

The user is at table number: {table_number}

When a user wants to place an order:
1. Identify the items they want and ask for the quantity for each item.
2. Use the table number {table_number} that's already provided.
3. Once the user confirms the order, respond with "ORDER_CONFIRMED" followed by a JSON object only with the order details.
4. Do not ask for confirmation again after the user has already confirmed the order.
5. If the user provides special instructions, include them in the JSON object.
6. After confirming the order, provide a final response indicating the order has been placed successfully and stop further order-taking unless the user explicitly starts a new order.

If the user asks for their orders:
1. Retrieve the orders placed for their table number.
2. Respond with a summary of the items ordered, their quantities, and the total cost.

########################################
Sample JSON format for a confirmed order:

ORDER_CONFIRMED
{{
"items": [
  {{"name": "Item Name", "quantity": 2}},
  {{"name": "Another Item", "quantity": 1}}
],
"table_number": {table_number},
"special_instructions": "Extra spicy"
}}

"""
    try:
        # Call the LLM using litellm
        response = litellm.completion(
            model="groq/llama-3.3-70b-versatile", # or any other model supported by litellm
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            caching=True
        )
        
        bot_response = response['choices'][0]['message']['content']
        
        # Check if the response contains ORDER_CONFIRMED
        if "ORDER_CONFIRMED" in bot_response:
            try:
                # Extract the JSON part
                json_str = re.search(r'\{.*\}', bot_response, re.DOTALL).group()
                order_data = json.loads(json_str)
                
                # Ensure we have the table number
                if not order_data.get('table_number'):
                    order_data['table_number'] = table_number
                
                # Process the order
                process_llm_order(order_data)
                
                # Send a confirmation back to the user
                bot_response = "Your order has been placed successfully! It will be prepared shortly."
            except Exception as e:
                print(f"Order processing error: {str(e)}")  # Add logging for debugging
                bot_response = f"I couldn't process your order. Please try again. Error: {str(e)}"
        
        # Add logic to handle queries about placed orders
        if "What are my orders" in user_message or "orders" in user_message:
            try:
                # Retrieve orders for the current table number
                orders = Order.query.filter_by(table_number=table_number).all()
                if not orders:
                    bot_response = f"No orders found for table {table_number}."
                else:
                    order_summary = []
                    total_cost = 0
                    for order in orders:
                        item_name = order.menu_item.name
                        quantity = order.quantity
                        cost = order.menu_item.price * quantity
                        total_cost += cost
                        order_summary.append(f"- {item_name}: {quantity} (${cost:.2f})")
                    
                    order_details = "\n".join(order_summary)
                    bot_response = f"Here are your orders for table {table_number}:\n{order_details}\nTotal cost: ${total_cost:.2f}"
            except Exception as e:
                print(f"Error retrieving orders: {str(e)}")  # Add logging for debugging
                bot_response = f"Sorry, I couldn't retrieve your orders. Please try again later."

            # Save the chat message
            chat_message = ChatMessage(
                user_message=user_message, 
                bot_response=bot_response,
                resulted_in_order=False
            )
            db.session.add(chat_message)
            db.session.commit()
            
            return jsonify({'response': bot_response})

        # Save the chat message
        resulted_in_order = "ORDER_CONFIRMED" in bot_response
        chat_message = ChatMessage(
            user_message=user_message, 
            bot_response=bot_response,
            resulted_in_order=resulted_in_order
        )
        db.session.add(chat_message)
        db.session.commit()
        
        return jsonify({'response': bot_response})
    
    except Exception as e:
        print(f"Chat API error: {str(e)}")  # Add logging for debugging
        return jsonify({'response': f"Sorry, I encountered an error: {str(e)}"})

def process_llm_order(order_data):
    """Process the order data from the LLM and save to database"""
    # Make sure we have valid data
    if not order_data:
        raise ValueError("Empty order data received")
        
    table_number = order_data.get('table_number')
    special_instructions = order_data.get('special_instructions', '')
    items = order_data.get('items', [])
    
    print(f"Processing order: Table #{table_number}, Items: {json.dumps(items)}")  # Debug log
    
    if not table_number or not items:
        raise ValueError("Missing table number or items in order data")
    
    orders_created = 0
    
    for item_data in items:
        item_name = item_data.get('name')
        quantity = item_data.get('quantity', 1)
        
        if not item_name:
            print(f"Skipping item with no name: {item_data}")
            continue
            
        # Find the menu item by name - try multiple matching strategies
        print(f"Looking for menu item: '{item_name}'")
        item_name_clean = item_name.lower().strip()
        
        # Strategy 1: Exact match after lowercase & trim
        menu_item = MenuItem.query.filter(func.lower(MenuItem.name) == item_name_clean).first()
        
        # Strategy 2: Contains match after lowercase & trim
        if not menu_item:
            menu_item = MenuItem.query.filter(func.lower(MenuItem.name).contains(item_name_clean)).first()
        
        # Strategy 3: Word by word matching for longer words
        if not menu_item:
            for word in item_name_clean.split():
                if len(word) > 3:  # Only use words longer than 3 chars to avoid matching on "the", "and", etc.
                    menu_item = MenuItem.query.filter(func.lower(MenuItem.name).contains(word)).first()
                    if menu_item:
                        print(f"Found menu item via word match: {menu_item.name}")
                        break
        
        # If we found a matching menu item
        if menu_item:
            print(f"Matched '{item_name}' to menu item: {menu_item.name}")
            
            # Create new order
            new_order = Order(
                table_number=table_number, 
                item_id=menu_item.id, 
                special_instructions=special_instructions, 
                quantity=quantity, 
                order_time=datetime.datetime.utcnow()
            )
            db.session.add(new_order)
            
            # Add to order history
            order_history = OrderHistory(
                table_number=table_number,
                item_name=menu_item.name,
                quantity=quantity,
                total_cost=menu_item.price * quantity,
                order_time=datetime.datetime.utcnow()  # Use current time directly
            )
            db.session.add(order_history)
            orders_created += 1
        else:
            print(f"No menu item match found for: '{item_name}'")
    
    # Only commit if we actually created orders
    if orders_created > 0:
        print(f"Successfully created {orders_created} orders")
        db.session.commit()
    else:
        print("No orders created - likely due to item matching failure")
        raise ValueError(f"No valid menu items found in the order. Items requested: {[item.get('name') for item in items]}")

# Add a route to view chat history in admin
@app.route('/admin/chats')
@token_required
def admin_chats():
    chats = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).all()
    return render_template('admin_chats.html', chats=chats)

# Initialize the database (create tables)
def create_tables():
    with app.app_context():
        db.create_all()
        # Create a default admin user if not exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin')
            admin.set_password('admin')  # Set the admin password here
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5002)
