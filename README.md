# 💬 Peer2PeerChatRoom

Ein Netzwerk-Chatclient mit zentralem Server für Teilnehmerverwaltung und Peer-to-Peer-Kommunikation über TCP/UDP.
Dieses Projekt entstand im Rahmen der Lehrveranstaltung *Rechnernetze*.

---

## 📦 Features

* **Zentrale Nutzerverwaltung** über einen Server
* **Gruppenchat (Broadcast)** für alle Teilnehmer
* **Direkte Peer-to-Peer-Kommunikation** zwischen Clients (private Chats)
* **Nutzung von TCP** (für Datenübertragung) **und UDP** (für Verbindungsaufbau)
* **Moderne GUI** mit Tkinter
* **Mehrere Clients** können gleichzeitig verbunden sein
* **Einfache Bedienung** und übersichtliche Benutzerliste

---

## ⚙️ Installation & Start

### 1. Voraussetzungen

* **Python 3.10+** (getestet mit Python 3.11/3.12/3.13)
* Alle Ordner (`client`, `server`, `network`) müssen eine leere `__init__.py` enthalten

### 2. Repository klonen

```sh
git clone <repo-url>
cd <repo-ordner>
```

### 3. Starten des Servers

**Wichtig:**
Du musst im Verzeichnis **eine Ebene über** `Peer2PeerChatRoom` stehen!

```sh
python -m Peer2PeerChatRoom.server.run_server
```

Der Server läuft dann und akzeptiert Befehle:

* `list` – Zeigt alle verbundenen Clients
* `exit` – Beendet den Server

### 4. Starten des Clients

In einem neuen Terminal, ebenfalls im übergeordneten Verzeichnis:

```sh
python -m Peer2PeerChatRoom.client.client
```

Es öffnet sich die grafische Oberfläche.
Trage Nickname, Server-IP (z.B. `127.0.0.1` für lokal) und Port (Standard: `9000`) ein und verbinde dich.

---

## 🖥️ Bedienung

* **Verbinden:** Nickname, Server-IP und Port eingeben, dann auf "Verbinden" klicken.
* **Broadcast:** Nachricht eingeben und Enter drücken oder auf "Senden" klicken, um an alle zu senden.
* **Private Chats:** Nutzer in der Liste anklicken, um einen privaten Chat zu starten.
* **Trennen:** "Disconnect" klicken, um die Verbindung zu beenden.

---

## 🗂️ Projektstruktur

```
Peer2PeerChatRoom/
├── README.md
├── .gitignore
│
├── client/
│   ├── client.py         # Startpunkt für den Client (GUI)
│   ├── core.py           # Client-Logik
│   ├── gui.py            # Tkinter-GUI
│   └── chat_session.py   # Private Chat-Handling
│
├── server/
│   ├── run_server.py     # Startpunkt für den Server
│   └── server.py         # Server-Logik
│
└── network/
    └── protocol.py       # Protokoll-Definitionen
```

---

## 📡 Protokoll-Design & Kommunikation

Die Kommunikation zwischen Clients und dem Server (sowie zwischen Clients untereinander für private Chats) verwendet ein **binäres Nachrichtenprotokoll mit Längenpräfix**, das in `network/protocol.py` definiert ist.

### 🔖 Struktur der Nachrichten

* Jede Nachricht besteht aus:

  * einem **4-Byte-Längenpräfix** (`!I`, also big-endian unsigned int)
  * einem **UTF-8 codierten Textinhalt**, z. B. `BROADCAST Alice Hallo Welt`

#### 📦 Beispiel

```python
msg = Protocol.broadcast("Alice", "Hallo Welt")
# ergibt:
# 4-Byte Länge (z.B. \x00\x00\x00\x18 für 24)
# + UTF-8 encoded bytes von "BROADCAST Alice Hallo Welt"
```

Der Empfänger liest zuerst 4 Bytes zur Bestimmung der Nachrichtenlänge, dann genau so viele Bytes für die Nachricht selbst.
So können mehrere Nachrichten in einem TCP-Stream ohne Delimiter eindeutig extrahiert werden.

---

### 🧰 Wichtige Methoden (`protocol.py`)

* `build_command(command, *args)`  → generiert Nachrichten im richtigen Format
* `decode_stream(buffer)`  → verarbeitet einen TCP-Stream mit mehreren Nachrichten
* `extract_command(payload)`  → trennt Kommando und Argumente
* `register(nick, udp_port)`  → erzeugt eine Registrierung
* `chat_request(port)`  → erzeugt eine private Chat-Anfrage
* `read_user_list(args)`  → validiert die empfangene Nutzerliste

---

### ✅ Vorteile des Protokolls

* **Robust gegen Fragmentierung** bei TCP
* **Unicode-fähig** (z. B. Emojis)
* **Einheitlich & leicht zu debuggen**

---

## 🛠️ Troubleshooting

* **ImportError / relative imports:**
  Stelle sicher, dass du **aus dem Verzeichnis überhalb** des Repos startest und mit `-m` arbeitest

* **Firewall-Probleme:**
  Stelle sicher, dass UDP und TCP für den verwendeten Port erlaubt sind

---

## 📚 Hinweise

* Dieses Projekt ist für Lehrzwecke konzipiert, nicht für den produktiven Einsatz
* Die Kommunikation erfolgt **nicht verschlüsselt** (aber Erweiterung möglich)
* Erweiterungen wie **Ende-zu-Ende-Verschlüsselung**, **Login-System** oder **Key-Fingerprint-Validierung** sind leicht integrierbar

---

## 👥 Autor

* [IamNico42](https://github.com/IamNico42)
