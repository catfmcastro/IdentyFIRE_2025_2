"""
Visualizador de Logs de Exclusão Mútua com Relógio Lógico
Gera diagramas e análises dos eventos distribuídos
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import sys
import os

class MutexLogVisualizer:
    """
    Visualiza logs de exclusão mútua usando relógios lógicos
    """
    
    def __init__(self, log_files):
        self.log_files = log_files if isinstance(log_files, list) else [log_files]
        self.all_events = []
        self.processes = []
        self.load_logs()
    
    def load_logs(self):
        """Carrega todos os arquivos de log"""
        for log_file in self.log_files:
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    
                    events = data.get('events', [])
                    if events:
                        self.all_events.extend(events)
                        
                        # Extrai process_id
                        pid = data.get('process_id', events[0].get('process_id', 'unknown'))
                        if pid not in self.processes:
                            self.processes.append(pid)
                        
                        print(f"✓ Carregado: {log_file} ({len(events)} eventos)")
            except Exception as e:
                print(f"✗ Erro ao carregar {log_file}: {e}")
        
        # Ordena eventos por timestamp de Lamport
        self.all_events.sort(key=lambda e: (e['lamport_ts'], e['process_id']))
        print(f"\n✓ Total: {len(self.all_events)} eventos de {len(self.processes)} processos")
    
    def generate_space_time_diagram(self, output_file='mutex_spacetime.png'):
        """
        Gera diagrama espaço-tempo (Lamport diagram)
        """
        if not self.all_events:
            print("Nenhum evento para visualizar")
            return
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Cores para diferentes tipos de eventos
        colors = {
            'REQUEST': '#FFA726',    # Laranja
            'GRANT': '#66BB6A',      # Verde
            'ENTER_CS': '#42A5F5',   # Azul
            'EXIT_CS': '#AB47BC',    # Roxo
            'RELEASE': '#EF5350'     # Vermelho
        }
        
        # Mapeia processos para linhas do eixo Y
        process_map = {pid: idx for idx, pid in enumerate(sorted(self.processes))}
        
        # Plota eventos
        for event in self.all_events:
            pid = event['process_id']
            y = process_map[pid]
            x = event['lamport_ts']
            etype = event['event_type']
            
            color = colors.get(etype, '#757575')
            marker = 'o' if etype != 'ENTER_CS' else 's'
            size = 100 if etype in ['ENTER_CS', 'EXIT_CS'] else 80
            
            ax.scatter(x, y, c=color, marker=marker, s=size, 
                      edgecolors='black', linewidths=1.5, zorder=3)
            
            # Anotação
            if etype in ['ENTER_CS', 'EXIT_CS']:
                ax.annotate(etype.replace('_', '\n'), 
                           xy=(x, y), xytext=(5, 5), 
                           textcoords='offset points',
                           fontsize=7, fontweight='bold')
        
        # Conecta eventos do mesmo processo
        for pid in self.processes:
            process_events = [e for e in self.all_events if e['process_id'] == pid]
            process_events.sort(key=lambda e: e['lamport_ts'])
            
            y = process_map[pid]
            timestamps = [e['lamport_ts'] for e in process_events]
            
            ax.plot(timestamps, [y]*len(timestamps), 
                   color='gray', linestyle='--', linewidth=0.8, alpha=0.5, zorder=1)
        
        # Configuração dos eixos
        ax.set_xlabel('Lamport Timestamp', fontsize=12, fontweight='bold')
        ax.set_ylabel('Process', fontsize=12, fontweight='bold')
        ax.set_yticks(range(len(self.processes)))
        ax.set_yticklabels(sorted(self.processes))
        ax.grid(True, alpha=0.3)
        
        # Legenda
        legend_elements = [
            mpatches.Patch(color=colors['REQUEST'], label='REQUEST'),
            mpatches.Patch(color=colors['GRANT'], label='GRANT'),
            mpatches.Patch(color=colors['ENTER_CS'], label='ENTER CS'),
            mpatches.Patch(color=colors['EXIT_CS'], label='EXIT CS'),
            mpatches.Patch(color=colors['RELEASE'], label='RELEASE')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
        
        plt.title('Diagrama Espaço-Tempo - Exclusão Mútua Distribuída', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ Diagrama salvo: {output_file}")
        plt.close()
    
    def generate_critical_section_timeline(self, output_file='mutex_cs_timeline.png'):
        """
        Gera linha do tempo das seções críticas
        """
        # Extrai períodos de CS
        cs_periods = []
        
        for pid in self.processes:
            process_events = [e for e in self.all_events if e['process_id'] == pid]
            process_events.sort(key=lambda e: e['lamport_ts'])
            
            enter_ts = None
            for event in process_events:
                if event['event_type'] == 'ENTER_CS':
                    enter_ts = event['lamport_ts']
                elif event['event_type'] == 'EXIT_CS' and enter_ts is not None:
                    cs_periods.append({
                        'process': pid,
                        'start': enter_ts,
                        'end': event['lamport_ts']
                    })
                    enter_ts = None
        
        if not cs_periods:
            print("Nenhum período de CS encontrado")
            return
        
        # Plota
        fig, ax = plt.subplots(figsize=(14, 6))
        
        process_map = {pid: idx for idx, pid in enumerate(sorted(self.processes))}
        
        for period in cs_periods:
            y = process_map[period['process']]
            start = period['start']
            end = period['end']
            duration = end - start
            
            # Barra horizontal
            ax.barh(y, duration, left=start, height=0.6, 
                   color='#42A5F5', edgecolor='black', linewidth=1.5, alpha=0.7)
            
            # Anotação de duração
            mid = start + duration / 2
            ax.text(mid, y, f'{duration}', ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='white')
        
        # Verificação de sobreposição (violações)
        violations = []
        for i, p1 in enumerate(cs_periods):
            for p2 in cs_periods[i+1:]:
                # Checa se há sobreposição
                if not (p1['end'] <= p2['start'] or p2['end'] <= p1['start']):
                    if p1['process'] != p2['process']:
                        violations.append((p1, p2))
                        
                        # Marca violação
                        overlap_start = max(p1['start'], p2['start'])
                        overlap_end = min(p1['end'], p2['end'])
                        
                        ax.axvspan(overlap_start, overlap_end, 
                                 color='red', alpha=0.3, zorder=0)
        
        if violations:
            print(f"\n⚠ {len(violations)} VIOLAÇÕES DE EXCLUSÃO MÚTUA DETECTADAS!")
            for v1, v2 in violations:
                print(f"  - {v1['process']} e {v2['process']}: "
                      f"ts {max(v1['start'], v2['start'])} - {min(v1['end'], v2['end'])}")
        
        ax.set_xlabel('Lamport Timestamp', fontsize=12, fontweight='bold')
        ax.set_ylabel('Process', fontsize=12, fontweight='bold')
        ax.set_yticks(range(len(self.processes)))
        ax.set_yticklabels(sorted(self.processes))
        ax.grid(True, axis='x', alpha=0.3)
        
        title = 'Linha do Tempo - Seções Críticas'
        if violations:
            title += f' (⚠ {len(violations)} VIOLAÇÕES)'
        
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Timeline salva: {output_file}")
        plt.close()
    
    def generate_statistics_report(self, output_file='mutex_statistics.txt'):
        """
        Gera relatório estatístico textual
        """
        report = []
        report.append("="*60)
        report.append("RELATÓRIO DE ANÁLISE DE EXCLUSÃO MÚTUA")
        report.append("="*60)
        report.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total de Eventos: {len(self.all_events)}")
        report.append(f"Processos: {len(self.processes)}")
        report.append(f"Processos IDs: {', '.join(sorted(self.processes))}")
        report.append("")
        
        # Estatísticas por tipo de evento
        report.append("--- Eventos por Tipo ---")
        event_types = {}
        for event in self.all_events:
            etype = event['event_type']
            event_types[etype] = event_types.get(etype, 0) + 1
        
        for etype, count in sorted(event_types.items()):
            report.append(f"  {etype}: {count}")
        report.append("")
        
        # Estatísticas por processo
        report.append("--- Estatísticas por Processo ---")
        for pid in sorted(self.processes):
            process_events = [e for e in self.all_events if e['process_id'] == pid]
            
            enters = sum(1 for e in process_events if e['event_type'] == 'ENTER_CS')
            exits = sum(1 for e in process_events if e['event_type'] == 'EXIT_CS')
            requests = sum(1 for e in process_events if e['event_type'] == 'REQUEST')
            grants = sum(1 for e in process_events if e['event_type'] == 'GRANT')
            
            report.append(f"\n{pid}:")
            report.append(f"  Total de eventos: {len(process_events)}")
            report.append(f"  Requests: {requests}")
            report.append(f"  Grants: {grants}")
            report.append(f"  CS Entries: {enters}")
            report.append(f"  CS Exits: {exits}")
            
            # Calcula tempos de espera
            wait_times = []
            req_ts = None
            for e in sorted(process_events, key=lambda x: x['lamport_ts']):
                if e['event_type'] == 'REQUEST':
                    req_ts = e['lamport_ts']
                elif e['event_type'] == 'GRANT' and req_ts is not None:
                    wait_times.append(e['lamport_ts'] - req_ts)
                    req_ts = None
            
            if wait_times:
                avg_wait = sum(wait_times) / len(wait_times)
                max_wait = max(wait_times)
                report.append(f"  Tempo médio de espera (lógico): {avg_wait:.2f} ticks")
                report.append(f"  Tempo máximo de espera (lógico): {max_wait} ticks")
        
        report.append("")
        report.append("="*60)
        
        # Salva relatório
        report_text = "\n".join(report)
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        print(f"✓ Relatório salvo: {output_file}")
        print("\n" + report_text)
    
    def visualize_all(self, prefix='mutex_analysis'):
        """Gera todas as visualizações"""
        print("\n" + "="*60)
        print("GERANDO VISUALIZAÇÕES")
        print("="*60)
        
        self.generate_space_time_diagram(f'{prefix}_spacetime.png')
        self.generate_critical_section_timeline(f'{prefix}_timeline.png')
        self.generate_statistics_report(f'{prefix}_report.txt')
        
        print("\n" + "="*60)
        print("✓ VISUALIZAÇÕES CONCLUÍDAS")
        print("="*60)


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualizador de Logs de Exclusão Mútua')
    parser.add_argument('log_files', nargs='+', help='Arquivos de log JSON')
    parser.add_argument('--output-prefix', default='mutex_analysis', 
                       help='Prefixo para arquivos de saída')
    
    args = parser.parse_args()
    
    # Verifica se arquivos existem
    for log_file in args.log_files:
        if not os.path.exists(log_file):
            print(f"✗ Arquivo não encontrado: {log_file}")
            sys.exit(1)
    
    visualizer = MutexLogVisualizer(args.log_files)
    visualizer.visualize_all(args.output_prefix)


if __name__ == "__main__":
    main()