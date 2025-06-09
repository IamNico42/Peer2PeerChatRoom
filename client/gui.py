# gui.py – angepasst für PrivateChatSession
import tkinter as tk
from tkinter import messagebox, scrolledtext

class ChatGUI:
    def __init__(self, master, controller):
        self.master = master
        self.controller = controller
        self.build_gui()

    def build_gui(self):
        self.master.title("GroupChat Client")
        self.master.protocol("WM_DELETE_WINDOW", self.controller.on_closing)
        self.server_ip = tk.StringVar()
        self.nickname = tk.StringVar()
        self.server_port = tk.IntVar(value=9000)

        top_frame = tk.Frame(self.master)
        top_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(top_frame, text="Server IP:").pack(side="left")
        tk.Entry(top_frame, textvariable=self.server_ip, width=15).pack(side="left")
        tk.Label(top_frame, text="Port:").pack(side="left")
        tk.Entry(top_frame, textvariable=self.server_port, width=5).pack(side="left")
        tk.Label(top_frame, text="Nickname:").pack(side="left")
        tk.Entry(top_frame, textvariable=self.nickname, width=10).pack(side="left")
        self.connect_button = tk.Button(top_frame, text="Connect", command=self.controller.connect_from_gui)
        self.connect_button.pack(side="left")
        self.disconnect_button = tk.Button(top_frame, text="Disconnect", command=self.controller.disconnect, state="disabled")
        self.disconnect_button.pack(side="left")

        self.status_label = tk.Label(self.master, text="Nicht verbunden", fg="red")
        self.status_label.pack(pady=2)

        self.chat_box = scrolledtext.ScrolledText(self.master, state='disabled', height=10)
        self.chat_box.pack(padx=10, pady=5, fill="both")

        self.input_entry = tk.Entry(self.master)
        self.input_entry.pack(padx=10, fill="x")
        self.input_entry.bind("<Return>", self.controller.send_broadcast_from_gui)

        bottom_frame = tk.Frame(self.master)
        bottom_frame.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(bottom_frame, text="Users:").pack(anchor="w")
        self.user_list = tk.Listbox(bottom_frame)
        self.user_list.bind("<Double-Button-1>", self.controller.handle_user_click)
        self.user_list.pack(fill="both", expand=True)

    def log(self, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + "\n")
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def update_user_list(self, users):
        self.user_list.delete(0, tk.END)
        for entry in users:
            self.user_list.insert(tk.END, entry)

    def show_private_chat(self, session):
        chat_window = tk.Toplevel(self.master)
        chat_window.title(f"Privater Chat mit {session.peer_nick} @ {session.peer_ip}:{session.peer_port}")

        chat_box = scrolledtext.ScrolledText(chat_window, state='disabled', height=10)
        chat_box.pack(padx=10, pady=5, fill="both")

        input_entry = tk.Entry(chat_window)
        input_entry.pack(padx=10, fill="x")

        def log_chat(message):
            chat_box.config(state='normal')
            chat_box.insert(tk.END, message + "\n")
            chat_box.config(state='disabled')
            chat_box.yview(tk.END)

        def send_msg(event=None):
            msg = input_entry.get()
            if msg.strip():
                session.send(msg)
                input_entry.delete(0, tk.END)

        input_entry.bind("<Return>", send_msg)
        chat_window.protocol("WM_DELETE_WINDOW", lambda: (session.close(), chat_window.destroy()))
        session.gui_callback = log_chat
        session.start()
