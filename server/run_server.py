from .server import ChatServer
import threading

def main():
    srv = ChatServer(host="0.0.0.0", port=9000)
    t = threading.Thread(target=srv.start, daemon=True)
    t.start()

    print("Server läuft. Befehle: 'exit', 'list'")
    while True:
        cmd = input().strip().lower()
        if cmd == "exit":
            print("Shutting down server…")
            srv.shutdown()
            break
        elif cmd == "list":
            clients = srv.list_clients()
            if clients:
                print("Aktive Clients:")
                for entry in clients:
                    print(" -", entry)
            else:
                print("Keine Clients verbunden.")
        else:
            print("Ungültig – unterstützte Befehle: 'exit', 'list'")

    t.join()
    print("Server beendet.")

if __name__ == "__main__":
    main()
