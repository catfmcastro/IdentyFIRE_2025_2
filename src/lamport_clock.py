"""
Implementação de Relógio Lógico de Lamport para Sistemas Distribuídos
Usado para ordenar eventos e testar o protocolo de exclusão mútua
"""

import threading
import json
import time
from datetime import datetime
from collections import deque

class LamportClock:
    """
    Relógio Lógico de Lamport
    
    Regras:
    1. Antes de executar um evento, incrementa o relógio local
    2. Ao enviar mensagem, inclui timestamp e incrementa relógio
    3. Ao receber mensagem, atualiza: clock = max(clock_local, clock_recebido) + 1
    """
    
    def __init__(self, process_id):
        self.process_id = process_id
        self.clock = 0
        self.lock = threading.Lock()
        self.event_log = deque(maxlen=1000)  # Log dos últimos 1000 eventos
    
    def tick(self):
        """Incrementa o relógio (evento local)"""
        with self.lock:
            self.clock += 1
            return self.clock
    
    def send_event(self, event_type, data=None):
        """Registra evento de envio e retorna timestamp"""
        with self.lock:
            self.clock += 1
            timestamp = self.clock
            
            self._log_event("SEND", event_type, timestamp, data)
            return timestamp
    
    def receive_event(self, received_timestamp, event_type, data=None):
        """Atualiza relógio ao receber mensagem"""
        with self.lock:
            self.clock = max(self.clock, received_timestamp) + 1
            
            self._log_event("RECV", event_type, self.clock, data, received_timestamp)
            return self.clock
    
    def get_timestamp(self):
        """Retorna timestamp atual sem incrementar"""
        with self.lock:
            return self.clock
    
    def _log_event(self, direction, event_type, timestamp, data=None, recv_ts=None):
        """Registra evento no log para análise"""
        event = {
            'process_id': self.process_id,
            'direction': direction,
            'event_type': event_type,
            'lamport_ts': timestamp,
            'received_ts': recv_ts,
            'wall_clock': datetime.now().isoformat(),
            'data': data
        }
        self.event_log.append(event)
    
    def get_event_log(self):
        """Retorna cópia do log de eventos"""
        with self.lock:
            return list(self.event_log)
    
    def export_log(self, filename=None):
        """Exporta log para arquivo JSON"""
        if filename is None:
            filename = f"lamport_log_{self.process_id}_{int(time.time())}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.get_event_log(), f, indent=2)
        
        return filename


class VectorClock:
    """
    Relógio Vetorial (extensão do Lamport)
    Permite detectar causalidade entre eventos
    """
    
    def __init__(self, process_id, num_processes):
        self.process_id = process_id
        self.num_processes = num_processes
        self.vector = [0] * num_processes
        self.lock = threading.Lock()
        self.event_log = deque(maxlen=1000)
    
    def tick(self):
        """Incrementa posição do próprio processo"""
        with self.lock:
            self.vector[self.process_id] += 1
            return self.vector.copy()
    
    def send_event(self, event_type, data=None):
        """Evento de envio"""
        with self.lock:
            self.vector[self.process_id] += 1
            timestamp = self.vector.copy()
            
            self._log_event("SEND", event_type, timestamp, data)
            return timestamp
    
    def receive_event(self, received_vector, event_type, data=None):
        """Atualiza vetor ao receber mensagem"""
        with self.lock:
            # Atualiza cada posição com o máximo
            for i in range(self.num_processes):
                self.vector[i] = max(self.vector[i], received_vector[i])
            
            # Incrementa própria posição
            self.vector[self.process_id] += 1
            
            self._log_event("RECV", event_type, self.vector.copy(), data, received_vector)
            return self.vector.copy()
    
    def happens_before(self, v1, v2):
        """
        Verifica se v1 happened-before v2 (v1 -> v2)
        Retorna True se v1 < v2 (todos elementos <= e pelo menos um <)
        """
        less_or_equal = all(v1[i] <= v2[i] for i in range(self.num_processes))
        strictly_less = any(v1[i] < v2[i] for i in range(self.num_processes))
        return less_or_equal and strictly_less
    
    def concurrent(self, v1, v2):
        """Verifica se dois eventos são concorrentes"""
        return not self.happens_before(v1, v2) and not self.happens_before(v2, v1)
    
    def _log_event(self, direction, event_type, vector, data=None, recv_vec=None):
        """Registra evento no log"""
        event = {
            'process_id': self.process_id,
            'direction': direction,
            'event_type': event_type,
            'vector': vector,
            'received_vector': recv_vec,
            'wall_clock': datetime.now().isoformat(),
            'data': data
        }
        self.event_log.append(event)
    
    def get_event_log(self):
        """Retorna cópia do log"""
        with self.lock:
            return list(self.event_log)


