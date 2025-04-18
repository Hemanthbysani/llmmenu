# Restaurant AI Assistant

This project is a restaurant management system that integrates an AI-powered chatbot to assist customers in placing orders. It also includes features for menu management, order tracking, and admin functionalities.

## Features

- **AI Chatbot**: Helps customers place orders and provides menu recommendations.
- **Menu Management**: Admins can add, edit, and delete menu items.
- **Order Tracking**: View and manage orders in real-time.
- **Kitchen Dashboard**: Displays grouped orders for the kitchen staff.
- **Chat History**: Admins can view chat logs to analyze customer interactions.
- **Authentication**: Secure admin login with JWT-based authentication.

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **AI Integration**: `litellm` library for LLM-based chatbot functionality.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/llmmenu.git
   cd llmmenu
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**:
   Update the `GEMINI_API_KEY` and `GROQ_API_KEY` in the `.env` file with your API keys.

5. **Initialize the Database**:
   ```bash
   python app.py
   ```
   This will create the database and a default admin user (`username: admin`, `password: admin`).

6. **Run the Application**:
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5002`.

## Usage

### Customer Workflow

1. **Landing Page**: Customers enter their table number to start interacting with the AI assistant.
2. **AI Assistant**: The chatbot helps customers place orders or inquire about the menu.
3. **Menu Page**: Customers can view the traditional menu and place orders manually.

### Admin Workflow

1. **Login**: Admins log in using their credentials.
2. **Menu Management**: Add, edit, or delete menu items.
3. **Order Management**: View and delete orders.
4. **Kitchen Dashboard**: View grouped orders for preparation.
5. **Chat History**: Analyze customer interactions with the chatbot.

## File Structure

```
llmmenu/
├── app.py                 # Main application file
├── templates/             # HTML templates
│   ├── admin.html         # Admin dashboard
│   ├── admin_chats.html   # Chat history page
│   ├── admin_login.html   # Admin login page
│   ├── edit_item.html     # Edit menu item page
│   ├── kitchen.html       # Kitchen dashboard
│   ├── llmenu.html        # AI assistant page
│   ├── llmenu_start.html  # Landing page
│   ├── menu.html          # Traditional menu page
│   ├── orders.html        # Orders page
├── static/                # Static files (CSS, JS)
│   ├── style.css          # Global styles
│   ├── script.js          # Global JavaScript
│   ├── llmenu.css         # Styles for AI assistant
│   ├── llmenu.js          # JavaScript for AI assistant
├── restaurant.db          # SQLite database (auto-generated)
└── README.md              # Project documentation
```

## API Endpoints

### Public Endpoints

- `GET /`: Landing page.
- `POST /`: Set table number and redirect to AI assistant.
- `GET /menu`: View the traditional menu.
- `POST /order`: Place an order.

### Admin Endpoints

- `GET /admin_login`: Admin login page.
- `POST /admin_login`: Authenticate admin.
- `GET /admin`: Admin dashboard.
- `POST /add_item`: Add a new menu item.
- `POST /edit_item/<id>`: Edit an existing menu item.
- `POST /delete_item/<id>`: Delete a menu item.
- `GET /kitchen`: View kitchen orders.
- `POST /clear_orders`: Clear all kitchen orders.
- `GET /orders`: View all orders.
- `POST /delete_order/<id>`: Delete an order.
- `GET /admin/chats`: View chat history.

### Chat API

- `POST /api/chat`: Handle customer messages and respond using the AI assistant.

## Default Admin Credentials

- **Username**: `admin`
- **Password**: `admin`

## Customization

- **AI Model**: Update the `model` parameter in the `litellm.completion` call in `app.py` to use a different LLM.
- **Database**: Replace SQLite with another database by updating the `SQLALCHEMY_DATABASE_URI` in `app.py`.

## Screenshots

### Landing Page
![Landing Page](screenshots/landing_page.png)

### AI Assistant
![AI Assistant](screenshots/ai_assistant.png)

### Admin Dashboard
![Admin Dashboard](screenshots/admin_dashboard.png)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, please contact 
