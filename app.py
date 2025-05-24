import socket
import threading

# إعدادات الخادم الحقيقي الذي تريد إعادة التوجيه إليه
REMOTE_WS_HOST = "ssh-fr-1.vpnv.cc"
REMOTE_WS_PORT = 80  # أو 443 إذا WSS (مع SSL تحتاج تعديل)

def relay(src, dst):
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

def handle_client(client_socket, client_addr):
    print(f"New client from {client_addr}")
    try:
        http_response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 13\r\n"
        "\r\n"
        "Hello, world!")
        # استقبل طلب الترقية من العميل
        request = client_socket.recv(4096).decode(errors="ignore")
        if "websocket" not in request:
            client_socket.send(http_response.encode())
            print("Not a WebSocket upgrade request.")
            client_socket.close()
            return

        print("[*] WebSocket upgrade requested.")

        # أرسل رد الترقية
        upgrade_response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Connection: Upgrade\r\n"
            "Upgrade: websocket\r\n"
            "\r\n"
        )
        client_socket.send(upgrade_response.encode())

        # اتصال بالخادم الحقيقي
        remote_socket = socket.create_connection((REMOTE_WS_HOST, REMOTE_WS_PORT))
        print(f"Connected to remote WS {REMOTE_WS_HOST}:{REMOTE_WS_PORT}")

        # أرسل نفس طلب الترقية إلى الخادم الحقيقي
        remote_socket.send(request.encode())

        # أنشئ ربط بين الجهتين
        threading.Thread(target=relay, args=(client_socket, remote_socket), daemon=True).start()
        threading.Thread(target=relay, args=(remote_socket, client_socket), daemon=True).start()

    except Exception as e:
        print("Error:", e)
        client_socket.close()

def start_proxy():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.bind(("0.0.0.0", 80))  # نفس بورت HTTP Custom
    listen_socket.listen(10)
    print("WebSocket proxy is running on port 80")

    while True:
        client_sock, client_addr = listen_socket.accept()
        threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True).start()

if __name__ == "__main__":
    start_proxy()
