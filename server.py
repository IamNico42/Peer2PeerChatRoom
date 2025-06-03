import socket
import threading
from protocol import build_message, parse_message

class ChatServer:
    def __init__(self, host='0.0.0.0', port=9000):
        self.host = host
        self.port = port
        self.clients = {}
        self.lock = threading.Lock()
        self.running = False
        self._sock = None

    def start(self):
        self.running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen()
        self._sock.settimeout(1.0) # Timeout für accept, damit wir regelmäßig prüfen können, ob self.running noch True ist

        print(f"[SERVER] Listening on {self.host}:{self.port}")
        while self.running:
            try:
                conn, addr = self._sock.accept()
            except socket.timeout:
                continue  # Timeout, prüf erneut self.running
            except OSError:
                break  # Socket wurde geschlossen
            print(f"[NEW CONNECTION] {addr}")
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

        # Cleanup beim Beenden
        try:
            self._sock.close()
        except:
            pass
        with self.lock:
            for conn in self.clients.values():
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                except:
                    pass
            self.clients.clear()
        print("[SERVER] Shutdown complete.")

    def list_clients(self):
        with self.lock:
            return [
                f"{nick} @ {ip}:{udp}" for nick, (_, ip, udp) in self.clients.items()
            ]


    def shutdown(self):
        self.running = False
        try:
            self._sock.close()
        except:
            pass

    def handle_client(self, conn):
        nickname = None
        buffer = ""
        try:
            while True:
                try:
                    data = conn.recv(4096).decode()
                    if not data:
                        break  # Verbindung wurde ordentlich beendet
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        cmd, args = parse_message(line)
                        if cmd == "REGISTER" and len(args) >= 2:
                            nickname, udp = args[0], args[1]
                            client_ip = conn.getpeername()[0]
                            
                            with self.lock:
                                if nickname in self.clients:
                                    print(f"[REJECTED] Nickname '{nickname}' schon vergeben.")
                                    try:
                                        conn.sendall(build_message("ERROR", "Nickname bereits vergeben").encode())
                                    except:
                                        pass
                                    conn.close()
                                    return  # Neue Verbindung wird abgelehnt
                                self.clients[nickname] = (conn, client_ip, udp)

                            conn.sendall(build_message("WELCOME", nickname).encode())
                            self.send_userlist_initial(conn)
                            self.notify_all("USER_JOINED", nickname, client_ip, udp)
                        elif cmd == "BROADCAST" and len(args) >= 2:
                            sender = args[0]
                            text = " ".join(args[1:])
                            print(f"[DEBUG Server] Broadcast von {sender}: {text}")
                            self.broadcast(sender, text)
                        elif cmd == "QUIT":
                            break
                except (ConnectionResetError, ConnectionAbortedError):
                    break  # Verbindung wurde vom Client beendet
                except Exception as e:
                    print(f"[ERROR] Bei der Verarbeitung eines Clients: {e}")
                    break
        finally:
            with self.lock:
                if nickname in self.clients and self.clients[nickname][0] == conn:
                    del self.clients[nickname]
            conn.close()
            print(f"[INFO] {nickname or 'Unbekannt'} disconnected.")
            if nickname:
                self.notify_all("USER_LEFT", nickname)

    def broadcast(self, sender, message):
        with self.lock:
            for nick, conn_info in self.clients.items():
                if nick != sender:
                    conn = conn_info[0]
                    try:
                        conn.sendall(build_message("BROADCAST_MSG", sender, message).encode())
                    except:
                        pass

    def send_userlist_initial(self, conn):
        with self.lock:
            entries = [f"{n}:{ip}:{u}" for n, (_, ip, u) in self.clients.items()]
        conn.sendall(build_message("USERLIST", *entries).encode())

    def notify_all(self, cmd, *args):
        msg = build_message(cmd, *args)
        with self.lock:
            for n, (c, _, _) in self.clients.items():
                try:
                    c.sendall(msg.encode())
                except:
                    pass
