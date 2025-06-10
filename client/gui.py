# gui.py – angepasst für PrivateChatSession
import tkinter as tk
from .emoji_bar import EmojiBar


class ChatGUI:
    def __init__(self, master, controller):
        self.master = master
        self.controller = controller
        self.build_gui()

    def build_gui(self):
        self.master.title("Peer2Peer Chatroom ✨")
        self.master.geometry("600x500")
        self.master.configure(bg="#23272f")
        self.master.protocol("WM_DELETE_WINDOW", self.controller.on_closing)
        self.server_ip = tk.StringVar(value="127.0.0.1")
        self.nickname = tk.StringVar()
        self.server_port = tk.IntVar(value=9000)

        # --- Top Frame ---
        top_frame = tk.Frame(self.master, bg="#23272f")
        top_frame.pack(padx=15, pady=10, fill="x")
        tk.Label(top_frame, text="Server IP:", bg="#23272f", fg="#b9bbbe").pack(side="left", padx=(0,2))
        tk.Entry(top_frame, textvariable=self.server_ip, width=15, bg="#23272f", fg="#d1d1d1", insertbackground="#d1d1d1", relief="flat").pack(side="left", padx=(0,8))
        tk.Label(top_frame, text="Port:", bg="#23272f", fg="#b9bbbe").pack(side="left")
        tk.Entry(top_frame, textvariable=self.server_port, width=5, bg="#23272f", fg="#d1d1d1", insertbackground="#d1d1d1", relief="flat").pack(side="left", padx=(0,8))
        tk.Label(top_frame, text="Nickname:", bg="#23272f", fg="#b9bbbe").pack(side="left")
        tk.Entry(top_frame, textvariable=self.nickname, width=10, bg="#23272f", fg="#d1d1d1", insertbackground="#d1d1d1", relief="flat").pack(side="left", padx=(0,8))
        self.connect_button = tk.Button(top_frame, text="Connect", command=self.controller.connect_from_gui, bg="#5865f2", fg="#f6f6f6", relief="flat", activebackground="#4048a1")
        self.connect_button.pack(side="left", padx=(0,4))
        self.disconnect_button = tk.Button(top_frame, text="Disconnect", command=self.controller.disconnect, state="disabled", bg="#f04747", fg="#f6f6f6", relief="flat", activebackground="#a03a3a")
        self.disconnect_button.pack(side="left")

        # --- Status ---
        self.status_label = tk.Label(self.master, text="Nicht verbunden", fg="#f04747", bg="#23272f", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(pady=2)

        # --- Chat Box ---
        chat_box_frame = tk.Frame(self.master, bg="#23272f", highlightbackground="#36393f", highlightthickness=2, bd=0)
        chat_box_frame.pack(padx=15, pady=8, fill="both")
        self.chat_box = tk.Text(chat_box_frame, state='disabled', height=12, bg="#23272f", fg="#d1d1d1", insertbackground="#d1d1d1", relief="flat", font=("Consolas", 11), borderwidth=0, highlightthickness=0)
        self.chat_box.pack(fill="both", expand=True)
        # Mausrad-Scrolling aktivieren
        def _on_mousewheel(event):
            self.chat_box.yview_scroll(int(-1*(event.delta/120)), "units")
        self.chat_box.bind("<MouseWheel>", _on_mousewheel)
        self.chat_box.bind("<Button-4>", lambda e: self.chat_box.yview_scroll(-1, "units"))  # Linux
        self.chat_box.bind("<Button-5>", lambda e: self.chat_box.yview_scroll(1, "units"))   # Linux

        # --- Input ---
        input_frame = tk.Frame(self.master, bg="#23272f")
        input_frame.pack(padx=15, pady=(0,8), fill="x")
        input_entry_frame = tk.Frame(input_frame, bg="#23272f", highlightbackground="#36393f", highlightthickness=2, bd=0)
        input_entry_frame.pack(side="left", fill="x", expand=True)
        self.input_entry = tk.Entry(input_entry_frame, bg="#23272f", fg="#d1d1d1", insertbackground="#d1d1d1", relief="flat", font=("Segoe UI", 11), borderwidth=0, highlightthickness=0)
        self.input_entry.pack(fill="x", expand=True, padx=2, pady=2)
        self.input_entry.bind("<Return>", self.controller.send_broadcast_from_gui)
        send_btn = tk.Button(input_frame, text="Senden", command=self.controller.send_broadcast_from_gui, bg="#3ba55d", fg="#f6f6f6", relief="flat", activebackground="#2d7d46")
        send_btn.pack(side="left", padx=(8,0))

        # --- Emoji Bar ---
        self.emoji_bar = EmojiBar(self.master, self.input_entry)
        # Immer gepackt, aber initial Höhe 0 (unsichtbar)
        self.emoji_bar.pack(padx=15, pady=(0, 4), fill="x")
        # self.emoji_bar.set_height(0)  # Entfernen
        self.emoji_bar.clip.configure(height=0)
        self.emoji_bar.visible = False


        self.toggle_emoji_btn = tk.Button(
            input_frame,
            text="😊",
            command=self.emoji_bar.toggle,
            bg="#23272f",
            fg="#f6f6f6",
            relief="flat",
            font=("Segoe UI Emoji", 12),
            activebackground="#36393f"
        )
        self.toggle_emoji_btn.pack(side="left", padx=(6, 0))


        # --- Bottom/Userlist ---
        bottom_frame = tk.Frame(self.master, bg="#23272f")
        bottom_frame.pack(padx=15, pady=5, fill="both", expand=True)
        tk.Label(bottom_frame, text="Users:", bg="#23272f", fg="#b9bbbe", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.user_list = tk.Listbox(bottom_frame, bg="#23272f", fg="#b9bbbe", selectbackground="#36393f", selectforeground="#f6f6f6", relief="flat", font=("Segoe UI", 11))
        self.user_list.bind("<Double-Button-1>", self.controller.handle_user_click)
        self.user_list.pack(fill="both", expand=True, pady=(2,0))

    def log(self, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + "\n")
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def update_user_list(self, users):
        self.user_list.delete(0, tk.END)
        for entry in users:
            self.user_list.insert(tk.END, entry)

    def clear_user_list(self):
        self.user_list.delete(0, tk.END)

    def show_private_chat(self, session):
        chat_window = tk.Toplevel(self.master)
        chat_window.title(f"Privater Chat mit {session.peer_nick} @ {session.peer_ip}:{session.peer_port}")
        chat_window.configure(bg="#23272f")
        chat_window.geometry("500x350")
        chat_window.minsize(350, 200)
        chat_window.rowconfigure(0, weight=1)
        chat_window.rowconfigure(1, weight=0)
        chat_window.columnconfigure(0, weight=1)

        chat_box_frame = tk.Frame(chat_window, bg="#23272f", highlightbackground="#36393f", highlightthickness=2, bd=0)
        chat_box_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=8)
        chat_box_frame.rowconfigure(0, weight=1)
        chat_box_frame.columnconfigure(0, weight=1)
        chat_box = tk.Text(chat_box_frame, state='disabled', height=10, bg="#23272f", fg="#d1d1d1", insertbackground="#d1d1d1", relief="flat", font=("Consolas", 11), borderwidth=0, highlightthickness=0)
        chat_box.grid(row=0, column=0, sticky="nsew")
        # Mausrad-Scrolling aktivieren
        def _on_mousewheel(event):
            chat_box.yview_scroll(int(-1*(event.delta/120)), "units")
        chat_box.bind("<MouseWheel>", _on_mousewheel)
        chat_box.bind("<Button-4>", lambda e: chat_box.yview_scroll(-1, "units"))  # Linux
        chat_box.bind("<Button-5>", lambda e: chat_box.yview_scroll(1, "units"))   # Linux

        input_frame = tk.Frame(chat_window, bg="#23272f")
        input_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0,2))
        input_frame.columnconfigure(0, weight=1)
        input_entry_frame = tk.Frame(input_frame, bg="#23272f", highlightbackground="#36393f", highlightthickness=2, bd=0)
        input_entry_frame.grid(row=0, column=0, sticky="ew")
        input_entry_frame.columnconfigure(0, weight=1)
        input_entry = tk.Entry(input_entry_frame, bg="#23272f", fg="#d1d1d1", insertbackground="#d1d1d1", relief="flat", font=("Segoe UI", 11), borderwidth=0, highlightthickness=0)
        input_entry.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        def send_msg(event=None):
            msg = input_entry.get()
            if msg.strip():
                session.send(msg)
                input_entry.delete(0, tk.END)

        send_btn = tk.Button(input_frame, text="Senden", command=send_msg, bg="#3ba55d", fg="#f6f6f6", relief="flat", activebackground="#2d7d46")
        send_btn.grid(row=0, column=1, padx=(8,0))

        # --- Emoji Bar für Private Chat ---
        emoji_bar = EmojiBar(chat_window, input_entry)
        emoji_bar.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 4))
        emoji_bar.set_height(0)
        toggle_emoji_btn = tk.Button(
            input_frame,
            text="😊",
            command=emoji_bar.toggle,
            bg="#23272f",
            fg="#f6f6f6",
            relief="flat",
            font=("Segoe UI Emoji", 12),
            activebackground="#36393f"
        )
        toggle_emoji_btn.grid(row=0, column=2, padx=(6, 0))


        def log_chat(message):
            chat_box.config(state='normal')
            chat_box.insert(tk.END, message + "\n")
            chat_box.config(state='disabled')
            chat_box.yview(tk.END)

        input_entry.bind("<Return>", send_msg)
        chat_window.protocol("WM_DELETE_WINDOW", lambda: (session.close(), chat_window.destroy()))
        session.gui_callback = log_chat
        session.start()

    def show_dark_popup(self, title, message, yes_text="Annehmen", no_text="Ablehnen"):
        popup = tk.Toplevel(self.master)
        popup.title(title)
        popup.configure(bg="#23272f")
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self.master)
        popup.geometry("350x150")
        # Center popup
        popup.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (350 // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (150 // 2)
        popup.geometry(f"350x150+{x}+{y}")

        label = tk.Label(popup, text=message, bg="#23272f", fg="#f6f6f6", font=("Segoe UI", 11), wraplength=320, justify="center")
        label.pack(pady=(30, 20), padx=20)

        btn_frame = tk.Frame(popup, bg="#23272f")
        btn_frame.pack(pady=(0, 10))
        result = {"value": None}

        def on_yes():
            result["value"] = True
            popup.destroy()
        def on_no():
            result["value"] = False
            popup.destroy()

        yes_btn = tk.Button(btn_frame, text=yes_text, width=10, command=on_yes, bg="#3ba55d", fg="#f6f6f6", relief="flat", activebackground="#2d7d46", font=("Segoe UI", 10, "bold"))
        yes_btn.pack(side="left", padx=10)
        no_btn = tk.Button(btn_frame, text=no_text, width=10, command=on_no, bg="#36393f", fg="#f6f6f6", relief="flat", activebackground="#23272f", font=("Segoe UI", 10))
        no_btn.pack(side="left", padx=10)

        popup.bind("<Return>", lambda e: on_yes())
        popup.bind("<Escape>", lambda e: on_no())
        yes_btn.focus_set()
        popup.wait_window()
        return result["value"]
