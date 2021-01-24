import os
from dotenv import load_dotenv
from flaskdemo import create_app


dotenv_path = os.path.join(os.path.dirname(__file__), '.flaskenv')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = create_app('production')

