from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

access = os.getenv('ACCESS_KEY')
secret = os.getenv('SECRET_TOKEN')
cloudflare_api_token = os.getenv('CLOUDFLARE_API_TOKEN')
