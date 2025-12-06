"""
Testador Automatizado de Exclusão Mútua com Relógios Lógicos
Simula múltiplos clientes competindo pelo recurso e valida corretude
"""

import threading
import time
import random
import json
import sys
from datetime import datetime

# Assumindo que você tem os módulos no path
try:
    from lamport_clock import MutexEventLogger, compare_event_logs
    from rpc_protocol import send_rpc_message, receive_rpc_message
except ImportError:
    print("Erro: Certifique-se de que lamport_clock.py e rpc_protocol.py estão no mesmo diretório")
    sys.exit(1)

import socket


class MutexTestClient:
    """
    Cliente de teste para exclusão mútua
    Inclui logging com relógio de Lamport
    """
    
    def __init__(self, client_id, host="127.0.0.1", port=5000, logger=None):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.logger = logger or MutexEventLogger(client_id)
        self.results = []
    
    def _send_request(self, method, params=None):
        """Envia requisição RPC com logging"""
        if params is None:
            params = {}
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        try:
            sock.connect((self.host, self.port))
            
            message = {
                "method": method,
                "params": params
            }
            
            send_rpc_message(sock, message)
            response = receive_rpc_message(sock)
            
            return True, response
        except Exception as e:
            return False, f"Erro RPC: {str(e)}"
        finally:
            try:
                sock.close()
            except:
                pass
    
    def acquire_lock_with_logging(self, timeout=30):
        """Adquire lock com logging de eventos e timeout"""
        # Log da solicitação
        self.logger.log_request({'client_id': self.client_id})
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                success, response = self._send_request("mutex_acquire", {"client_id": self.client_id})
                
                if success and response:
                    if response.get('success') and response.get('status') == 'GRANTED':
                        # Log do grant
                        self.logger.log_grant(data={'queue_wait': False})
                        return True
                    
                    # Em fila
                    pos = response.get('queue_position', 1)
                    wait_time = min(1.0 + (pos * 0.5), 3.0)  # Max 3s
                    time.sleep(wait_time)
                else:
                    time.sleep(2)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[Client {self.client_id}] Erro ao adquirir lock: {e}")
                time.sleep(2)
        
        return False  # Timeout
    
    def release_lock_with_logging(self):
        """Libera lock com logging"""
        self.logger.log_release({'client_id': self.client_id})
        self._send_request("mutex_release", {"client_id": self.client_id})
    
    def simulate_critical_section(self, duration=None):
        """Simula trabalho na seção crítica"""
        if duration is None:
            duration = random.uniform(0.1, 0.5)
        
        # Log de entrada
        enter_ts = self.logger.log_enter_cs()
        
        # Simula trabalho
        time.sleep(duration)
        
        # Log de saída
        exit_ts = self.logger.log_exit_cs()
        
        return {'enter_ts': enter_ts, 'exit_ts': exit_ts, 'duration': duration}
    
    def run_test_cycle(self, num_accesses=5, work_duration=None, max_wait_per_access=30):
        """
        Executa ciclo de teste: múltiplos acessos à seção crítica
        """
        print(f"[Client {self.client_id}] Iniciando {num_accesses} acessos...")
        
        for i in range(num_accesses):
            try:
                # Solicita acesso
                print(f"[Client {self.client_id}] Acesso {i+1}/{num_accesses} - Solicitando...")
                
                # Tenta adquirir com timeout
                start_time = time.time()
                acquired = False
                
                while (time.time() - start_time) < max_wait_per_access:
                    if self.acquire_lock_with_logging():
                        acquired = True
                        break
                
                if acquired:
                    print(f"[Client {self.client_id}] ✓ Lock adquirido")
                    
                    # Trabalha na seção crítica
                    cs_info = self.simulate_critical_section(work_duration)
                    print(f"[Client {self.client_id}] Trabalhou por {cs_info['duration']:.3f}s")
                    
                    # Libera
                    self.release_lock_with_logging()
                    print(f"[Client {self.client_id}] ✓ Lock liberado")
                    
                    self.results.append({
                        'access_num': i + 1,
                        'success': True,
                        'cs_info': cs_info
                    })
                else:
                    print(f"[Client {self.client_id}] ✗ Timeout aguardando lock")
                    self.results.append({
                        'access_num': i + 1,
                        'success': False,
                        'error': 'Timeout waiting for lock'
                    })
                
                # Pausa entre acessos
                time.sleep(random.uniform(0.1, 0.3))
                
            except KeyboardInterrupt:
                print(f"[Client {self.client_id}] Interrompido pelo usuário")
                break
            except Exception as e:
                print(f"[Client {self.client_id}] Erro: {e}")
                import traceback
                traceback.print_exc()
                self.results.append({
                    'access_num': i + 1,
                    'success': False,
                    'error': str(e)
                })
        
        print(f"[Client {self.client_id}] Concluído!")
        return self.results


