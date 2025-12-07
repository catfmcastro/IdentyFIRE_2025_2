"""
Script simples para testar conexão com o servidor antes de executar os testes
"""

import socket
import sys
import json
import struct

def send_rpc_message(sock, message_dict):
    """Envia mensagem RPC"""
    json_data = json.dumps(message_dict).encode('utf-8')
    header = struct.pack('>I', len(json_data))
    sock.sendall(header + json_data)

def recvall(sock, n):
    """Recebe exatamente n bytes"""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def receive_rpc_message(sock):
    """Recebe mensagem RPC"""
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    data = recvall(sock, msglen)
    if not data:
        return None
    return json.loads(data.decode('utf-8'))

def test_connection(host='127.0.0.1', port=5000):
    """Testa conexão básica com o servidor"""
    print("="*60)
    print("TESTE DE CONEXÃO COM SERVIDOR")
    print("="*60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print()
    
    # Teste 1: TCP Connection
    print("1. Testando conexão TCP...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        print("   ✓ Conexão TCP estabelecida")
    except ConnectionRefusedError:
        print("   ✗ Conexão recusada - servidor não está rodando?")
        return False
    except socket.timeout:
        print("   ✗ Timeout - host/porta incorretos?")
        return False
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return False
    
    # Teste 2: Health Check
    print("\n2. Testando health_check...")
    try:
        message = {"method": "health_check", "params": {}}
        send_rpc_message(sock, message)
        response = receive_rpc_message(sock)
        
        if response:
            print("   ✓ Servidor respondeu")
            print(f"   Status: {response.get('status')}")
            print(f"   Modelo carregado: {response.get('model_loaded')}")
            print(f"   Modelo: {response.get('model_name')}")
        else:
            print("   ✗ Sem resposta do servidor")
            sock.close()
            return False
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        sock.close()
        return False
    
    sock.close()
    
    # Teste 3: Mutex Acquire/Release
    print("\n3. Testando mutex_acquire...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        message = {"method": "mutex_acquire", "params": {"client_id": "test_client"}}
        send_rpc_message(sock, message)
        response = receive_rpc_message(sock)
        
        if response and response.get('success'):
            status = response.get('status')
            print(f"   ✓ Mutex acquire funcionando (status: {status})")
            
            # Tenta release
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            
            message = {"method": "mutex_release", "params": {"client_id": "test_client"}}
            send_rpc_message(sock, message)
            response = receive_rpc_message(sock)
            
            if response:
                print(f"   ✓ Mutex release funcionando")
            else:
                print(f"   ⚠ Mutex release sem resposta")
        else:
            print(f"   ✗ Mutex acquire falhou: {response}")
            sock.close()
            return False
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        try:
            sock.close()
        except:
            pass
        return False
    
    sock.close()
    
    print("\n" + "="*60)
    print("✓ TODOS OS TESTES PASSARAM")
    print("="*60)
    print("\nO servidor está funcionando corretamente!")
    print("Você pode executar os testes com:")
    print(f"  python mutex_tester.py --host {host} --port {port}")
    print()
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Testa conexão com servidor RPC')
    parser.add_argument('--host', default='127.0.0.1', help='Host do servidor')
    parser.add_argument('--port', type=int, default=5000, help='Porta do servidor')
    
    args = parser.parse_args()
    
    try:
        success = test_connection(args.host, args.port)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")
        sys.exit(130)