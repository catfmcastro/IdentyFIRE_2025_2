import json
import struct
import socket
import base64
import threading

# ============================================================================
# PROTOCOLO RPC MANUAL (Substitui HTTP/Flask)
# Estrutura do Pacote: [TAMANHO (4 bytes big-endian)] + [DADOS (JSON utf-8)]
# ============================================================================

def send_rpc_message(sock, message_dict, lamport_clock=None):
    """
    Serializa dict para JSON e envia com cabeçalho de tamanho
    Se lamport_clock fornecido, adiciona timestamp
    """
    try:
        # Adiciona timestamp de Lamport se disponível
        if lamport_clock:
            ts = lamport_clock.send_event(
                message_dict.get('method', 'UNKNOWN'),
                {'params': message_dict.get('params')}
            )
            message_dict['lamport_ts'] = ts
        
        json_data = json.dumps(message_dict).encode('utf-8')
        header = struct.pack('>I', len(json_data))
        sock.sendall(header + json_data)
        
    except Exception as e:
        print(f"[RPC Protocol] Erro ao enviar: {e}")
        raise


def receive_rpc_message(sock, lamport_clock=None):
    """
    Lê 4 bytes de tamanho e depois o corpo da mensagem
    Se lamport_clock fornecido, atualiza com timestamp recebido
    """
    try:
        # 1. Ler o cabeçalho (4 bytes)
        raw_msglen = recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        
        # 2. Ler o corpo da mensagem
        data = recvall(sock, msglen)
        if not data:
            return None
        
        message = json.loads(data.decode('utf-8'))
        
        # Atualiza relógio se disponível
        if lamport_clock and 'lamport_ts' in message:
            received_ts = message['lamport_ts']
            lamport_clock.receive_event(
                received_ts,
                message.get('method', 'RESPONSE'),
                message.get('params') or message.get('result')
            )
        
        return message
        
    except Exception as e:
        print(f"[RPC Protocol] Erro ao receber: {e}")
        return None


def recvall(sock, n):
    """Garante que lemos exatamente n bytes do socket"""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


# Funções auxiliares para imagem
def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')


def base64_to_image(base64_string):
    return base64.b64decode(base64_string)


# ============================================================================
# SERVIDOR RPC BASE COM LAMPORT CLOCK
# ============================================================================

class RPCServerBase:
    def __init__(self, host, port, lamport_clock=None):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.methods = {}
        self.running = False
        self.lamport_clock = lamport_clock
    
    def register_method(self, name, function):
        """Registra uma função que pode ser chamada remotamente"""
        self.methods[name] = function
    
    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.running = True
        print(f"[RPC Server] Escutando em {self.host}:{self.port} (TCP Sockets)")
        print(f"[RPC Server] Lamport Clock: {'Enabled' if self.lamport_clock else 'Disabled'}")
        
        while self.running:
            try:
                client_sock, address = self.sock.accept()
                t = threading.Thread(target=self.handle_client, args=(client_sock,))
                t.daemon = True
                t.start()
            except OSError:
                break
    
    def stop(self):
        self.running = False
        self.sock.close()
    
    def handle_client(self, client_sock):
        with client_sock:
            while True:
                # Recebe mensagem e atualiza relógio
                request = receive_rpc_message(client_sock, self.lamport_clock)
                if request is None:
                    break
                
                method_name = request.get('method')
                params = request.get('params', {})
                
                # Adiciona timestamp recebido aos params para logs
                if 'lamport_ts' in request:
                    params['_received_lamport_ts'] = request['lamport_ts']
                
                response = {"success": False, "error": "Method not found"}
                
                if method_name in self.methods:
                    try:
                        result = self.methods[method_name](params)
                        response = result
                    except Exception as e:
                        response = {"success": False, "error": str(e)}
                
                # Envia resposta com timestamp
                send_rpc_message(client_sock, response, self.lamport_clock)