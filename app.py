import socket
import threading
import os

# إعدادات الخادم
LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = int(os.getenv("PORT", 10000))  # Render يحدد هذا تلقائيًا
SSH_HOST = 'meayouf.zapto.org'  # ← غيّر هذا إلى عنوان SSH الخارجي الذي تريد ربطه
SSH_PORT = 22               # منفذ SSH الافتراضي
# رد WebSocket Handshake وهمي
WS_HANDSHAKE_RESPONSE = (
    "HTTP/1.1 101 Switching Protocols\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "\r\n"
)

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode(errors='ignore')
        print("🔵 طلب Handshake:\n", request.lower())

        if "upgrade: websocket" not in request.lower():
            client_socket.close()
            return

        # إرسال رد WebSocket Handshake
        client_socket.send(WS_HANDSHAKE_RESPONSE.encode())

        # الاتصال بخادم SSH
        ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssh_socket.connect((SSH_HOST, SSH_PORT))
        print("🟢 تم الاتصال بـ SSH")

        # نقل البيانات في كلا الاتجاهين
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

    except Exception as e:
        print("❌ خطأ:", e)
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(100)
    print(f"🚀 يعمل على {LISTEN_HOST}:{LISTEN_PORT} وينقل إلى SSH في {SSH_HOST}:{SSH_PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"🔌 اتصال جديد من {addr}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == '__main__':
    start_server()