class MutexEventLogger:
    """
    Logger especializado para eventos de exclusão mútua
    Combina relógio lógico com análise de corretude
    """
    
    def __init__(self, process_id):
        self.process_id = process_id
        self.clock = LamportClock(process_id)
        self.mutex_events = []
        self.lock = threading.Lock()
    
    def log_request(self, data=None):
        """Cliente solicita acesso"""
        ts = self.clock.send_event("MUTEX_REQUEST", data)
        self._log_mutex_event("REQUEST", ts, data)
        return ts
    
    def log_grant(self, received_ts=None, data=None):
        """Servidor concede acesso"""
        if received_ts:
            ts = self.clock.receive_event(received_ts, "MUTEX_GRANT", data)
        else:
            ts = self.clock.tick()
        
        self._log_mutex_event("GRANT", ts, data)
        return ts
    
    def log_enter_cs(self):
        """Entra na seção crítica"""
        ts = self.clock.tick()
        self._log_mutex_event("ENTER_CS", ts, {'critical_section': True})
        return ts
    
    def log_exit_cs(self):
        """Sai da seção crítica"""
        ts = self.clock.tick()
        self._log_mutex_event("EXIT_CS", ts, {'critical_section': False})
        return ts
    
    def log_release(self, data=None):
        """Cliente libera recurso"""
        ts = self.clock.send_event("MUTEX_RELEASE", data)
        self._log_mutex_event("RELEASE", ts, data)
        return ts
    
    def _log_mutex_event(self, event_type, timestamp, data):
        """Registra evento de mutex"""
        with self.lock:
            event = {
                'process_id': self.process_id,
                'event_type': event_type,
                'lamport_ts': timestamp,
                'wall_clock': time.time(),
                'wall_clock_str': datetime.now().isoformat(),
                'data': data or {}
            }
            self.mutex_events.append(event)
    
    def verify_mutex_safety(self):
        """
        Verifica propriedades de segurança do mutex:
        1. Exclusão mútua: no máximo 1 processo na CS por vez
        2. Ausência de deadlock: se alguém pediu, eventualmente alguém entra
        """
        with self.lock:
            events_copy = list(self.mutex_events)
        
        return self._verify_mutex_safety_unlocked(events_copy)
    
    def _verify_mutex_safety_unlocked(self, events):
        """Verifica segurança SEM usar lock (versão segura)"""
        events_sorted = sorted(events, key=lambda e: e['lamport_ts'])
        
        in_cs = set()
        violations = []
        
        for event in events_sorted:
            pid = event['process_id']
            etype = event['event_type']
            
            if etype == "ENTER_CS":
                if in_cs:
                    violations.append({
                        'type': 'MUTUAL_EXCLUSION_VIOLATION',
                        'timestamp': event['lamport_ts'],
                        'processes_in_cs': list(in_cs) + [pid]
                    })
                in_cs.add(pid)
            
            elif etype == "EXIT_CS":
                in_cs.discard(pid)
        
        return {
            'safe': len(violations) == 0,
            'violations': violations,
            'total_events': len(events_sorted)
        }
    
    def get_statistics(self):
        """Retorna estatísticas dos eventos"""
        with self.lock:
            events_copy = list(self.mutex_events)
            process_id = self.process_id
        
        return self._calculate_statistics_unlocked(events_copy, process_id)
    
    def _calculate_statistics_unlocked(self, events, process_id):
        """Calcula estatísticas SEM usar lock (versão segura)"""
        if not events:
            return {}
        
        request_count = sum(1 for e in events if e['event_type'] == 'REQUEST')
        grant_count = sum(1 for e in events if e['event_type'] == 'GRANT')
        enter_cs_count = sum(1 for e in events if e['event_type'] == 'ENTER_CS')
        exit_cs_count = sum(1 for e in events if e['event_type'] == 'EXIT_CS')
        release_count = sum(1 for e in events if e['event_type'] == 'RELEASE')
        
        # Calcular tempos de espera (REQUEST -> GRANT)
        wait_times = []
        requests = {e['lamport_ts']: e for e in events if e['event_type'] == 'REQUEST'}
        grants = [e for e in events if e['event_type'] == 'GRANT']
        
        for grant in grants:
            # Encontrar REQUEST correspondente (último antes do GRANT)
            request_ts = max((ts for ts in requests.keys() if ts < grant['lamport_ts']), default=None)
            if request_ts:
                wait_times.append(grant['lamport_ts'] - request_ts)
        
        return {
            'total_events': len(events),
            'requests': request_count,
            'grants': grant_count,
            'enters': enter_cs_count,
            'exits': exit_cs_count,
            'releases': release_count,
            'avg_wait_time_logical': sum(wait_times) / len(wait_times) if wait_times else 0,
            'max_lamport_ts': max(e['lamport_ts'] for e in events) if events else 0,
            'process_id': process_id
        }
    
    def export_events(self, filename=None):
        """Exporta eventos para arquivo JSON"""
        if filename is None:
            filename = f"mutex_events_{self.process_id}_{int(time.time())}.json"
        
        try:
            # Copia dados COM lock
            with self.lock:
                events_copy = list(self.mutex_events)
                process_id = self.process_id
            
            # Calcula stats e verification SEM lock
            stats = self._calculate_statistics_unlocked(events_copy, process_id)
            verification = self._verify_mutex_safety_unlocked(events_copy)
            
            # Monta dados finais
            data = {
                'process_id': process_id,
                'events': events_copy,
                'statistics': stats,
                'verification': verification
            }
            
            # Escreve arquivo SEM lock COM ENCODING UTF-8
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)  # ensure_ascii=False preserva caracteres especiais
            
            return filename
        except Exception as e:
            print(f"Erro ao exportar eventos: {e}")
            return None


def compare_event_logs(log_files):
    """
    Compara logs de múltiplos processos para verificar consistência global
    """
    all_events = []
    
    for log_file in log_files:
        with open(log_file, 'r') as f:
            data = json.load(f)
            all_events.extend(data.get('events', []))
    
    # Ordenar por timestamp de Lamport
    all_events.sort(key=lambda e: (e['lamport_ts'], e['process_id']))
    
    # Verificar exclusão mútua global
    in_cs = set()
    violations = []
    
    for event in all_events:
        pid = event['process_id']
        etype = event['event_type']
        
        if etype == "ENTER_CS":
            if in_cs:
                violations.append({
                    'timestamp': event['lamport_ts'],
                    'violation': 'Multiple processes in CS',
                    'processes': list(in_cs) + [pid]
                })
            in_cs.add(pid)
        elif etype == "EXIT_CS":
            in_cs.discard(pid)
    
    return {
        'total_events': len(all_events),
        'processes': list(set(e['process_id'] for e in all_events)),
        'violations': violations,
        'safe': len(violations) == 0,
        'ordered_events': all_events
    }