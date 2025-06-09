# 💬 Peer2PeerChatRoom

Ein Netzwerk-Chatclient mit zentralem Server für Teilnehmerverwaltung und Peer-to-Peer-Kommunikation über TCP/UDP.  
Dieses Projekt entstand im Rahmen der Lehrveranstaltung *Rechnernetze*.

---

## 📦 Features

- **Zentrale Nutzerverwaltung** über einen Server
- **Gruppenchat (Broadcast)** für alle Teilnehmer
- **Direkte Peer-to-Peer-Kommunikation** zwischen Clients (private Chats)
- **Nutzung von TCP** (für Datenübertragung) **und UDP** (für Verbindungsaufbau)
- **Moderne GUI** mit Tkinter
- **Mehrere Clients** können gleichzeitig verbunden sein
- **Einfache Bedienung** und übersichtliche Benutzerliste

---

## ⚙️ Installation & Start

### 1. Voraussetzungen

- **Python 3.10+** (getestet mit Python 3.11/3.12/3.13)
- Alle Ordner (`client`, `server`, `network`) müssen eine leere `__init__.py` enthalten

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
- `list` – Zeigt alle verbundenen Clients
- `exit` – Beendet den Server

### 4. Starten des Clients

In einem neuen Terminal, ebenfalls im übergeordneten Verzeichnis:

```sh
python -m Peer2PeerChatRoom.client.client
```

Es öffnet sich die grafische Oberfläche.  
Trage Nickname, Server-IP (z.B. `127.0.0.1` für lokal) und Port (Standard: `9000`) ein und verbinde dich.

---

## 🖥️ Bedienung

- **Verbinden:** Nickname, Server-IP und Port eingeben, dann auf "Verbinden" klicken.
- **Broadcast:** Nachricht eingeben und Enter drücken oder auf "Senden" klicken, um an alle zu senden.
- **Private Chats:** Nutzer in der Liste anklicken, um einen privaten Chat zu starten.
- **Trennen:** "Disconnect" klicken, um die Verbindung zu beenden.

---

## 🗂️ Projektstruktur

```
Peer2PeerChatRoom/
├── README.md
├── .gitignore 
│
├── client/
│   │
│   ├── client.py         # Startpunkt für den Client (GUI)
│   ├── core.py           # Client-Logik
│   └── gui.py            # Tkinter-GUI
│
├── server/
│   │
│   ├── run_server.py     # Startpunkt für den Server
│   └── server.py         # Server-Logik
│
└── network/
    │
    └── protocol.py       # Protokoll-Definitionen
```

---

## 📡 Protokoll-Design & Kommunikation

Die Kommunikation zwischen Client und Server (sowie zwischen Clients für private Chats) basiert auf einem eigenen, textbasierten Protokoll, das in `protocol.py` definiert ist.  
Das Protokoll ist so gestaltet, dass es sowohl zuverlässig als auch einfach zu parsen ist.

### 🧱 Aufbau der Nachrichten

**Längenpräfix:**  
Jede Nachricht beginnt mit einem Längenpräfix (z. B. `0042:`), das die Anzahl der folgenden Bytes angibt.

**Beispiel:**

```
0015:BROADCAST|Hi!
```

Das bedeutet: Die Nachricht ist 15 Zeichen lang, gefolgt von einem Doppelpunkt und dann der eigentlichen Nachricht.

**Kommando-Struktur:**  
Nachrichten bestehen aus einem Kommando (z. B. `BROADCAST`, `USERLIST`, `CHAT_REQUEST`) und den zugehörigen Argumenten, getrennt durch Pipes (`|`).

---

### ✅ Vorteile des Längenpräfix

- **Robuste Nachrichtenverarbeitung:**  
  Der Empfänger weiß immer genau, wie viele Bytes zur nächsten vollständigen Nachricht gehören – das verhindert Probleme bei TCP-Streams, wo Nachrichten fragmentiert oder zusammengefasst eintreffen können.

- **Einfache Implementierung:**  
  Erst das Präfix lesen, dann exakt so viele Bytes für die Nachricht.

- **Keine Sonderzeichen-Probleme:**  
  Nachrichten können beliebige Zeichen enthalten (auch Zeilenumbrüche oder Pipes).

---

### 🧰 Wichtige Methoden im Protokoll (`protocol.py`)

- `make_broadcast(nick, msg)`  
  → Baut eine Broadcast-Nachricht für alle Clients.

- `read_broadcast(args)`  
  → Parst eine Broadcast-Nachricht und gibt Nickname und Nachricht zurück.

- `make_user_list(userlist)`  
  → Baut eine Nachricht mit der aktuellen Userliste.

- `read_user_list(args)`  
  → Parst die Userliste in eine Python-Liste.

- `make_chat_request(port)`  
  → Erstellt eine UDP-Chat-Anfrage an einen anderen Client.

- `read_chat_request(args)`  
  → Parst die Portnummer aus einer Chat-Anfrage.

- `chat_rejected()`  
  → Baut eine Nachricht, um eine private Chat-Anfrage abzulehnen.

- `make_error(reason)`  
  → Baut eine Fehlernachricht.

Alle Methoden sorgen dafür, dass Nachrichten immer im richtigen Format mit Längenpräfix erzeugt und gelesen werden.

---

### 🔄 Zusammenspiel im System

- Der **Server** empfängt Nachrichten von Clients, parst sie mit den Protokoll-Methoden und verteilt sie (z. B. Broadcast, Userlist).
- Die **Clients** nutzen die Protokoll-Methoden zum Erzeugen und Verarbeiten von Nachrichten – sowohl für Server-Kommunikation als auch für Peer-to-Peer-Chats.
- **Private Chats** werden per UDP angefragt, der eigentliche Chat läuft dann über eine direkte TCP-Verbindung zwischen den Clients.

---

### 🎯 Vorteile des Ansatzes

- **Skalierbar:** Neue Kommandos können einfach ergänzt werden.
- **Fehlerresistent:** Durch das Längenpräfix werden Nachrichten nie "verschluckt" oder falsch zusammengesetzt.
- **Klar & nachvollziehbar:** Das Protokoll ist menschenlesbar und leicht zu debuggen.

---

## 🛠️ Troubleshooting

- **ImportError / relative imports:**  
  Stelle sicher, dass du IMMER aus dem Verzeichnis **eine Ebene über** `Peer2PeerChatRoom` startest und die Startbefehle mit `-m` verwendest.
- **Firewall:**  
  Stelle sicher, dass keine Firewall die Ports blockiert.

---

## 📚 Hinweise

- Das System ist für Lernzwecke konzipiert und nicht für produktiven Einsatz gedacht.
- Die Kommunikation erfolgt unverschlüsselt.
- Erweiterungen (z.B. Verschlüsselung, Authentifizierung) sind möglich.

---

## 👥 Autor

- IamNico42-  
