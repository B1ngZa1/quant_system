import time
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

def monitor_migration(state_file: Path, data_dir: Path):
    console = Console()
    
    # Calculate total files initially
    total_files = 0
    for adj_type in ["前复权", "后复权", "不复权"]:
        adj_dir = data_dir / adj_type
        if adj_dir.exists():
            total_files += sum(1 for _ in adj_dir.rglob("*.csv"))
            total_files += sum(1 for _ in adj_dir.rglob("*.csv.bak"))
            
    if total_files == 0:
        console.print("[red]No CSV files found to monitor.[/red]")
        return

    with Live(console=console, refresh_per_second=2) as live:
        while True:
            if state_file.exists():
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                        
                    processed = len(state.get("processed_files", []))
                    errors = len(state.get("errors", []))
                    records = state.get("total_records", 0)
                    
                    pct = (processed / total_files) * 100 if total_files > 0 else 0
                    
                    table = Table(title="ETL Migration Monitor")
                    table.add_column("Metric", justify="right", style="cyan")
                    table.add_column("Value", style="magenta")
                    
                    table.add_row("Total Files", str(total_files))
                    table.add_row("Processed", str(processed))
                    table.add_row("Errors", str(errors))
                    table.add_row("Total Records", f"{records:,}")
                    table.add_row("Progress", f"{pct:.2f}%")
                    
                    panel = Panel(table, title="Parquet Migration Status")
                    live.update(panel)
                    
                    if processed + errors >= total_files and processed > 0:
                        break
                        
                except Exception as e:
                    live.update(Panel(f"Error reading state: {e}", style="red"))
            else:
                live.update(Panel("Waiting for migration to start...", style="yellow"))
                
            time.sleep(2)

if __name__ == "__main__":
    monitor_migration(Path("../daily_data_parquet/migration_state.json"), Path("../daily_data"))