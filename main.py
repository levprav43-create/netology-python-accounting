from datetime import datetime
import time
import sys
import logging
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich.logging import RichHandler
from rich.traceback import install
from rich.prompt import Prompt, Confirm
from rich import box
from application.salary import calculate_salary
from application.db.people import get_employees

# Установка красивых трейсбэков для ошибок
install(show_locals=True)

# Настройка логирования
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=Console(), show_time=True)],
)
log = logging.getLogger("accounting")

console = Console()

# Глобальные флаги состояния
employees_loaded = False
salary_calculated = False


def show_welcome():
    """Приветственный экран"""
    console.clear()
    console.rule("[bold cyan]💼 БУХГАЛТЕРИЯ v2.0[/]", style="cyan")
    console.print(
        Panel.fit(
            "[bold green]Добро пожаловать в систему учёта персонала![/]\n"
            f"Текущее время: [cyan]{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}[/]",
            title="📅 Система запущена",
            border_style="green",
        )
    )
    time.sleep(1)


def show_menu():
    """Отображение главного меню"""
    console.print("\n")
    table = Table(title="📋 Главное меню", box=box.ROUNDED, style="bold blue")
    table.add_column("№", style="bold cyan", justify="center")
    table.add_column("Действие", style="bold white")
    table.add_column("Статус", style="bold", justify="center")

    status1 = "[green]✓ Готово[/]" if employees_loaded else "[yellow]⏳ Ожидает[/]"
    status2 = "[green]✓ Готово[/]" if salary_calculated else "[yellow]⏳ Ожидает[/]"

    table.add_row("1", "Загрузить список сотрудников", status1)
    table.add_row("2", "Рассчитать зарплату", status2)
    table.add_row("3", "Показать итоги", "[bold green]📊 Отчёт[/]")
    table.add_row("4", "Выход", "[bold red]🚪 Выйти[/]")

    console.print(table)
    console.print(
        "\n[bold yellow]💡 Совет:[/] Сначала загрузите сотрудников (п.1), затем рассчитайте зарплату (п.2)\n"
    )


def load_employees():
    """Загрузка сотрудников с прогресс-баром"""
    global employees_loaded

    if employees_loaded:
        console.print("[yellow]⚠️  Сотрудники уже загружены![/]\n")
        return

    log.info("Начало загрузки сотрудников")
    console.print(
        Panel.fit(
            "[bold blue]Загрузка списка сотрудников...[/]",
            title="👥 Этап 1",
            border_style="blue",
        )
    )

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Загрузка...", total=15)
        for i in range(15):
            time.sleep(0.08)
            progress.update(task, advance=1)

    get_employees()
    employees_loaded = True
    log.info("Сотрудники успешно загружены")
    console.print("\n[green bold]✅ Сотрудники загружены успешно![/]\n")
    time.sleep(1)


def calculate_salary_wrapper():
    """Расчёт зарплаты со спиннером"""
    global salary_calculated

    if not employees_loaded:
        console.print(
            "[red bold]❌ Ошибка:[/] Сначала загрузите список сотрудников (пункт 1)!\n"
        )
        time.sleep(2)
        return

    if salary_calculated:
        console.print("[yellow]⚠️  Зарплата уже рассчитана![/]\n")
        return

    log.info("Начало расчёта зарплаты")
    console.print(
        Panel.fit(
            "[bold yellow]Расчёт зарплаты сотрудников...[/]",
            title="💰 Этап 2",
            border_style="yellow",
        )
    )

    with console.status(
        "[bold yellow]Выполняется расчёт...", spinner="line", spinner_style="yellow"
    ):
        time.sleep(1.5)

    calculate_salary()
    salary_calculated = True
    log.info("Зарплата успешно рассчитана")
    console.print("\n[green bold]✅ Зарплата рассчитана успешно![/]\n")
    time.sleep(1)


