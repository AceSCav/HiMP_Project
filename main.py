import tkinter as tk
from Login_Page import loginpage



def main():
    root = tk.Tk()
    app = loginpage.Login(root)
    root.mainloop()

if __name__ == "__main__":
    main()
