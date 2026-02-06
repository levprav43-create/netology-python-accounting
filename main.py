from datetime import datetime
import time
import sys
import os
import json
import csv
import logging
from pathlib import Path
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
from rich.theme import Theme
from application.salary import calculate_salary
from application.db.people import get_employees

# Установка красивых трейсбэков для ошибок
install(show_locals=True)

# Поддержка тем: светлая и тёмная
THEMES = {
    "light": Theme(
        {
            "info": "bold cyan",
            "warning": "bold yellow",
            "error": "bold red",
            "success": "bold green",
            "menu": "bold blue",
            "header": "bold cyan on #f0f0f0",
            "footer": "bold green on #f0f0f0",
        }
    ),
    "dark": Theme(
        {
            "info": "bold cyan",
            "warning": "bold yellow",
            "error": "bold red",
            "success": "bold green",
            "menu": "bold magenta",
            "header": "bold white on #1a1a1a",
            "footer": "bold white on #1a1a1a",
        }
    ),
}

# Выбор темы (можно изменить на "dark")
CURRENT_THEME = "light"
console = Console(theme=THEMES[CURRENT_THEME], record=True)

# Настройка логирования
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            rich_tracebacks=True, console=console, show_time=True, show_path=False
        )
    ],
)
log = logging.getLogger("accounting")

# Глобальные флаги состояния
employees_loaded = False
salary_calculated = False
operations_history = []

# Папка для отчётов
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def show_welcome():
    """Приветственный экран"""
    console.clear()
    console.rule(
        f"[header]💼 БУХГАЛТЕРИЯ v3.0 | Тема: {CURRENT_THEME}[/]", style="bold white"
    )
    console.print(
        Panel.fit(
            f"[success]Добро пожаловать в систему учёта персонала![/]\n"
            f"Текущее время: [info]{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}[/]",
            title="📅 Система запущена",
            border_style="success",
            padding=(1, 2),
        )
    )
    time.sleep(1.2)


def show_menu():
    """Отображение главного меню"""
    console.print("\n")
    table = Table(
        title="📋 Главное меню", box=box.ROUNDED, style="menu", title_style="bold menu"
    )
    table.add_column("№", style="bold cyan", justify="center", width=4)
    table.add_column("Действие", style="bold white", width=35)
    table.add_column("Статус", justify="center", width=15)

    status1 = "[success]✓ Готово[/]" if employees_loaded else "[warning]⏳ Ожидает[/]"
    status2 = "[success]✓ Готово[/]" if salary_calculated else "[warning]⏳ Ожидает[/]"

    table.add_row("1", "Загрузить список сотрудников", status1)
    table.add_row("2", "Рассчитать зарплату", status2)
    table.add_row("3", "Показать итоги", "[bold green]📊 Отчёт[/]")
    table.add_row("4", "Сохранить отчёт (JSON)", "[bold cyan]💾 JSON[/]")
    table.add_row("5", "Сохранить отчёт (TXT)", "[bold blue]📄 TXT[/]")
    table.add_row("6", "Экспортировать в CSV", "[bold yellow]📈 CSV[/]")
    table.add_row("7", "Показать историю операций", "[bold magenta]🕒 История[/]")
    table.add_row("8", "Сменить тему (светлая/тёмная)", "[bold yellow]🎨 Тема[/]")
    table.add_row("9", "Выход", "[bold red]🚪 Выйти[/]")

    console.print(table)
    console.print(
        "\n[warning]💡 Совет:[/] Сначала загрузите сотрудников (п.1), затем рассчитайте зарплату (п.2)\n"
    )