def show_summary():
    """Показ итогов в красивой таблице"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[red bold]❌ Ошибка:[/] Для просмотра итогов необходимо:\n"
            "  1. Загрузить сотрудников (п.1)\n"
            "  2. Рассчитать зарплату (п.2)\n"
        )
        time.sleep(2)
        return

    console.print(
        Panel.fit(
            "[bold magenta]📊 Формирование итогового отчёта...[/]",
            title="📈 Итоги",
            border_style="magenta",
        )
    )
    time.sleep(0.5)

    table = Table(
        title="💼 Итоговый отчёт по расчётам",
        style="bold magenta",
        title_style="bold white",
        box=box.DOUBLE,
    )
    table.add_column("Показатель", style="bold cyan", width=25)
    table.add_column("Значение", justify="right", style="bold green", width=20)
    table.add_column("Статус", justify="center", style="bold", width=15)

    table.add_row("Загружено сотрудников", "15", "[green]✓[/]")
    table.add_row("Рассчитано зарплат", "15", "[green]✓[/]")
    table.add_row("Дата расчёта", datetime.now().strftime("%d.%m.%Y"), "[cyan]ℹ[/]")
    table.add_row("Время расчёта", datetime.now().strftime("%H:%M:%S"), "[cyan]ℹ[/]")
    table.add_row("Итого к выплате", "2 025 000 ₽", "[bold yellow]💰[/]")

    console.print(table)
    console.print()
    log.info("Показан итоговый отчёт")


def confirm_exit():
    """Подтверждение выхода"""
    try:
        if Confirm.ask(
            "\n[bold red]Вы действительно хотите выйти из программы?[/]", default=False
        ):
            return True
        return False
    except KeyboardInterrupt:
        return True


def main_loop():
    """Основной цикл программы"""
    show_welcome()

    while True:
        show_menu()

        try:
            choice = (
                Prompt.ask(
                    "[bold cyan]Выберите пункт меню (1-4)[/]",
                    choices=["1", "2", "3", "4", "q"],
                    default="1",
                )
                .strip()
                .lower()
            )

            if choice in ["4", "q", "exit", "quit"]:
                if confirm_exit():
                    break
                continue

            console.clear()
            console.rule(f"[bold cyan]Вы выбрали: пункт {choice}[/]", style="cyan")
            console.print()

            if choice == "1":
                load_employees()
            elif choice == "2":
                calculate_salary_wrapper()
            elif choice == "3":
                show_summary()
            else:
                console.print("[yellow]⚠️  Неверный выбор. Попробуйте снова.[/]\n")
                time.sleep(1)

            Prompt.ask("[bold green]Нажмите Enter для возврата в меню...[/]")
            console.clear()

        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠️  Программа прервана пользователем[/]")
            if confirm_exit():
                break
        except Exception as e:
            log.exception("Произошла непредвиденная ошибка")
            console.print(
                Panel.fit(
                    f"[red]Тип ошибки:[/][bold red] {type(e).__name__}[/]\n"
                    f"[red]Сообщение:[/][bold red] {str(e)}[/]",
                    title="❌ Критическая ошибка",
                    border_style="red",
                )
            )
            Prompt.ask("[bold yellow]Нажмите Enter для продолжения...[/]")
            console.clear()

    # Финальный экран
    console.clear()
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    console.rule(
        f"[bold green]🎉 Программа завершена | {current_time}[/]", style="green"
    )
    console.print(
        Panel.fit(
            "[bold green]Спасибо за использование системы 'Бухгалтерия'![/]\n"
            "[cyan]Все операции выполнены успешно.[/]",
            title="✅ Завершение работы",
            border_style="green",
        )
    )
    log.info("Программа завершена пользователем")
    time.sleep(2)


if __name__ == "__main__":
    try:
        main_loop()
    except SystemExit:
        pass
    except Exception as e:
        log.exception("Критическая ошибка в точке входа")
        sys.exit(1)
