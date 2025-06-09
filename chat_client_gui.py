import socket
import threading
from time import sleep
import tkinter as tk
from tkinter import messagebox, scrolledtext
from protocol import Protocol
import queue
from datetime import datetime





class UDPPortChooser:
    @staticmethod
    def choose():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

class TCPReceiverThread(threading.Thread):
    def __init__(self, sock, callback):
        super().__init__(daemon=True)
        self.sock = sock
        self.callback = callback
        self.running = True

    def run(self):
        buffer = b""
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                buffer += data
                messages, buffer = Protocol.decode_stream(buffer)
                for payload in messages:
                    cmd, args = Protocol.extract_command(payload)
                    self.callback(cmd, args)
            except:
                break

    def stop(self):
        self.running = False

class UDPListenerThread(threading.Thread):
    def __init__(self, udp_sock, callback):
        super().__init__(daemon=True)
        self.udp_sock = udp_sock
        self.callback = callback
        self.running = True

    def run(self):
        while self.running:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                print(f"[Debug] [UDP RAW] empfangen von {addr}: {data}")
                cmd, args = Protocol.extract_udp_message(data)
                self.callback(cmd, addr, args)
            except OSError:
                break

    def stop(self):
        self.running = False

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

        self.tcp_thread = None
        self.udp_thread = None

        self.chat_requests = queue.Queue()

        self.build_gui()
        self.master.after(1000, self.check_chat_requests)

    def build_gui(self):
        top_frame = tk.Frame(self.master)
        top_frame.pack(padx=10, pady=5, fill="x")

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

        self.chat_box = scrolledtext.ScrolledText(self.master, state='disabled', height=10)
        self.chat_box.pack(padx=10, pady=5, fill="both")

        self.input_entry = tk.Entry(self.master)
        self.input_entry.pack(padx=10, fill="x")
        self.input_entry.bind("<Return>", self.send_broadcast)

        bottom_frame = tk.Frame(self.master)
        bottom_frame.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(bottom_frame, text="Users:").pack(anchor="w")
        self.user_list = tk.Listbox(bottom_frame)
        self.user_list.bind("<Double-Button-1>", self.handle_user_click)
        self.user_list.pack(fill="both", expand=True)

    def handle_user_click(self, event):
        selection = self.user_list.get(tk.ACTIVE)
        try:
            nick, ip, udp = selection.split(":")
            udp_port = int(udp)
            self.send_chat_request(ip, udp_port, nick)
        except:
            messagebox.showerror("Fehler", "Ungültiger Eintrag in der Userliste.")

    def log(self, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + "\n")
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def current_time(self):
        return datetime.now().strftime("%H:%M")

    def connect_to_server(self):
        if not self.server_ip.get() or not self.nickname.get():
            messagebox.showerror("Fehler", "Bitte Server-IP und Nickname eingeben.")
            return
        if self.running:
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip.get(), self.server_port.get()))
            self.udp_port = UDPPortChooser.choose()
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.bind(('0.0.0.0', self.udp_port))

            self.sock.sendall(Protocol.register(self.nickname.get(), str(self.udp_port)))

            buffer = b""
            while True:
                data = self.sock.recv(1024)
                if not data:
                    raise Exception("Keine Antwort vom Server.")
                buffer += data
                messages, buffer = Protocol.decode_stream(buffer)
                if messages:
                    cmd, args = Protocol.extract_command(messages[0])
                    break

            if cmd == "WELCOME":
                self.own_nickname = args[0]
                self.running = True
                self.status_label.config(text="Verbunden", fg="green")
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.tcp_thread = TCPReceiverThread(self.sock, self.handle_tcp_command)
                self.tcp_thread.start()
                self.udp_thread = UDPListenerThread(self.udp_sock, self.handle_udp_command)
                self.udp_thread.start()
            elif cmd == "ERROR":
                messagebox.showerror("Fehler", f"Serverfehler: {' '.join(args)}")
                self.sock.close()
                self.sock = None

        except Exception as e:
            messagebox.showerror("Fehler", f"Verbindung fehlgeschlagen: {e}")
            self.sock = None

    def handle_tcp_command(self, cmd, args):
        if cmd == "BROADCAST":
            sender, msg = Protocol.read_broadcast(args)
            self.log(f"[{sender}]: {msg}")
        elif cmd == "USERLIST":
            entries = Protocol.read_user_list(args)
            self.user_list.delete(0, tk.END)
            for entry in entries:
                nick, _, _ = entry.split(":")
                if nick != self.own_nickname:
                    self.user_list.insert(tk.END, entry)
        elif cmd == "USER_JOINED":
            nick, ip, udp = Protocol.read_user_joined(args)
            if nick != self.own_nickname:
                self.user_list.insert(tk.END, f"{nick}:{ip}:{udp}")
            self.log(f"[INFO] {nick} ist beigetreten")
        elif cmd == "USER_LEFT":
            left_nick = Protocol.read_user_left(args)
            for i in range(self.user_list.size()):
                if self.user_list.get(i).startswith(left_nick + ":"):
                    self.user_list.delete(i)
                    break
            self.log(f"[INFO] {left_nick} hat den Chat verlassen")
        elif cmd == "ERROR":
            reason = Protocol.read_error(args)
            self.log(f"[SERVER FEHLER] {reason}")

    def handle_udp_command(self, cmd, addr, args):
        if cmd == "CHAT_REQUEST":
            try:
                port = Protocol.read_chat_request(args)
                self.chat_requests.put((addr[0], port))
                self.log(f"[UDP] Chat-Anfrage von {addr[0]}:{port}")
            except ValueError:
                self.log(f"[UDP] Ungültige CHAT_REQUEST von {addr}")
        elif cmd == "CHAT_REJECTED":
            self.log(f"[UDP] Chat-Anfrage von {addr} abgelehnt")

    def check_chat_requests(self):
        while not self.chat_requests.empty():
            ip, port = self.chat_requests.get()
            if messagebox.askyesno("Chat-Anfrage", f"{ip}:{port} möchte mit dir chatten. Annehmen?"):
                try:
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((ip, port))
                    conn.sendall(self.nickname.get().encode())
                    peer_nickname = conn.recv(1024).decode().strip()
                    self.start_direct_chat(conn, ip, port, peer_nickname)
                except Exception as e:
                    self.log(f"[FEHLER] Verbindung fehlgeschlagen: {e}")
            else:
                try:
                    self.udp_sock.sendto(Protocol.chat_rejected(), (ip, port))
                except Exception as e:
                    self.log(f"[WARNUNG] CHAT_REJECTED konnte nicht gesendet werden: {e}")
        self.master.after(1000, self.check_chat_requests)

    def send_broadcast(self, event=None):
        message = self.input_entry.get().strip()
        if message and self.sock:
            self.sock.sendall(Protocol.broadcast(self.nickname.get(), message))
            self.input_entry.delete(0, tk.END)

    def disconnect_from_server(self):
        if self.running:
            try:
                self.sock.sendall(Protocol.quit())
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

        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")

    def on_closing(self):
        self.disconnect_from_server()
        self.master.destroy()

    def send_chat_request(self, target_ip, target_udp_port, target_nick):
        self.log(f"[DEBUG] Sende CHAT_REQUEST an {target_ip}:{target_udp_port}")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', 0))
        server.listen(1)
        tcp_port = server.getsockname()[1]
        threading.Thread(target=self.accept_chat, args=(server, target_nick), daemon=True).start()

        try:
            msg = Protocol.chat_request(tcp_port)
            self.udp_sock.sendto(msg, (target_ip, target_udp_port))
            self.log(f"[INFO] Chat-Anfrage an {target_ip}:{target_udp_port} gesendet")
        except Exception as e:
            self.log(f"[FEHLER] Chat-Anfrage konnte nicht gesendet werden: {e}")

    def accept_chat(self, server_sock, expected_nick=None):
        server_sock.settimeout(10)
        try:
            conn, addr = server_sock.accept()
            peer_nickname = conn.recv(1024).decode().strip()
            conn.sendall(self.nickname.get().encode())
            self.start_direct_chat(conn, addr[0], addr[1], peer_nickname)
        except socket.timeout:
            self.log("[INFO] Deine Chat-Anfrage wurde nicht beantwortet.")
        finally:
            server_sock.close()

    def start_direct_chat(self, conn, peer_ip, peer_port, peer_nickname):
        chat_window = tk.Toplevel(self.master)
        chat_window.title(f"Privater Chat mit {peer_nickname} @ {peer_ip}:{peer_port}")

        chat_box = scrolledtext.ScrolledText(chat_window, state='disabled', height=10)
        chat_box.pack(padx=10, pady=5, fill="both")

        input_entry = tk.Entry(chat_window)
        input_entry.pack(padx=10, fill="x")

        stop_event = threading.Event()

        def log_chat(msg, sender=None):
            timestamp = self.current_time()
            if sender:
                line = f"[{sender}] ({timestamp}): {msg}"
            else:
                line = msg
            chat_box.config(state='normal')
            chat_box.insert(tk.END, line + "\n")
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
                        sleep(5)
                        break
                    log_chat(decoded, peer_nickname)
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
                    conn.sendall(b"[DISCONNECT]")
                except:
                    pass
                chat_window.destroy()
                return
            conn.sendall(msg.encode())
            log_chat(msg, self.nickname.get())
            input_entry.delete(0, tk.END)

        input_entry.bind("<Return>", send_msg)
        chat_window.protocol("WM_DELETE_WINDOW", lambda: (
            stop_event.set(),
            conn.sendall(b"[DISCONNECT]"),
            conn.close(),
            chat_window.destroy()
        ))

        threading.Thread(target=recv_loop, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()