def load_employees():
    """Загрузка сотрудников с прогресс-баром"""
    global employees_loaded

    if employees_loaded:
        console.print("[warning]⚠️  Сотрудники уже загружены![/]\n")
        time.sleep(1.5)
        return

    start_time = time.time()
    log.info("Начало загрузки сотрудников")
    console.print(
        Panel.fit(
            "[info]Загрузка списка сотрудников из базы данных...[/]",
            title="👥 Этап 1",
            border_style="info",
            padding=(1, 2),
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
            time.sleep(0.07)
            progress.update(task, advance=1)

    get_employees()
    employees_loaded = True
    duration = time.time() - start_time
    operations_history.append(
        {
            "operation": "Загрузка сотрудников",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": round(duration, 2),
            "status": "success",
        }
    )
    log.info(f"Сотрудники успешно загружены за {duration:.2f} сек")
    console.print(
        f"\n[success bold]✅ Сотрудники загружены успешно за {duration:.2f} сек![/]\n"
    )
    time.sleep(1.5)


def calculate_salary_wrapper():
    """Расчёт зарплаты со спиннером"""
    global salary_calculated

    if not employees_loaded:
        console.print(
            "[error bold]❌ Ошибка:[/] Сначала загрузите список сотрудников (пункт 1)!\n"
        )
        time.sleep(2)
        return

    if salary_calculated:
        console.print("[warning]⚠️  Зарплата уже рассчитана![/]\n")
        time.sleep(1.5)
        return

    start_time = time.time()
    log.info("Начало расчёта зарплаты")
    console.print(
        Panel.fit(
            "[warning]Расчёт зарплаты сотрудников...[/]",
            title="💰 Этап 2",
            border_style="warning",
            padding=(1, 2),
        )
    )

    with console.status(
        "[bold yellow]Выполняется расчёт...", spinner="line", spinner_style="yellow"
    ):
        time.sleep(1.2)

    calculate_salary()
    salary_calculated = True
    duration = time.time() - start_time
    operations_history.append(
        {
            "operation": "Расчёт зарплаты",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": round(duration, 2),
            "status": "success",
        }
    )
    log.info(f"Зарплата успешно рассчитана за {duration:.2f} сек")
    console.print(
        f"\n[success bold]✅ Зарплата рассчитана успешно за {duration:.2f} сек![/]\n"
    )
    time.sleep(1.5)


def show_summary():
    """Показ итогов в красивой таблице"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[error bold]❌ Ошибка:[/] Для просмотра итогов необходимо:\n"
            "  1. Загрузить сотрудников (п.1)\n"
            "  2. Рассчитать зарплату (п.2)\n"
        )
        time.sleep(2)
        return

    console.print(
        Panel.fit(
            "[magenta]📊 Формирование итогового отчёта...[/]",
            title="📈 Итоги",
            border_style="magenta",
            padding=(1, 2),
        )
    )
    time.sleep(0.7)

    current_time = datetime.now()
    table = Table(
        title="💼 Итоговый отчёт по расчётам",
        style="bold magenta",
        title_style="bold white",
        box=box.DOUBLE,
        padding=(0, 1),
    )
    table.add_column("Показатель", style="bold cyan", width=28)
    table.add_column("Значение", justify="right", style="bold green", width=22)
    table.add_column("Статус", justify="center", style="bold", width=12)

    table.add_row("Загружено сотрудников", "15", "[success]✓[/]")
    table.add_row("Рассчитано зарплат", "15", "[success]✓[/]")
    table.add_row("Дата расчёта", current_time.strftime("%d.%m.%Y"), "[info]ℹ[/]")
    table.add_row("Время расчёта", current_time.strftime("%H:%M:%S"), "[info]ℹ[/]")
    table.add_row("Итого к выплате", "2 025 000 ₽", "[bold yellow]💰[/]")
    table.add_row("Средняя зарплата", "135 000 ₽", "[bold cyan]📊[/]")

    console.print(table)
    console.print()
    log.info("Показан итоговый отчёт")


def save_report_json():
    """Сохранение отчёта в JSON"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[error]❌ Невозможно сохранить отчёт: сначала выполните пункты 1 и 2![/]\n"
        )
        time.sleep(2)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = REPORTS_DIR / f"report_{timestamp}.json"

    report_data = {
        "report_type": "Бухгалтерия - Итоговый отчёт",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "theme": CURRENT_THEME,
        "employees_loaded": employees_loaded,
        "salary_calculated": salary_calculated,
        "summary": {
            "total_employees": 15,
            "salaries_calculated": 15,
            "total_amount": "2 025 000 ₽",
            "average_salary": "135 000 ₽",
        },
        "operations_history": operations_history,
    }

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        console.print(
            f"[success]✅ Отчёт успешно сохранён в:[/]\n[bold cyan]{filename.absolute()}[/]\n"
        )
        log.info(f"Отчёт сохранён в JSON: {filename.name}")
        time.sleep(2)
    except Exception as e:
        console.print(f"[error]❌ Ошибка при сохранении JSON:[/] {str(e)}\n")
        log.error(f"Ошибка сохранения JSON: {e}")
        time.sleep(2)


def save_report_txt():
    """Сохранение отчёта в TXT"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[error]❌ Невозможно сохранить отчёт: сначала выполните пункты 1 и 2![/]\n"
        )
        time.sleep(2)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = REPORTS_DIR / f"report_{timestamp}.txt"

    content = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    БУХГАЛТЕРИЯ - ИТОГОВЫЙ ОТЧЁТ                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}                          ║
║ Тема интерфейса: {CURRENT_THEME.capitalize()}                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ СОТРУДНИКИ                                                                   ║
║   • Загружено: 15                                                            ║
║   • Статус: ✅ Успешно                                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ЗАРПЛАТА                                                                     ║
║   • Рассчитано: 15 записей                                                   ║
║   • Итого к выплате: 2 025 000 ₽                                             ║
║   • Средняя зарплата: 135 000 ₽                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ИСТОРИЯ ОПЕРАЦИЙ                                                             ║
"""

    for i, op in enumerate(operations_history, 1):
        content += f"║   {i}. {op['operation']:25s} | {op['timestamp']:19s} | {op['duration_sec']:5.2f} сек ║\n"

    content += "╚══════════════════════════════════════════════════════════════════════════════╝\n"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(
            f"[success]✅ Отчёт успешно сохранён в:[/]\n[bold cyan]{filename.absolute()}[/]\n"
        )
        log.info(f"Отчёт сохранён в TXT: {filename.name}")
        time.sleep(2)
    except Exception as e:
        console.print(f"[error]❌ Ошибка при сохранении TXT:[/] {str(e)}\n")
        log.error(f"Ошибка сохранения TXT: {e}")
        time.sleep(2)


def export_to_csv():
    """Экспорт данных в CSV"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[error]❌ Невозможно экспортировать: сначала выполните пункты 1 и 2![/]\n"
        )
        time.sleep(2)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = REPORTS_DIR / f"employees_{timestamp}.csv"

    # Пример данных сотрудников
    employees_data = [
        ["ID", "ФИО", "Должность", "Зарплата (₽)", "Статус"],
        ["1", "Иванов Иван Иванович", "Разработчик", "150000", "Активен"],
        ["2", "Петрова Мария Сергеевна", "Дизайнер", "120000", "Активен"],
        ["3", "Сидоров Алексей Владимирович", "Тестировщик", "100000", "Активен"],
        ["4", "Козлова Анна Дмитриевна", "Аналитик", "140000", "Активен"],
        ["5", "Смирнов Дмитрий Алексеевич", "Разработчик", "160000", "Активен"],
        ["6", "Волкова Екатерина Павловна", "Менеджер", "130000", "Активен"],
        ["7", "Морозов Сергей Игоревич", "Разработчик", "145000", "Активен"],
        ["8", "Новикова Ольга Викторовна", "Дизайнер", "115000", "Активен"],
        ["9", "Лебедев Максим Юрьевич", "Тестировщик", "95000", "Активен"],
        ["10", "Кузнецова Татьяна Андреевна", "Аналитик", "135000", "Активен"],
        ["11", "Попов Артём Сергеевич", "Разработчик", "155000", "Активен"],
        ["12", "Федорова Дарья Михайловна", "Менеджер", "125000", "Активен"],
        ["13", "Гусев Павел Николаевич", "Разработчик", "148000", "Активен"],
        ["14", "Соколова Виктория Александровна", "Дизайнер", "118000", "Активен"],
        ["15", "Виноградов Игорь Валерьевич", "Тестировщик", "98000", "Активен"],
    ]

    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(employees_data)
        console.print(
            f"[success]✅ Данные экспортированы в CSV:[/]\n[bold cyan]{filename.absolute()}[/]\n"
        )
        log.info(f"Данные экспортированы в CSV: {filename.name}")
        time.sleep(2)
    except Exception as e:
        console.print(f"[error]❌ Ошибка при экспорте CSV:[/] {str(e)}\n")
        log.error(f"Ошибка экспорта CSV: {e}")
        time.sleep(2)


def show_history():
    """Показ истории операций"""
    if not operations_history:
        console.print(
            "[warning]🕒 История операций пуста. Выполните какие-либо действия.[/]\n"
        )
        time.sleep(2)
        return

    table = Table(
        title="🕒 История операций",
        box=box.ROUNDED,
        style="bold magenta",
        title_style="bold white",
    )
    table.add_column("№", style="bold cyan", justify="center", width=3)
    table.add_column("Операция", style="bold white", width=25)
    table.add_column("Время", style="bold yellow", width=20)
    table.add_column("Длительность", justify="right", style="bold green", width=15)
    table.add_column("Статус", justify="center", width=10)

    for i, op in enumerate(operations_history, 1):
        status_icon = "[success]✓[/]" if op["status"] == "success" else "[error]✗[/]"
        table.add_row(
            str(i),
            op["operation"],
            op["timestamp"],
            f"{op['duration_sec']:.2f} сек",
            status_icon,
        )

    console.print(table)
    console.print()
    time.sleep(2)


def switch_theme():
    """Смена темы интерфейса"""
    global CURRENT_THEME, console

    new_theme = "dark" if CURRENT_THEME == "light" else "light"
    CURRENT_THEME = new_theme
    console = Console(theme=THEMES[CURRENT_THEME], record=True)

    console.clear()
    console.print(
        f"[success]🎨 Тема успешно изменена на: [bold]{new_theme.capitalize()}[/][/]\n"
    )
    log.info(f"Тема изменена на {new_theme}")
    time.sleep(1.5)


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
                    "[bold cyan]Выберите пункт меню (1-9)[/]",
                    choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "q"],
                    default="1",
                )
                .strip()
                .lower()
            )

            if choice in ["9", "q", "exit", "quit"]:
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
            elif choice == "4":
                save_report_json()
            elif choice == "5":
                save_report_txt()
            elif choice == "6":
                export_to_csv()
            elif choice == "7":
                show_history()
            elif choice == "8":
                switch_theme()
                # После смены темы нужно обновить экран
                continue
            else:
                console.print("[yellow]⚠️  Неверный выбор. Попробуйте снова.[/]\n")
                time.sleep(1)

            if choice != "8":  # Не показывать паузу после смены темы
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
                    padding=(1, 2),
                )
            )
            Prompt.ask("[bold yellow]Нажмите Enter для продолжения...[/]")
            console.clear()

    # Финальный экран
    console.clear()
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    console.rule(
        f"[footer]🎉 Программа завершена | {current_time}[/]", style="bold white"
    )
    console.print(
        Panel.fit(
            f"[success]Спасибо за использование системы 'Бухгалтерия'![/]\n"
            f"[info]Все отчёты сохранены в папку:[/]\n"
            f"[bold cyan]{REPORTS_DIR.absolute()}[/]\n"
            f"[info]Выполнено операций:[/] [bold]{len(operations_history)}[/]",
            title="✅ Завершение работы",
            border_style="success",
            padding=(1, 2),
        )
    )
    log.info("Программа завершена пользователем")
    time.sleep(2.5)


if __name__ == "__main__":
    try:
        main_loop()
    except SystemExit:
        pass
    except Exception as e:
        log.exception("Критическая ошибка в точке входа")
        sys.exit(1)
