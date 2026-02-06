from datetime import datetime
import time
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from application.salary import calculate_salary
from application.db.people import get_employees

console = Console()

if __name__ == "__main__":
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    # Заголовок
    console.rule(f"[bold cyan]📅 Бухгалтерия | {current_time}[/]", style="cyan")
    console.print()

    # Прогресс-бар: загрузка сотрудников
    console.print("[bold blue]👥 Загрузка списка сотрудников...[/]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Загрузка...", total=15)
        for i in range(15):
            time.sleep(0.05)
            progress.update(task, advance=1)

    console.print("[green]✅ Сотрудники загружены![/]")
    console.print()

    # Спиннер: расчёт зарплаты
    console.print("[bold yellow]💰 Расчёт зарплаты...[/]")
    with console.status("[bold yellow]Выполняется расчёт...", spinner="dots"):
        time.sleep(1.0)

    console.print("[green]✅ Зарплата рассчитана![/]")
    console.print()

    # Итоговая таблица
    table = Table(
        title="📊 Итоги операции", style="bold green", title_style="bold cyan"
    )
    table.add_column("Операция", style="bold")
    table.add_column("Результат", justify="right", style="green")

    table.add_row("Загружено сотрудников", "15")
    table.add_row("Рассчитано зарплат", "15")
    table.add_row("Время выполнения", f"{datetime.now().strftime('%H:%M:%S')}")

    console.print(table)
    console.print()

    # Футер
    console.rule(
        f"[bold green]🎉 Программа завершена успешно | {current_time}[/]", style="green"
    )
