import tkinter as tk
from tkinter import messagebox
import sys
import os
from database import supabase

# Para importar database.py que está na pasta pai
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def validar_login(username_box, password_box):
    # Validação do campo NIF
    nif = username_box.get().strip()  # Remove espaços em branco
    
    if not nif:  # Se o campo estiver vazio
        messagebox.showerror("Erro", "Por favor, insira um NIF válido.")
        username_box.focus_set()  # Coloca o foco de volta no campo
        return False
    
    try:
        # Verifica se o NIF contém apenas números
        nif_int = int(nif)
    except ValueError:
        messagebox.showerror("Erro", "O NIF deve conter apenas números.")
        username_box.focus_set()
        return False
    
    # Validação da senha
    senha = password_box.get()
    if not senha:
        messagebox.showerror("Erro", "Por favor, insira sua senha.")
        password_box.focus_set()
        return False

    try:
        response = supabase.table("users").select("*").eq("nif", nif).maybe_single().execute()

        if response is None or response.data is None:
            messagebox.showerror("Erro de login", "NIF não encontrado.")
            return False
        
        user = response.data

        if user["password"] == senha:
            return True
        else:
            messagebox.showerror("Erro de login", "Senha incorreta.")
            return False

    except Exception as e:
        messagebox.showerror("Erro", f"Erro no sistema: {str(e)}")
        return False

