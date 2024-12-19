import socket
import socketserver
import ssl
import os
import pyqrcode
from MyHandler import MyHandler


# Assign port (443 for SSL, 8443 for development SSL)
PORT = 8443


# Path to SSL certificates
CERT_PTH = os.path.join(os.getcwd(), 'server.crt')
KEY_PTH = os.path.join(os.getcwd(), 'server.key')

 
# Get path to the current user's desktop, and change path to that directory
desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
os.chdir(desktop)
  
 
# Start the TCP server over a secure connection
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:

    # Get the address of the server
    hostname = socket.gethostname()
    IP = "https://"  + socket.gethostbyname(hostname) + ":" + str(PORT)


    # Create and display a qr link to the server in the cl
    print(pyqrcode.create(IP).terminal())
    print("serving at ", IP)


    # Enable HTTPS with SSL, wrap base socket with this
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERT_PTH, keyfile=KEY_PTH)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    # Serve while this script is running
    httpd.serve_forever()
