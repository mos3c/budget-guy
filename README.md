Budget Guy API

A Django REST Framework (DRF) backend for managing budgets, transactions, categories, and investments.
Fully equipped with analytics endpoints and designed for integration with a frontend (React, Vue, etc.).

📦 Features

    User Authentication: Register, Login, Logout using JWT tokens.
    
    Categories: Create and manage transaction categories.
    
    Transactions: CRUD operations for income and expenses.
  
    Budgets: Track budget allocations and usage.
    
    Investments: Track stocks, crypto, real estate, and other investments.

Analytics Endpoints:

    Dashboard summary
    
    Monthly summary
    
    Category breakdown
    
    Investment performance
    
    Budget progress
    
🛠 Tech Stack

    Backend: Python 3.x, Django, Django REST Framework
    
    Database: PostgreSQL
    
    Authentication: JWT (via djangorestframework-simplejwt)

🚀 Getting Started (Locally)

Clone the repository

    git clone https://github.com/your-username/budget-backend.git
    cd budget-backend


Create a virtual environment

    python -m venv venv
    source venv/bin/activate   # Linux/Mac
    venv\Scripts\activate      # Windows


Install dependencies

    pip install -r requirements.txt


Set environment variables
Create a .env file or set variables for:

    SECRET_KEY=<your-django-secret-key>
    DEBUG=True
    DATABASE_URL=postgres://user:password@host:5432/dbname


Run migrations

    python manage.py migrate


Start local server

    python manage.py runserver


Access API locally

    http://127.0.0.1:8000/
