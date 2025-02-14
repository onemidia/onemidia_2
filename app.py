import os
from dotenv import load_dotenv
from flask import Flask
from database import init_db
from routes import routes

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default_secret_key")

init_db()  # Inicializa o banco

app.register_blueprint(routes)

if __name__ == "__main__":
    app.run(debug=False)  # Evita DEBUG em produção