class MutexTestSuite:
    """
    Suite de testes para exclusão mútua distribuída
    """
    
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.clients = []
        self.threads = []
    
    def test_single_client(self, num_accesses=5):
        """Teste com um único cliente"""
        print("\n" + "="*60)
        print("TESTE 1: Cliente Único")
        print("="*60)
        
        client = MutexTestClient("test_single", self.host, self.port)
        
        try:
            results = client.run_test_cycle(num_accesses)
            
            # Exporta log
            print("\n--- Exportando logs ---")
            log_file = client.logger.export_events("test_single_client.json")
            print(f"✓ Log exportado: {log_file}")
            
            # Verifica
            print("\n--- Verificação ---")
            verification = client.logger.verify_mutex_safety()
            stats = client.logger.get_statistics()
            
            print(f"Total de acessos: {len(results)}")
            print(f"Sucessos: {sum(1 for r in results if r['success'])}")
            print(f"Verificação: {'✓ SEGURO' if verification['safe'] else '✗ VIOLAÇÕES DETECTADAS'}")
            
            if stats:
                print(f"\n--- Estatísticas ---")
                print(f"Requests: {stats.get('requests', 0)}")
                print(f"Enters: {stats.get('enters', 0)}")
                print(f"Exits: {stats.get('exits', 0)}")
            
            return verification['safe']
            
        except Exception as e:
            print(f"\n✗ Erro durante teste: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_concurrent_clients(self, num_clients=3, num_accesses=5):
        """Teste com múltiplos clientes concorrentes"""
        print("\n" + "="*60)
        print(f"TESTE 2: {num_clients} Clientes Concorrentes")
        print("="*60)
        
        self.clients = []
        self.threads = []
        
        # Cria clientes
        for i in range(num_clients):
            client = MutexTestClient(f"client_{i}", self.host, self.port)
            self.clients.append(client)
        
        # Inicia threads
        start_time = time.time()
        
        for client in self.clients:
            thread = threading.Thread(
                target=client.run_test_cycle,
                args=(num_accesses,),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        
        # Aguarda conclusão COM TIMEOUT
        timeout = 60 + (num_clients * num_accesses * 5)  # 5s por acesso + margem
        print(f"\n⏱ Aguardando threads (timeout: {timeout}s)...")
        
        wait_start = time.time()
        all_done = False
        
        while (time.time() - wait_start) < timeout:
            alive = sum(1 for t in self.threads if t.is_alive())
            if alive == 0:
                all_done = True
                break
            
            elapsed = int(time.time() - wait_start)
            print(f"  Progresso: {num_clients - alive}/{num_clients} threads concluídas (elapsed: {elapsed}s)", end='\r')
            time.sleep(1)
        
        print()  # Nova linha
        
        if all_done:
            print(f"✓ Todas as threads concluídas em {time.time() - wait_start:.1f}s")
        else:
            alive_count = sum(1 for t in self.threads if t.is_alive())
            print(f"⚠ Timeout! {alive_count} thread(s) ainda ativa(s)")
        
        end_time = time.time()
        
        # Exporta logs
        log_files = []
        for client in self.clients:
            try:
                log_file = client.logger.export_events(f"test_concurrent_{client.client_id}.json")
                log_files.append(log_file)
                print(f"✓ Log exportado: {log_file}")
            except Exception as e:
                print(f"✗ Erro ao exportar log de {client.client_id}: {e}")
        
        if not log_files:
            print("✗ Nenhum log exportado - teste falhou")
            return False
        
        # Análise global
        print("\n--- Análise Global ---")
        try:
            global_analysis = compare_event_logs(log_files)
            
            print(f"Total de eventos: {global_analysis['total_events']}")
            print(f"Processos: {global_analysis['processes']}")
            print(f"Tempo total: {end_time - start_time:.2f}s")
            print(f"Verificação: {'✓ SEGURO' if global_analysis['safe'] else '✗ VIOLAÇÕES DETECTADAS'}")
            
            if global_analysis['violations']:
                print("\n⚠ VIOLAÇÕES DETECTADAS:")
                for v in global_analysis['violations']:
                    print(f"  - Timestamp {v['timestamp']}: {v['violation']}")
                    print(f"    Processos: {v['processes']}")
            
            # Estatísticas individuais
            print("\n--- Estatísticas por Cliente ---")
            for client in self.clients:
                try:
                    stats = client.logger.get_statistics()
                    print(f"\n{client.client_id}:")
                    print(f"  Requests: {stats.get('requests', 0)}")
                    print(f"  Enters: {stats.get('enters', 0)}")
                    print(f"  Exits: {stats.get('exits', 0)}")
                    if stats.get('avg_wait_time_logical', 0) > 0:
                        print(f"  Avg Wait (logical): {stats['avg_wait_time_logical']:.2f} ticks")
                except Exception as e:
                    print(f"  Erro ao obter stats: {e}")
            
            # Salva análise global
            with open('test_concurrent_global_analysis.json', 'w') as f:
                json.dump(global_analysis, f, indent=2)
            
            print("\n✓ Análise global salva em: test_concurrent_global_analysis.json")
            
            return global_analysis['safe']
            
        except Exception as e:
            print(f"✗ Erro na análise global: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_stress(self, num_clients=10, num_accesses=10):
        """Teste de stress com muitos clientes"""
        print("\n" + "="*60)
        print(f"TESTE 3: Stress Test ({num_clients} clientes, {num_accesses} acessos cada)")
        print("="*60)
        
        return self.test_concurrent_clients(num_clients, num_accesses)
    
    def run_all_tests(self):
        """Executa todos os testes"""
        results = {}
        
        print("\n" + "="*60)
        print("INICIANDO SUITE DE TESTES DE EXCLUSÃO MÚTUA")
        print("="*60)
        
        try:
            # Teste 1
            print("\n[1/3] Executando teste de cliente único...")
            results['single_client'] = self.test_single_client(5)
            print("✓ Teste 1 concluído\n")
            time.sleep(2)
            
            # Teste 2
            print("\n[2/3] Executando teste de clientes concorrentes...")
            results['concurrent_clients'] = self.test_concurrent_clients(3, 5)
            print("✓ Teste 2 concluído\n")
            time.sleep(2)
            
            # Teste 3
            print("\n[3/3] Executando teste de stress...")
            results['stress_test'] = self.test_stress(5, 3)
            print("✓ Teste 3 concluído\n")
            
        except KeyboardInterrupt:
            print("\n\n⚠ Suite interrompida pelo usuário")
            raise
        except Exception as e:
            print(f"\n✗ Erro durante execução da suite: {e}")
            import traceback
            traceback.print_exc()
        
        # Relatório final
        print("\n" + "="*60)
        print("RELATÓRIO FINAL")
        print("="*60)
        
        all_passed = all(results.values())
        
        for test_name, passed in results.items():
            status = "✓ PASSOU" if passed else "✗ FALHOU"
            print(f"{test_name}: {status}")
        
        print("\n" + "="*60)
        if all_passed:
            print("✓ TODOS OS TESTES PASSARAM")
        else:
            print("✗ ALGUNS TESTES FALHARAM")
        print("="*60)
        
        return all_passed


def main():
    """Função principal"""
    import argparse
    import signal
    import os
    import atexit
    
    # Flag para forçar saída
    force_exit = [False]
    
    # Handler para Ctrl+C
    def signal_handler(sig, frame):
        print("\n\n⚠ Interrompido pelo usuário (Ctrl+C)")
        print("Finalizando testes...")
        force_exit[0] = True
        os._exit(130)
    
    # Handler de saída
    def exit_handler():
        if not force_exit[0]:
            print("\n✓ Programa finalizado normalmente")
            sys.stdout.flush()
    
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(exit_handler)
    
    parser = argparse.ArgumentParser(description='Testador de Exclusão Mútua com Relógio Lógico')
    parser.add_argument('--host', default='127.0.0.1', help='Host do servidor')
    parser.add_argument('--port', type=int, default=5000, help='Porta do servidor')
    parser.add_argument('--test', choices=['single', 'concurrent', 'stress', 'all'], 
                       default='all', help='Teste a executar')
    parser.add_argument('--clients', type=int, default=3, help='Número de clientes (concurrent/stress)')
    parser.add_argument('--accesses', type=int, default=5, help='Número de acessos por cliente')
    
    args = parser.parse_args()
    
    print("="*60)
    print("TESTADOR DE EXCLUSÃO MÚTUA - RELÓGIO LÓGICO DE LAMPORT")
    print("="*60)
    print(f"Servidor: {args.host}:{args.port}")
    print(f"Pressione Ctrl+C para interromper")
    print("="*60)
    sys.stdout.flush()
    
    suite = MutexTestSuite(args.host, args.port)
    result = False
    
    try:
        if args.test == 'single':
            result = suite.test_single_client(args.accesses)
        elif args.test == 'concurrent':
            result = suite.test_concurrent_clients(args.clients, args.accesses)
        elif args.test == 'stress':
            result = suite.test_stress(args.clients, args.accesses)
        else:  # all
            result = suite.run_all_tests()
        
        print("\n" + "="*60)
        if result:
            print("✓ TESTE CONCLUÍDO COM SUCESSO")
            exit_code = 0
        else:
            print("✗ TESTE FALHOU OU DETECTOU VIOLAÇÕES")
            exit_code = 1
        print("="*60)
        sys.stdout.flush()
        
        # Força saída imediata
        time.sleep(0.5)
        os._exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrompido pelo usuário")
        sys.stdout.flush()
        os._exit(130)
    except Exception as e:
        print(f"\n✗ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)


if __name__ == "__main__":
    main()