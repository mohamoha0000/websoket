import socket
import threading
import os

LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = int(os.getenv("PORT", 10000))
SSH_HOST = 'meayouf.zapto.org'  # ← غيّر هذا حسب خادم SSH الذي تستخدمه
SSH_PORT = 22

# رد Handshake WebSocket
WS_HANDSHAKE_RESPONSE = (
    "HTTP/1.1 101 Switching Protocols\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "\r\n"
)

# رد عادي (HTML)
HTTP_OK_RESPONSE = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/html\r\n"
    "Connection: close\r\n"
    "\r\n"
    "<html><body><h1>✅ تم، مرحبًا بك!</h1></body></html>"
)

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode(errors='ignore')
        print("🔵 طلب وارد:\n", request.lower())

        if "upgrade: websocket" in request.lower() or "websocke" in request.lower():
            # رد WebSocket
            client_socket.send(WS_HANDSHAKE_RESPONSE.encode())
            print("🟢 WebSocket Handshake تم بنجاح")

            # اتصال SSH
            ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssh_socket.connect((SSH_HOST, SSH_PORT))
            print("🔐 تم الاتصال بخادم SSH")

            def forward(src, dst):
                try:
                    while True:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.sendall(data)
                except:
                    pass
                finally:
                    src.close()
                    dst.close()

            threading.Thread(target=forward, args=(client_socket, ssh_socket)).start()
            threading.Thread(target=forward, args=(ssh_socket, client_socket)).start()

        else:
            # الرد على طلب عادي (مثل متصفح)
            client_socket.send(HTTP_OK_RESPONSE.encode())
            print("📄 تم إرسال رد HTML")
            client_socket.close()

    except Exception as e:
        print("❌ خطأ:", e)
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(100)
    print(f"🚀 الخادم يعمل على {LISTEN_HOST}:{LISTEN_PORT} وينقل إلى SSH في {SSH_HOST}:{SSH_PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"🔌 اتصال جديد من {addr}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == '__main__':
    start_server()
