from supabase import create_client
import os
import sys
from dotenv import load_dotenv

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Carrega o .env corretamente, mesmo no executável
load_dotenv(dotenv_path=resource_path(".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Variáveis SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não foram encontradas no .env.")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
