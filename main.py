from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
from datetime import datetime
import json
import socket
import logging

IP = '127.0.0.1'
http_port = 3000
socket_udp_port = 5000
filename = './storage/data.json'

def transform_data_from_form_to_file(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
#    print(f'data_parse = {data_parse}') # парсений рядок 
    data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
#    print(f'data_dict = {data_dict}') # словничок user+text, що введений на сторінці 
    data_dict_for_saving = {str(datetime.now()): data_dict}
#    print(f'data_dict_for_saving = {data_dict_for_saving}') # словничок time+user+text для запису 
    try:
        with open (filename, 'r', encoding='utf-8') as file:
            dict_from_file = json.load (file)
    except FileNotFoundError:
        dict_from_file = {}
    dict_from_file.update (data_dict_for_saving)
    with open (filename, 'w', encoding='utf-8') as file:
        json.dump (dict_from_file, file, ensure_ascii=False, indent=4)

# socket-сервер
def run_socket_udp_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    logging.info ('Start socket server')
    try:
        while True:
            data, address = sock.recvfrom(1024)
            transform_data_from_form_to_file (data)

    except KeyboardInterrupt:
        logging.info(f'Destroy server')
    finally:
        sock.close()
   
# http-сервер
class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length'])) # сирий бінарний рядок після натиску кнопки
        sock_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_client.sendto (data, (IP, socket_udp_port))
        sock_client.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()        
                                                       
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

# запуск http-сервера 
def run_http_server(IP_addr, port):
    server_address = (IP_addr, port)
    http = HTTPServer(server_address, HttpHandler)
    logging.info ('Start http server')
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    logging.basicConfig (level = logging.DEBUG, format = '%(threadName)s %(message)s')
    http_server1 = Thread (target = run_http_server, args = (IP, http_port))
    socket_udp_server = Thread (target = run_socket_udp_server, args = (IP, socket_udp_port))
    http_server1.start()
    socket_udp_server.start()

