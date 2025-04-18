from flask import Flask

app = Flask(__name__, template_folder='../templates')

from app.routes import pnp_handlers
