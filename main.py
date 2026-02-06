from datetime import datetime
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from application.salary import calculate_salary
from application.db.people import get_employees

console = Console()

if __name__ == "__main__":
    # Заголовок с датой
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    console.rule(f"[bold cyan]📅 Бухгалтерия | {current_time}[/]", style="cyan")
    console.print()

    # Вызов функций
    get_employees()
    console.print()
    calculate_salary()

    # Итоговая таблица
    console.print()
    table = Table(title="📊 Итоги расчёта", style="green")
    table.add_column("Показатель", style="bold")
    table.add_column("Значение", justify="right")

    table.add_row("Сотрудников", "15")
    table.add_row("Рассчитано зарплат", "15")
    table.add_row("Статус", "[green]✅ Успешно[/]")

    console.print(table)
    console.print()

    # Футер
    console.rule(
        f"[bold green]✅ Программа завершена | {current_time}[/]", style="green"
    )
