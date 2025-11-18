import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.constants import *
import os.path
from Home_Page.pagina import Home
from tkinter import *

_location = os.path.dirname(__file__)
from tkinter import messagebox

from Login_Page import loginpage_support

_bgcolor = '#d9d9d9'
_fgcolor = '#000000'
_tabfg1 = 'black' 
_tabfg2 = 'white' 
_bgmode = 'light' 
_tabbg1 = '#d9d9d9' 
_tabbg2 = 'gray40' 

_style_code_ran = 0
def _style_code():
    global _style_code_ran
    if _style_code_ran: return        
    try: loginpage_support.root.tk.call('source',
                os.path.join(_location, 'themes', 'default.tcl'))
    except: pass
    style = ttk.Style()
    style.theme_use('default')
    style.configure('.', font = "TkDefaultFont")
    if sys.platform == "win32":
       style.theme_use('winnative')    
    _style_code_ran = 1

class Login:
    def __init__(self, top=None):
        '''This class configures and populates the toplevel window.
           top is the toplevel containing window.'''

        top.geometry("600x450+729+245")
        top.minsize(120, 1)
        top.maxsize(3844, 1061)
        top.resizable(1,  1)
        top.title("HiMP")
        top.configure(background="#d9d9d9")
        top.configure(highlightbackground="#d9d9d9")
        top.configure(highlightcolor="#000000")

        self.top = top
        self.frame = Frame(self.top)
        self.frame.pack()

        self.menubar = tk.Menu(top,font="TkMenuFont",bg=_bgcolor,fg=_fgcolor)
        top.configure(menu = self.menubar)

        _style_code()
        self.TLabel1 = ttk.Label(self.top)
        self.TLabel1.place(relx=0.333, rely=0.022, height=37, width=194)
        self.TLabel1.configure(font="-family {Arial} -size 14 -weight bold -slant italic -underline 1")
        self.TLabel1.configure(relief="flat")
        self.TLabel1.configure(anchor='w')
        self.TLabel1.configure(justify='left')
        self.TLabel1.configure(text='''How Is My Process?''')
        self.TLabel1.configure(compound='left')
        self.TLabel1.configure(background=_bgcolor)

        self.Labelframe1 = tk.LabelFrame(self.top)
        self.Labelframe1.place(relx=0.3, rely=0.178, relheight=0.611
                , relwidth=0.383)
        self.Labelframe1.configure(relief='groove')
        self.Labelframe1.configure(font="-family {Segoe UI} -size 9")
        self.Labelframe1.configure(foreground="#000000")
        self.Labelframe1.configure(text='''Login''')
        self.Labelframe1.configure(background="#d9d9d9")
        self.Labelframe1.configure(highlightbackground="#d9d9d9")
        self.Labelframe1.configure(highlightcolor="#000000")

        self.username_box = tk.Entry(self.Labelframe1)
        self.username_box.place(relx=0.174, rely=0.291, height=20, relwidth=0.67
                , bordermode='ignore')
        self.username_box.configure(background="white")
        self.username_box.configure(disabledforeground="#a3a3a3")
        self.username_box.configure(font="-family {Courier New} -size 10")
        self.username_box.configure(foreground="#000000")
        self.username_box.configure(highlightbackground="#d9d9d9")
        self.username_box.configure(highlightcolor="#000000")
        self.username_box.configure(insertbackground="#000000")
        self.username_box.configure(selectbackground="#d9d9d9")
        self.username_box.configure(selectforeground="black")
        self.username_box.bind("<Return>", self.login)  
        self.username_box.focus()

        self.Label1 = tk.Label(self.Labelframe1)
        self.Label1.place(relx=0.37, rely=0.182, height=27, width=84
                , bordermode='ignore')
        self.Label1.configure(activebackground="#d9d9d9")
        self.Label1.configure(activeforeground="black")
        self.Label1.configure(anchor='w')
        self.Label1.configure(background="#d9d9d9")
        self.Label1.configure(compound='left')
        self.Label1.configure(disabledforeground="#a3a3a3")
        self.Label1.configure(font="-family {Segoe UI} -size 9")
        self.Label1.configure(foreground="#000000")
        self.Label1.configure(highlightbackground="#d9d9d9")
        self.Label1.configure(highlightcolor="#000000")
        self.Label1.configure(text='''Username''')

        self.Label2 = tk.Label(self.Labelframe1)
        self.Label2.place(relx=0.37, rely=0.436, height=27, width=64
                , bordermode='ignore')
        self.Label2.configure(activebackground="#d9d9d9")
        self.Label2.configure(activeforeground="black")
        self.Label2.configure(anchor='w')
        self.Label2.configure(background="#d9d9d9")
        self.Label2.configure(compound='left')
        self.Label2.configure(disabledforeground="#a3a3a3")
        self.Label2.configure(font="-family {Segoe UI} -size 9")
        self.Label2.configure(foreground="#000000")
        self.Label2.configure(highlightbackground="#d9d9d9")
        self.Label2.configure(highlightcolor="#000000")
        self.Label2.configure(text='''Password''')

        self.password_box = tk.Entry(self.Labelframe1, show='*')
        self.password_box.place(relx=0.174, rely=0.545, height=20, relwidth=0.67
                , bordermode='ignore')
        self.password_box.configure(background="white")
        self.password_box.configure(disabledforeground="#a3a3a3")
        self.password_box.configure(font="-family {Courier New} -size 10")
        self.password_box.configure(foreground="#000000")
        self.password_box.configure(highlightbackground="#d9d9d9")
        self.password_box.configure(highlightcolor="#000000")
        self.password_box.configure(insertbackground="#000000")
        self.password_box.configure(selectbackground="#d9d9d9")
        self.password_box.configure(selectforeground="black")
        self.password_box.bind("<Return>", self.login)

        self.login_button = tk.Button(self.Labelframe1)
        self.login_button.place(relx=0.174, rely=0.691, height=26, width=157
                , bordermode='ignore')
        self.login_button.configure(activebackground="#d9d9d9")
        self.login_button.configure(activeforeground="black")
        self.login_button.configure(background="#d9d9d9")
        self.login_button.configure(disabledforeground="#a3a3a3")
        self.login_button.configure(font="-family {Segoe UI} -size 9")
        self.login_button.configure(foreground="#000000")
        self.login_button.configure(highlightbackground="#d9d9d9")
        self.login_button.configure(highlightcolor="#000000")
        self.login_button.configure(text='''Log In''')
        self.login_button.configure(command=self.login)


    def login(self, event=None):
        user = self.username_box
        password = self.password_box
        if loginpage_support.validar_login(user, password):
            self.frame.destroy()
            Home(self.top)

            





