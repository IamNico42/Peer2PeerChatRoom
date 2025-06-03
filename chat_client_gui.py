import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from protocol import build_message, parse_message
import queue

def choose_udp_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class ChatClientGUI:
    def __init__(self, master):
        
        self.master = master
        self.master.title("GroupChat Client")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)


        self.server_ip = tk.StringVar()
        self.nickname = tk.StringVar()
        self.server_port = tk.IntVar(value=9000)
        self.udp_port = None

        self.sock = None
        self.udp_sock = None
        self.running = False
        self.chat_requests = queue.Queue()

        self.build_gui()


    def apply_dark_theme(self):
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#cba6f7"
        entry_bg = "#313244"  # leicht hellerer Ton

        self.master.configure(bg=bg)

        self.status_label.configure(bg=bg, fg=fg)
        self.chat_box.configure(bg=bg, fg=fg, insertbackground=fg, selectbackground=accent)
        self.input_entry.configure(bg=entry_bg, fg=fg, insertbackground=fg)
        self.user_list.configure(bg=bg, fg=fg, selectbackground=accent)

        # Alle Entry-Felder oben
        for child in self.master.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=bg)
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, tk.Entry):
                        grandchild.configure(bg=entry_bg, fg=fg, insertbackground=fg)
                    elif isinstance(grandchild, tk.Label):
                        grandchild.configure(bg=bg, fg=fg)

        self.connect_button.configure(bg=accent, fg="black", activebackground="#f5c2e7")
        self.disconnect_button.configure(bg="#f38ba8", fg="black", activebackground="#fab387")



    def build_gui(self):
        top_frame = tk.Frame(self.master)
        top_frame.pack(padx=10, pady=5, fill="x")
        top_frame.configure(bg="#1e1e2e")



        tk.Label(top_frame, text="Server IP:").pack(side="left")
        tk.Entry(top_frame, textvariable=self.server_ip, width=15).pack(side="left")

        tk.Label(top_frame, text="Port:").pack(side="left")
        tk.Entry(top_frame, textvariable=self.server_port, width=5).pack(side="left")

        tk.Label(top_frame, text="Nickname:").pack(side="left")
        tk.Entry(top_frame, textvariable=self.nickname, width=10).pack(side="left")

        self.connect_button = tk.Button(top_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(side="left")

        self.disconnect_button = tk.Button(top_frame, text="Disconnect", command=self.disconnect_from_server, state="disabled")
        self.disconnect_button.pack(side="left")


        self.status_label = tk.Label(self.master, text="Nicht verbunden", fg="red")
        self.status_label.pack(pady=2)

        self.chat_box = scrolledtext.ScrolledText(
            self.master,
            state='disabled',
            height=10,
            bg="#1e1e2e",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            selectbackground="#cba6f7"
        )

        self.chat_box.pack(padx=10, pady=5, fill="both")

        self.input_entry = tk.Entry(self.master)
        self.input_entry.pack(padx=10, fill="x")
        self.input_entry.bind("<Return>", self.send_broadcast)

        bottom_frame = tk.Frame(self.master)
        bottom_frame.pack(padx=10, pady=5, fill="both", expand=True)
        bottom_frame.configure(bg="#1e1e2e")

        tk.Label(bottom_frame, text="Users:").pack(anchor="w")
        self.user_list = tk.Listbox(
            bottom_frame,
            bg="#1e1e2e",
            fg="#cdd6f4",
            selectbackground="#cba6f7"
        )

        self.user_list.pack(fill="both", expand=True)
        self.user_list.bind("<Double-Button-1>", self.handle_user_click)

        self.master.after(1000, self.check_chat_requests)
        self.apply_dark_theme()


    def log(self, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + "\n")
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def connect_to_server(self):
        if not self.server_ip.get() or not self.nickname.get():
            messagebox.showerror("Fehler", "Bitte Server-IP und Nickname eingeben.")
            return
        if self.running:
            self.log("[INFO] Bereits verbunden – mehrfaches Verbinden nicht erlaubt.")
            return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip.get(), self.server_port.get()))

            self.udp_port = choose_udp_port()
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.bind(('0.0.0.0', self.udp_port))

            self.sock.sendall(build_message("REGISTER", self.nickname.get(), str(self.udp_port)).encode())

            # Warte synchron auf erste Antwort
            buffer = ""
            while True:
                data = self.sock.recv(1024).decode()
                if not data:
                    raise Exception("Keine Antwort vom Server.")
                buffer += data
                if "\n" in buffer:
                    break

            line, buffer = buffer.split("\n", 1)
            cmd, args = parse_message(line)

            if cmd == "ERROR":
                self.sock.close()
                self.sock = None
                messagebox.showerror("Fehler", f"Serverfehler: {args[0]}")
                return

            elif cmd == "WELCOME":
                self.running = True
                self.status_label.config(text="Verbunden", fg="green")
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.log(f"[SERVER]: Willkommen, {args[0]}")

                # Jetzt Threads starten
                threading.Thread(target=self.receive_loop, daemon=True).start()
                threading.Thread(target=self.listen_udp, daemon=True).start()
            else:
                raise Exception("Unerwartete Serverantwort.")

        except Exception as e:
            messagebox.showerror("Fehler", f"Verbindung fehlgeschlagen: {e}")
            self.sock = None
            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")


    def receive_loop(self):
        buffer = ""
        # Neu
        while self.sock:
            try:
                data = self.sock.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    cmd, args = parse_message(line)
                    if cmd == "WELCOME":
                        self.running = True
                        self.log(f"[SERVER]: Willkommen, {args[0]}")
                    elif cmd == "BROADCAST_MSG":
                        sender, msg = args[0], " ".join(args[1:])
                        self.log(f"[{sender}]: {msg}")
                    elif cmd == "USERLIST":
                        self.user_list.delete(0, tk.END)
                        for entry in args:
                            nick, ip, udp = entry.split(":")
                            if nick != self.nickname.get():
                                self.user_list.insert(tk.END, f"{nick}:{ip}:{udp}")
                    elif cmd == "USER_JOINED":
                        nick, ip, udp = args
                        if nick != self.nickname.get():
                            self.user_list.insert(tk.END, f"{nick}:{ip}:{udp}")
                        self.log(f"[INFO] {nick} ist beigetreten")
                    elif cmd == "USER_LEFT":
                        left_nick = args[0]
                        for i in range(self.user_list.size()):
                            if self.user_list.get(i).startswith(left_nick + ":"):
                                self.user_list.delete(i)
                                break
                        self.log(f"[INFO] {left_nick} hat den Chat verlassen")
                    elif cmd == "ERROR":
                        self.log(f"[SERVER FEHLER] {args[0]}")
                        try:
                            self.sock.shutdown(socket.SHUT_RDWR)
                            self.sock.close()
                        except:
                            pass
                        self.running = False
                        self.sock = None
                        self.status_label.config(text="Verbindung abgelehnt", fg="red")
                        self.connect_button.config(state="normal")
                        self.disconnect_button.config(state="disabled")
                        return

            except:
                break

    def listen_udp(self):
        while True:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                parts = data.decode().split()
                cmd = parts[0]
                if cmd == "CHAT_REQUEST":
                    port = int(parts[1])
                    self.chat_requests.put((addr[0], port))
                elif cmd == "CHAT_REJECTED":
                    self.log("[INFO] Chat-Anfrage wurde abgelehnt.")
            except OSError:
                break

    def check_chat_requests(self):
        while not self.chat_requests.empty():
            ip, port = self.chat_requests.get()
            if messagebox.askyesno("Chat-Anfrage", f"{ip} möchte mit dir chatten. Annehmen?"):
                try:
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((ip, port))
                    conn.sendall(self.nickname.get().encode()) # Sende Nickname
                    peer_nickname = conn.recv(1024).decode().strip()
                    
                    self.start_direct_chat(conn, peer_ip=ip, peer_port=port, peer_nickname=peer_nickname)
                except Exception as e:
                    self.log(f"[FEHLER] Verbindung fehlgeschlagen: {e}")
            else:
                reply = "CHAT_REJECTED".encode()
                self.udp_sock.sendto(reply, (ip, port))
        self.master.after(1000, self.check_chat_requests)

    def handle_user_click(self, event):
        selection = self.user_list.get(tk.ACTIVE)
        try:
            nick, ip, udp = selection.split(":")
            udp_port = int(udp)
            self.send_chat_request(ip, udp_port, nick)
        except:
            messagebox.showerror("Fehler", "Ungültiger Eintrag in der Userliste.")

    def send_chat_request(self, target_ip, target_udp_port, target_nick):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', 0))
        server.listen(1)
        tcp_port = server.getsockname()[1]
        threading.Thread(target=self.accept_chat, args=(server, target_nick), daemon=True).start()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            msg = f"CHAT_REQUEST {tcp_port}".encode()
            s.sendto(msg, (target_ip, target_udp_port))
            self.log(f"[INFO] Chat-Anfrage an {target_ip}:{target_udp_port} gesendet")

    def accept_chat(self, server_sock, expected_nick=None):
        server_sock.settimeout(10)
        try:
            conn, addr = server_sock.accept()

            peer_nickname = conn.recv(1024).decode().strip()
            conn.sendall(self.nickname.get().encode())

            self.start_direct_chat(conn, peer_ip=addr[0], peer_port=addr[1], peer_nickname=peer_nickname)
            
        except socket.timeout:
            self.log("[INFO] Deine Chat-Anfrage wurde nicht beantwortet.")
        finally:
            server_sock.close()

    def start_direct_chat(self, conn, peer_ip="Unbekannt", peer_port=None, peer_nickname="Unbekannt"):
        chat_window = tk.Toplevel(self.master)
        chat_window.title(f"Privater Chat mit {peer_nickname} @ {peer_ip}:{peer_port}")

        chat_box = scrolledtext.ScrolledText(chat_window, state='disabled', height=10)
        chat_box.pack(padx=10, pady=5, fill="both")

        input_entry = tk.Entry(chat_window)
        input_entry.pack(padx=10, fill="x")

        stop_event = threading.Event()

        def log_chat(msg):
            chat_box.config(state='normal')
            chat_box.insert(tk.END, msg + "\n")
            chat_box.config(state='disabled')
            chat_box.yview(tk.END)

        def recv_loop():
            while not stop_event.is_set():
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    decoded = data.decode().strip()
                    if decoded == "[DISCONNECT]":
                        log_chat(f"[INFO] {peer_nickname} hat den Chat beendet.")
                        messagebox.showinfo("Verbindung beendet", f"{peer_nickname} hat den Chat verlassen.")
                        break
                    log_chat(f"[{peer_nickname} @ {peer_ip}:{peer_port}]: {decoded}")
                except:
                    break
            stop_event.set()
            conn.close()
            try:
                chat_window.destroy()
            except:
                pass


        def send_msg(event=None):
            msg = input_entry.get()
            if msg.lower() in ("exit", "quit"):
                try:
                    conn.sendall("[DISCONNECT]\n".encode())
                except:
                    pass
                chat_window.destroy()
                return
            conn.sendall((msg + "\n").encode())
            log_chat(f"[{self.nickname.get()}]: {msg}")
            input_entry.delete(0, tk.END)

        input_entry.bind("<Return>", send_msg)
        chat_window.protocol("WM_DELETE_WINDOW", lambda: (
            stop_event.set(),
            conn.sendall("[DISCONNECT]\n".encode()),
            conn.close(),
            chat_window.destroy()
        ))

        threading.Thread(target=recv_loop, daemon=True).start()

    def send_broadcast(self, event=None):
        message = self.input_entry.get().strip()
        if message and self.sock:
            self.sock.sendall(build_message("BROADCAST", self.nickname.get(), message).encode())
            self.log(f"[{self.nickname.get()}]: {message}")
            self.input_entry.delete(0, tk.END)
    
    def disconnect_from_server(self):
        if self.running:
            try:
                self.sock.sendall(build_message("QUIT").encode())
            except:
                pass
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
            try:
                self.udp_sock.close()
            except:
                pass
            self.running = False
            self.sock = None
            self.udp_sock = None
            self.status_label.config(text="Nicht verbunden", fg="red")
            self.log("[SYSTEM] Verbindung getrennt")

        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")

    def on_closing(self):
        self.disconnect_from_server()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()
