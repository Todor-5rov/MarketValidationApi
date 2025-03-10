from flask import Flask
from flask_cors import CORS
from openai import OpenAI
import pandas as pd
from api_routes.api_blueprint import api_bp
#Add all libraries to requirements.txt

from Config.config import Config


pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


app = Flask(__name__)
CORS(app)

#Move this into a separate class config.py



client = OpenAI()
client.api_key = Config.OPENAI_API_KEY

#Move those to separate file bc they are too long and make code hard to read
# System instructions for the OpenAI agent

# -------------------------- Utility Functions --------------------------
#Move these to utility functions file



#Move all api endpoint functions to separate file
#Move all routing to separate file





if __name__ == "__main__":
    app.register_blueprint(api_bp)
    app.run(debug=True)
