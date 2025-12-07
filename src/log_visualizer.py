"""
Visualizador de Logs de Exclusao Mutua com Relogio Logico
Gera diagramas e analises dos eventos distribuidos
"""

import json
import sys
import os

# Configura stdout/stderr para UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')  # Backend nao-interativo
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


class MutexLogVisualizer:
    """
    Visualiza logs de exclusao mutua usando relogios logicos
    """
    
    def __init__(self, log_files):
        self.log_files = log_files if isinstance(log_files, list) else [log_files]
        self.all_events = []
        self.processes = []
        self.load_logs()
    
    def load_logs(self):
        """Carrega todos os arquivos de log com tratamento robusto de encoding"""
        for log_file in self.log_files:
            success = False
            
            # Tenta multiplos encodings
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings_to_try:
                try:
                    with open(log_file, 'r', encoding=encoding, errors='replace') as f:
                        data = json.load(f)
                        
                        events = data.get('events', [])
                        if events:
                            self.all_events.extend(events)
                            
                            # Extrai process_id
                            pid = data.get('process_id', events[0].get('process_id', 'unknown'))
                            if pid not in self.processes:
                                self.processes.append(pid)
                            
                            print(f"[OK] Carregado ({encoding}): {log_file} ({len(events)} eventos)")
                            success = True
                            break
                            
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                except Exception as e:
                    print(f"[ERRO] Ao tentar {encoding} em {log_file}: {e}")
                    continue
            
            if not success:
                print(f"[ERRO] Nao foi possivel carregar {log_file} com nenhum encoding")
    
    def generate_space_time_diagram(self, output_file='mutex_spacetime.png'):
        """
        Gera diagrama espaco-tempo usando wall clock time
        """
        if not self.all_events:
            print("[AVISO] Nenhum evento para visualizar")
            return False
        
        try:
            # Use wall_clock for X axis (real time)
            min_time = min(e['wall_clock'] for e in self.all_events)
            
            # Normalize to start at 0 (seconds from first event)
            for event in self.all_events:
                event['time_offset'] = event['wall_clock'] - min_time
            
            fig, ax = plt.subplots(figsize=(16, 8))
            
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
                x = event['time_offset']
                etype = event['event_type']
                
                color = colors.get(etype, '#757575')
                
                if etype in ['ENTER_CS', 'EXIT_CS']:
                    marker = 's'
                    size = 150
                elif etype == 'REQUEST':
                    marker = 'o'
                    size = 120
                elif etype == 'GRANT':
                    marker = '^'
                    size = 120
                else:
                    marker = 'o'
                    size = 100
                
                ax.scatter(x, y, c=color, marker=marker, s=size, 
                        edgecolors='black', linewidths=1.5, zorder=3, alpha=0.8)
                
                # Anotacao para eventos criticos
                if etype in ['ENTER_CS', 'EXIT_CS']:
                    label = 'ENTER' if etype == 'ENTER_CS' else 'EXIT'
                    ax.annotate(label, 
                            xy=(x, y), xytext=(0, 10), 
                            textcoords='offset points',
                            fontsize=8, fontweight='bold',
                            ha='center')
            
            # Conecta eventos do mesmo processo com linhas
            for pid in self.processes:
                process_events = [e for e in self.all_events if e['process_id'] == pid]
                process_events.sort(key=lambda e: e['time_offset'])
                
                y = process_map[pid]
                times = [e['time_offset'] for e in process_events]
                
                ax.plot(times, [y]*len(times), 
                    color='gray', linestyle='-', linewidth=1.5, alpha=0.4, zorder=1)
            
            # Destacar periodos de CS com retangulos
            for pid in self.processes:
                process_events = [e for e in self.all_events if e['process_id'] == pid]
                process_events.sort(key=lambda e: e['time_offset'])
                
                y = process_map[pid]
                enter_time = None
                
                for event in process_events:
                    if event['event_type'] == 'ENTER_CS':
                        enter_time = event['time_offset']
                    elif event['event_type'] == 'EXIT_CS' and enter_time:
                        exit_time = event['time_offset']
                        width = exit_time - enter_time
                        
                        rect = plt.Rectangle((enter_time, y - 0.3), width, 0.6,
                                            facecolor='yellow', alpha=0.3, 
                                            edgecolor='orange', linewidth=2, zorder=0)
                        ax.add_patch(rect)
                        
                        # Anotacao da duracao
                        mid = enter_time + width / 2
                        ax.text(mid, y, f'{width:.2f}s', ha='center', va='center',
                            fontsize=8, fontweight='bold', color='darkred')
                        enter_time = None
            
            # Configuracao dos eixos
            ax.set_xlabel('Time (seconds from start)', fontsize=13, fontweight='bold')
            ax.set_ylabel('Process', fontsize=13, fontweight='bold')
            ax.set_yticks(range(len(self.processes)))
            ax.set_yticklabels(sorted(self.processes), fontsize=11)
            
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Legenda melhorada
            legend_elements = [
                mpatches.Patch(color=colors['REQUEST'], label='REQUEST'),
                mpatches.Patch(color=colors['GRANT'], label='GRANT'),
                mpatches.Patch(color=colors['ENTER_CS'], label='ENTER CS'),
                mpatches.Patch(color=colors['EXIT_CS'], label='EXIT CS'),
                mpatches.Patch(color=colors['RELEASE'], label='RELEASE'),
                mpatches.Patch(facecolor='yellow', alpha=0.3, edgecolor='orange', 
                            linewidth=2, label='Critical Section')
            ]
            ax.legend(handles=legend_elements, loc='upper left', fontsize=10, 
                    framealpha=0.9, ncol=2)
            
            plt.title('Space-Time Diagram - Distributed Mutual Exclusion\n(Real Wall Clock Time)', 
                    fontsize=15, fontweight='bold', pad=20)
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"\n[OK] Diagrama salvo: {output_file}")
            plt.close()
            return True
            
        except Exception as e:
            print(f"[ERRO] Ao gerar diagrama espaco-tempo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_critical_section_timeline(self, output_file='mutex_cs_timeline.png'):
        """
        Gera linha do tempo das secoes criticas usando wall clock
        """
        try:
            # Use wall_clock for time axis
            min_time = min(e['wall_clock'] for e in self.all_events)
            
            # Normalize to start at 0
            for event in self.all_events:
                if 'time_offset' not in event:
                    event['time_offset'] = event['wall_clock'] - min_time
            
            # Extrai periodos de CS
            cs_periods = []
            
            for pid in self.processes:
                process_events = [e for e in self.all_events if e['process_id'] == pid]
                process_events.sort(key=lambda e: e['time_offset'])
                
                enter_time = None
                for event in process_events:
                    if event['event_type'] == 'ENTER_CS':
                        enter_time = event['time_offset']
                    elif event['event_type'] == 'EXIT_CS' and enter_time is not None:
                        cs_periods.append({
                            'process': pid,
                            'start': enter_time,
                            'end': event['time_offset']
                        })
                        enter_time = None
            
            if not cs_periods:
                print("[AVISO] Nenhum periodo de CS encontrado")
                return False
            
            # Plota
            fig, ax = plt.subplots(figsize=(16, 6))
            
            process_map = {pid: idx for idx, pid in enumerate(sorted(self.processes))}
            
            for period in cs_periods:
                y = process_map[period['process']]
                start = period['start']
                end = period['end']
                duration = end - start
                
                # Barra horizontal
                ax.barh(y, duration, left=start, height=0.6, 
                    color='#42A5F5', edgecolor='black', linewidth=1.5, alpha=0.7)
                
                # Anotacao de duracao
                mid = start + duration / 2
                ax.text(mid, y, f'{duration:.3f}s', ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.5))
            
            # Verificacao de sobreposicao (violacoes)
            violations = []
            for i, p1 in enumerate(cs_periods):
                for p2 in cs_periods[i+1:]:
                    # Checa se ha sobreposicao
                    if not (p1['end'] <= p2['start'] or p2['end'] <= p1['start']):
                        if p1['process'] != p2['process']:
                            violations.append((p1, p2))
                            
                            # Marca violacao
                            overlap_start = max(p1['start'], p2['start'])
                            overlap_end = min(p1['end'], p2['end'])
                            
                            ax.axvspan(overlap_start, overlap_end, 
                                    color='red', alpha=0.3, zorder=0)
            
            if violations:
                print(f"\n[AVISO] {len(violations)} VIOLACOES DE EXCLUSAO MUTUA DETECTADAS!")
                for v1, v2 in violations:
                    print(f"  - {v1['process']} e {v2['process']}: "
                        f"{max(v1['start'], v2['start']):.3f}s - {min(v1['end'], v2['end']):.3f}s")
            
            ax.set_xlabel('Time (seconds from start)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Process', fontsize=12, fontweight='bold')
            ax.set_yticks(range(len(self.processes)))
            ax.set_yticklabels(sorted(self.processes))
            ax.grid(True, axis='x', alpha=0.3)
            
            title = 'Critical Section Timeline (Real Time)'
            if violations:
                title += f' - {len(violations)} VIOLATIONS DETECTED!'
            
            plt.title(title, fontsize=14, fontweight='bold', pad=20, 
                    color='red' if violations else 'black')
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"[OK] Timeline salva: {output_file}")
            plt.close()
            return True
            
        except Exception as e:
            print(f"[ERRO] Ao gerar timeline: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_statistics_report(self, output_file='mutex_statistics.txt'):
        """
        Gera relatorio estatistico textual
        """
        try:
            report = []
            report.append("="*60)
            report.append("RELATORIO DE ANALISE DE EXCLUSAO MUTUA")
            report.append("="*60)
            report.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Total de Eventos: {len(self.all_events)}")
            report.append(f"Processos: {len(self.processes)}")
            report.append(f"Processos IDs: {', '.join(sorted(self.processes))}")
            report.append("")
            
            # Estatisticas por tipo de evento
            report.append("--- Eventos por Tipo ---")
            event_types = {}
            for event in self.all_events:
                etype = event['event_type']
                event_types[etype] = event_types.get(etype, 0) + 1
            
            for etype, count in sorted(event_types.items()):
                report.append(f"  {etype}: {count}")
            report.append("")
            
            # Estatisticas por processo
            report.append("--- Estatisticas por Processo ---")
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
                    report.append(f"  Tempo medio de espera (logico): {avg_wait:.2f} ticks")
                    report.append(f"  Tempo maximo de espera (logico): {max_wait} ticks")
            
            report.append("")
            report.append("="*60)
            
            # Salva relatorio com UTF-8
            report_text = "\n".join(report)
            with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(report_text)
            
            print(f"[OK] Relatorio salvo: {output_file}")
            print("\n" + report_text)
            return True
            
        except Exception as e:
            print(f"[ERRO] Ao gerar relatorio: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def visualize_all(self, prefix='mutex_analysis'):
        """Gera todas as visualizacoes"""
        print("\n" + "="*60)
        print("GERANDO VISUALIZACOES")
        print("="*60)
        
        os.makedirs('tests', exist_ok=True)

        success_count = 0
        
        if self.generate_space_time_diagram(f'tests/{prefix}_spacetime.png'):
            success_count += 1
    
        if self.generate_critical_section_timeline(f'tests/{prefix}_timeline.png'):
            success_count += 1
        
        if self.generate_statistics_report(f'tests/{prefix}_report.txt'):
            success_count += 1
        
        print("\n" + "="*60)
        if success_count == 3:
            print("[OK] VISUALIZACOES CONCLUIDAS COM SUCESSO")
        else:
            print(f"[AVISO] VISUALIZACOES PARCIALMENTE CONCLUIDAS ({success_count}/3)")
        print("="*60)
        
        return success_count > 0


def main():
    """Funcao principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualizador de Logs de Exclusao Mutua')
    parser.add_argument('log_files', nargs='+', help='Arquivos de log JSON')
    parser.add_argument('--output-prefix', default='mutex_analysis', 
                       help='Prefixo para arquivos de saida')
    
    args = parser.parse_args()
    
    # Verifica se arquivos existem
    for log_file in args.log_files:
        if not os.path.exists(log_file):
            print(f"[ERRO] Arquivo nao encontrado: {log_file}")
            sys.exit(1)
    
    visualizer = MutexLogVisualizer(args.log_files)
    
    if not visualizer.all_events:
        print("[ERRO] Nenhum evento carregado. Verifique os arquivos de log.")
        sys.exit(1)
    
    success = visualizer.visualize_all(args.output_prefix)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()