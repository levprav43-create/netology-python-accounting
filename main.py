#!/usr/bin/env python3
"""
Бухгалтерия v4.0 — профессиональное консольное приложение
с графиками, CLI-режимом, экспортами и полной статистикой
"""
import argparse
import csv
import json
import os
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Dict

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
from rich.theme import Theme
from rich.tree import Tree
from rich.syntax import Syntax
from rich.markdown import Markdown
from application.salary import calculate_salary
from application.db.people import get_employees

# Установка красивых трейсбэков
install(show_locals=True)

# Темы интерфейса
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
            "chart": "bold yellow",
            "chart_bar": "bold green",
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
            "chart": "bold cyan",
            "chart_bar": "bold blue",
        }
    ),
}

# Глобальные переменные
CURRENT_THEME = "light"
console = Console(theme=THEMES[CURRENT_THEME], record=True, width=120)

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

# Состояние приложения
employees_loaded = False
salary_calculated = False
operations_history: List[Dict] = []
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# Данные для графиков и статистики
DEPARTMENTS = {
    "Разработчики": {"count": 5, "total_salary": 758000, "avg_salary": 151600},
    "Дизайнеры": {"count": 3, "total_salary": 353000, "avg_salary": 117667},
    "Тестировщики": {"count": 3, "total_salary": 293000, "avg_salary": 97667},
    "Аналитики": {"count": 2, "total_salary": 275000, "avg_salary": 137500},
    "Менеджеры": {"count": 2, "total_salary": 255000, "avg_salary": 127500},
}


def show_ascii_logo():
    """ASCII-арт логотип"""
    logo = r"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗   ██╗███████╗██████╗  █████╗ ██╗     ██╗     ██████╗ ██████╗  ║
║  ██╔══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██║     ██║     ██╔══██╗██╔══██╗ ║
║  ██████╔╝██║   ██║█████╗  ██████╔╝███████║██║     ██║     ██████╔╝██████╔╝ ║
║  ██╔══██╗██║   ██║██╔══╝  ██╔══██╗██╔══██║██║     ██║     ██╔═══╝ ██╔══██╗ ║
║  ██████╔╝╚██████╔╝███████╗██║  ██║██║  ██║███████╗███████╗██║     ██║  ██║ ║
║  ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝ ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{logo}[/]")
    time.sleep(0.5)


def show_welcome():
    """Приветственный экран с логотипом"""
    console.clear()
    show_ascii_logo()
    console.rule(
        f"[header]💼 БУХГАЛТЕРИЯ v4.0 | Тема: {CURRENT_THEME}[/]", style="bold white"
    )
    console.print(
        Panel.fit(
            f"[success]Добро пожаловать в систему учёта персонала![/]\n"
            f"Текущее время: [info]{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}[/]\n"
            f"Версия Python: [cyan]{sys.version.split()[0]}[/]",
            title="📅 Система запущена",
            border_style="success",
            padding=(1, 2),
        )
    )
    time.sleep(1.0)


def show_menu():
    """Главное меню"""
    console.print("\n")
    table = Table(
        title="📋 Главное меню", box=box.ROUNDED, style="menu", title_style="bold menu"
    )
    table.add_column("№", style="bold cyan", justify="center", width=4)
    table.add_column("Действие", style="bold white", width=38)
    table.add_column("Статус", justify="center", width=15)

    status1 = "[success]✓ Готово[/]" if employees_loaded else "[warning]⏳ Ожидает[/]"
    status2 = "[success]✓ Готово[/]" if salary_calculated else "[warning]⏳ Ожидает[/]"

    table.add_row("1", "Загрузить список сотрудников", status1)
    table.add_row("2", "Рассчитать зарплату", status2)
    table.add_row(
        "3", "📊 Показать статистику и графики", "[bold magenta]📈 Графики[/]"
    )
    table.add_row("4", "💾 Сохранить отчёт (JSON)", "[bold cyan]JSON[/]")
    table.add_row("5", "📄 Сохранить отчёт (TXT)", "[bold blue]TXT[/]")
    table.add_row("6", "📈 Экспортировать в CSV", "[bold yellow]CSV[/]")
    table.add_row("7", "🌐 Экспортировать в HTML", "[bold red]HTML[/]")
    table.add_row("8", "🕒 Показать историю операций", "[bold magenta]История[/]")
    table.add_row(
        "9", "🎨 Сменить тему (светлая/тёмная)", f"[bold yellow]{CURRENT_THEME}[/]"
    )
    table.add_row("0", "🚪 Выход", "[bold red]Выйти[/]")

    console.print(table)
    console.print(
        "\n[warning]💡 Совет:[/] Выполните пункты 1 → 2 → 3 для полного цикла работы\n"
    )


def load_employees():
    """Загрузка сотрудников"""
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
            time.sleep(0.06)
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
    """Расчёт зарплаты"""
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
        time.sleep(1.0)

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


def show_statistics():
    """Показ статистики и текстовых графиков"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[error bold]❌ Ошибка:[/] Для просмотра статистики необходимо:\n"
            "  1. Загрузить сотрудников (п.1)\n"
            "  2. Рассчитать зарплату (п.2)\n"
        )
        time.sleep(2)
        return

    console.print(
        Panel.fit(
            "[magenta]📊 Формирование статистики и графиков...[/]",
            title="📈 Статистика",
            border_style="magenta",
            padding=(1, 2),
        )
    )
    time.sleep(0.7)

    # Итоговая таблица
    current_time = datetime.now()
    table = Table(
        title="💼 Итоговый отчёт",
        style="bold magenta",
        title_style="bold white",
        box=box.DOUBLE,
    )
    table.add_column("Показатель", style="bold cyan", width=25)
    table.add_column("Значение", justify="right", style="bold green", width=20)

    table.add_row("Всего сотрудников", "15")
    table.add_row("Рассчитано зарплат", "15")
    table.add_row("Дата расчёта", current_time.strftime("%d.%m.%Y"))
    table.add_row("Время расчёта", current_time.strftime("%H:%M:%S"))
    table.add_row("Итого к выплате", "2 025 000 ₽")
    table.add_row("Средняя зарплата", "135 000 ₽")

    console.print(table)
    console.print()

    # График по департаментам (текстовый)
    console.print(
        Panel.fit(
            "[chart]Структура по департаментам (средняя зарплата):[/]",
            style="chart",
            padding=(0, 1),
        )
    )

    max_salary = max(d["avg_salary"] for d in DEPARTMENTS.values())
    for dept, data in DEPARTMENTS.items():
        bar_length = int((data["avg_salary"] / max_salary) * 40)
        bar = "█" * bar_length
        console.print(
            f"[bold]{dept:18s}[/] [chart_bar]{bar}[/] [bold green]{data['avg_salary']:>7,} ₽[/]"
        )

    console.print()
    time.sleep(1)


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
        "report_type": "Бухгалтерия - Итоговый отчёт v4.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "theme": CURRENT_THEME,
        "employees_loaded": employees_loaded,
        "salary_calculated": salary_calculated,
        "summary": {
            "total_employees": 15,
            "salaries_calculated": 15,
            "total_amount": "2 025 000 ₽",
            "average_salary": "135 000 ₽",
            "departments": DEPARTMENTS,
        },
        "operations_history": operations_history,
    }

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        console.print(
            f"[success]✅ Отчёт сохранён:[/]\n[bold cyan]{filename.absolute()}[/]\n"
        )
        log.info(f"Отчёт сохранён в JSON: {filename.name}")
        time.sleep(1.5)
    except Exception as e:
        console.print(f"[error]❌ Ошибка сохранения JSON:[/] {str(e)}\n")
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
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                          БУХГАЛТЕРИЯ - ИТОГОВЫЙ ОТЧЁТ v4.0                                   ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║ Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}                                              ║
║ Тема интерфейса: {CURRENT_THEME.capitalize()}                                                              ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║ СОТРУДНИКИ                                                                                   ║
║   • Всего: 15                                                                                ║
║   • Статус: ✅ Успешно                                                                       ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║ ЗАРПЛАТА                                                                                     ║
║   • Рассчитано: 15 записей                                                                   ║
║   • Итого к выплате: 2 025 000 ₽                                                             ║
║   • Средняя зарплата: 135 000 ₽                                                              ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║ ДЕПАРТАМЕНТЫ                                                                                 ║
"""

    for dept, data in DEPARTMENTS.items():
        content += f"║   • {dept:18s} | Сотрудников: {data['count']:2d} | Средняя: {data['avg_salary']:>7,} ₽ ║\n"

    content += "╚══════════════════════════════════════════════════════════════════════════════════════════════╝\n"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(
            f"[success]✅ Отчёт сохранён:[/]\n[bold cyan]{filename.absolute()}[/]\n"
        )
        log.info(f"Отчёт сохранён в TXT: {filename.name}")
        time.sleep(1.5)
    except Exception as e:
        console.print(f"[error]❌ Ошибка сохранения TXT:[/] {str(e)}\n")
        log.error(f"Ошибка сохранения TXT: {e}")
        time.sleep(2)


def export_to_csv():
    """Экспорт в CSV"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[error]❌ Невозможно экспортировать: сначала выполните пункты 1 и 2![/]\n"
        )
        time.sleep(2)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = REPORTS_DIR / f"employees_{timestamp}.csv"

    employees_data = [
        ["ID", "ФИО", "Должность", "Департамент", "Зарплата (₽)", "Статус"],
        [
            "1",
            "Иванов Иван Иванович",
            "Разработчик",
            "Разработчики",
            "150000",
            "Активен",
        ],
        ["2", "Петрова Мария Сергеевна", "Дизайнер", "Дизайнеры", "120000", "Активен"],
        [
            "3",
            "Сидоров Алексей Владимирович",
            "Тестировщик",
            "Тестировщики",
            "100000",
            "Активен",
        ],
        ["4", "Козлова Анна Дмитриевна", "Аналитик", "Аналитики", "140000", "Активен"],
        [
            "5",
            "Смирнов Дмитрий Алексеевич",
            "Разработчик",
            "Разработчики",
            "160000",
            "Активен",
        ],
        [
            "6",
            "Волкова Екатерина Павловна",
            "Менеджер",
            "Менеджеры",
            "130000",
            "Активен",
        ],
        [
            "7",
            "Морозов Сергей Игоревич",
            "Разработчик",
            "Разработчики",
            "145000",
            "Активен",
        ],
        [
            "8",
            "Новикова Ольга Викторовна",
            "Дизайнер",
            "Дизайнеры",
            "115000",
            "Активен",
        ],
        [
            "9",
            "Лебедев Максим Юрьевич",
            "Тестировщик",
            "Тестировщики",
            "95000",
            "Активен",
        ],
        [
            "10",
            "Кузнецова Татьяна Андреевна",
            "Аналитик",
            "Аналитики",
            "135000",
            "Активен",
        ],
        [
            "11",
            "Попов Артём Сергеевич",
            "Разработчик",
            "Разработчики",
            "155000",
            "Активен",
        ],
        [
            "12",
            "Федорова Дарья Михайловна",
            "Менеджер",
            "Менеджеры",
            "125000",
            "Активен",
        ],
        [
            "13",
            "Гусев Павел Николаевич",
            "Разработчик",
            "Разработчики",
            "148000",
            "Активен",
        ],
        [
            "14",
            "Соколова Виктория Александровна",
            "Дизайнер",
            "Дизайнеры",
            "118000",
            "Активен",
        ],
        [
            "15",
            "Виноградов Игорь Валерьевич",
            "Тестировщик",
            "Тестировщики",
            "98000",
            "Активен",
        ],
    ]

    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(employees_data)
        console.print(
            f"[success]✅ Данные экспортированы в CSV:[/]\n[bold cyan]{filename.absolute()}[/]\n"
        )
        log.info(f"Данные экспортированы в CSV: {filename.name}")
        time.sleep(1.5)
    except Exception as e:
        console.print(f"[error]❌ Ошибка экспорта CSV:[/] {str(e)}\n")
        log.error(f"Ошибка экспорта CSV: {e}")
        time.sleep(2)


def export_to_html():
    """Экспорт в HTML с графиками"""
    if not employees_loaded or not salary_calculated:
        console.print(
            "[error]❌ Невозможно экспортировать: сначала выполните пункты 1 и 2![/]\n"
        )
        time.sleep(2)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = REPORTS_DIR / f"report_{timestamp}.html"

    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Бухгалтерия v4.0 - Отчёт</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 30px 0; }}
        .metric {{ text-align: center; padding: 15px; background: #ecf0f1; border-radius: 8px; width: 150px; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #3498db; }}
        .metric-label {{ color: #7f8c8d; margin-top: 5px; }}
        .chart {{ margin: 30px 0; }}
        .bar {{ height: 30px; background: #3498db; margin: 10px 0; border-radius: 5px; position: relative; }}
        .bar-label {{ position: absolute; left: 10px; top: 5px; color: white; font-weight: bold; }}
        .bar-value {{ position: absolute; right: 10px; top: 5px; color: white; font-weight: bold; }}
        .footer {{ text-align: center; margin-top: 40px; color: #7f8c8d; font-style: italic; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💼 Бухгалтерия v4.0 — Итоговый отчёт</h1>
        <div class="summary">
            <div class="metric">
                <div class="metric-value">15</div>
                <div class="metric-label">Сотрудников</div>
            </div>
            <div class="metric">
                <div class="metric-value">2 025 000 ₽</div>
                <div class="metric-label">Итого к выплате</div>
            </div>
            <div class="metric">
                <div class="metric-value">135 000 ₽</div>
                <div class="metric-label">Средняя зарплата</div>
            </div>
        </div>
        
        <h2>📊 Статистика по департаментам</h2>
        <div class="chart">
            <div class="bar" style="width: 95%;">
                <div class="bar-label">Разработчики</div>
                <div class="bar-value">151 600 ₽</div>
            </div>
            <div class="bar" style="width: 78%;">
                <div class="bar-label">Аналитики</div>
                <div class="bar-value">137 500 ₽</div>
            </div>
            <div class="bar" style="width: 84%;">
                <div class="bar-label">Менеджеры</div>
                <div class="bar-value">127 500 ₽</div>
            </div>
            <div class="bar" style="width: 77%;">
                <div class="bar-label">Дизайнеры</div>
                <div class="bar-value">117 667 ₽</div>
            </div>
            <div class="bar" style="width: 64%;">
                <div class="bar-label">Тестировщики</div>
                <div class="bar-value">97 667 ₽</div>
            </div>
        </div>
        
        <h2>👥 Список сотрудников</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>ФИО</th>
                <th>Должность</th>
                <th>Департамент</th>
                <th>Зарплата</th>
            </tr>
            <tr><td>1</td><td>Иванов Иван Иванович</td><td>Разработчик</td><td>Разработчики</td><td>150 000 ₽</td></tr>
            <tr><td>2</td><td>Петрова Мария Сергеевна</td><td>Дизайнер</td><td>Дизайнеры</td><td>120 000 ₽</td></tr>
            <tr><td>3</td><td>Сидоров Алексей Владимирович</td><td>Тестировщик</td><td>Тестировщики</td><td>100 000 ₽</td></tr>
            <tr><td>4</td><td>Козлова Анна Дмитриевна</td><td>Аналитик</td><td>Аналитики</td><td>140 000 ₽</td></tr>
            <tr><td>5</td><td>Смирнов Дмитрий Алексеевич</td><td>Разработчик</td><td>Разработчики</td><td>160 000 ₽</td></tr>
            <tr><td>6</td><td>Волкова Екатерина Павловна</td><td>Менеджер</td><td>Менеджеры</td><td>130 000 ₽</td></tr>
            <tr><td>7</td><td>Морозов Сергей Игоревич</td><td>Разработчик</td><td>Разработчики</td><td>145 000 ₽</td></tr>
            <tr><td>8</td><td>Новикова Ольга Викторовна</td><td>Дизайнер</td><td>Дизайнеры</td><td>115 000 ₽</td></tr>
            <tr><td>9</td><td>Лебедев Максим Юрьевич</td><td>Тестировщик</td><td>Тестировщики</td><td>95 000 ₽</td></tr>
            <tr><td>10</td><td>Кузнецова Татьяна Андреевна</td><td>Аналитик</td><td>Аналитики</td><td>135 000 ₽</td></tr>
            <tr><td>11</td><td>Попов Артём Сергеевич</td><td>Разработчик</td><td>Разработчики</td><td>155 000 ₽</td></tr>
            <tr><td>12</td><td>Федорова Дарья Михайловна</td><td>Менеджер</td><td>Менеджеры</td><td>125 000 ₽</td></tr>
            <tr><td>13</td><td>Гусев Павел Николаевич</td><td>Разработчик</td><td>Разработчики</td><td>148 000 ₽</td></tr>
            <tr><td>14</td><td>Соколова Виктория Александровна</td><td>Дизайнер</td><td>Дизайнеры</td><td>118 000 ₽</td></tr>
            <tr><td>15</td><td>Виноградов Игорь Валерьевич</td><td>Тестировщик</td><td>Тестировщики</td><td>98 000 ₽</td></tr>
        </table>
        
        <div class="footer">
            <p>Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} | Бухгалтерия v4.0</p>
        </div>
    </div>
</body>
</html>
"""

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        console.print(
            f"[success]✅ Отчёт экспортирован в HTML:[/]\n[bold cyan]{filename.absolute()}[/]\n"
        )

        # Автоматическое открытие в браузере (только если не в CI/CD)
        if not os.environ.get("CI"):
            webbrowser.open(filename.absolute().as_uri())
            console.print("[info]🌐 HTML-отчёт автоматически открыт в браузере[/]\n")

        log.info(f"Отчёт экспортирован в HTML: {filename.name}")
        time.sleep(2)
    except Exception as e:
        console.print(f"[error]❌ Ошибка экспорта HTML:[/] {str(e)}\n")
        log.error(f"Ошибка экспорта HTML: {e}")
        time.sleep(2)


def show_history():
    """История операций"""
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
    table.add_column("Операция", style="bold white", width=28)
    table.add_column("Время", style="bold yellow", width=20)
    table.add_column("Длительность", justify="right", style="bold green", width=12)
    table.add_column("Статус", justify="center", width=8)

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
    """Смена темы"""
    global CURRENT_THEME, console

    new_theme = "dark" if CURRENT_THEME == "light" else "light"
    CURRENT_THEME = new_theme
    console = Console(theme=THEMES[CURRENT_THEME], record=True, width=120)

    console.clear()
    console.print(
        f"[success]🎨 Тема изменена на: [bold]{new_theme.capitalize()}[/][/]\n"
    )
    log.info(f"Тема изменена на {new_theme}")
    time.sleep(1.2)


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
                    "[bold cyan]Выберите пункт меню (0-9)[/]",
                    choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "q"],
                    default="1",
                )
                .strip()
                .lower()
            )

            if choice in ["0", "q", "exit", "quit"]:
                if confirm_exit():
                    break
                continue

            console.clear()
            console.rule(f"[bold cyan]Вы выбрали: пункт {choice}[/]", style="cyan")
            console.print()

            actions = {
                "1": load_employees,
                "2": calculate_salary_wrapper,
                "3": show_statistics,
                "4": save_report_json,
                "5": save_report_txt,
                "6": export_to_csv,
                "7": export_to_html,
                "8": show_history,
                "9": switch_theme,
            }

            if choice in actions:
                if choice == "9":
                    switch_theme()
                    continue
                else:
                    actions[choice]()
            else:
                console.print("[yellow]⚠️  Неверный выбор. Попробуйте снова.[/]\n")
                time.sleep(1)

            if choice != "9":
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
    show_ascii_logo()
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    console.rule(
        f"[footer]🎉 Программа завершена | {current_time}[/]", style="bold white"
    )
    console.print(
        Panel.fit(
            f"[success]Спасибо за использование системы 'Бухгалтерия'![/]\n"
            f"[info]Все отчёты сохранены в:[/]\n"
            f"[bold cyan]{REPORTS_DIR.absolute()}[/]\n"
            f"[info]Выполнено операций:[/] [bold]{len(operations_history)}[/]",
            title="✅ Завершение работы",
            border_style="success",
            padding=(1, 2),
        )
    )
    log.info("Программа завершена пользователем")
    time.sleep(2.5)


def cli_mode(args):
    """Режим командной строки (без интерактивного меню)"""
    global CURRENT_THEME, console

    if args.theme:
        CURRENT_THEME = args.theme
        console = Console(theme=THEMES[CURRENT_THEME], record=True, width=120)

    console.print(f"[bold cyan]Запуск в CLI-режиме (тема: {CURRENT_THEME})[/]\n")

    if args.load:
        console.print("[info]→ Загрузка сотрудников...[/]")
        load_employees()

    if args.calculate:
        if not employees_loaded:
            console.print("[warning]⚠️  Сотрудники не загружены. Пропускаем расчёт.[/]")
        else:
            console.print("[info]→ Расчёт зарплаты...[/]")
            calculate_salary_wrapper()

    if args.stats and salary_calculated:
        console.print("[info]→ Генерация статистики...[/]")
        show_statistics()

    if args.export == "json" and salary_calculated:
        console.print("[info]→ Экспорт в JSON...[/]")
        save_report_json()
    elif args.export == "csv" and salary_calculated:
        console.print("[info]→ Экспорт в CSV...[/]")
        export_to_csv()
    elif args.export == "html" and salary_calculated:
        console.print("[info]→ Экспорт в HTML...[/]")
        export_to_html()
    elif args.export and salary_calculated:
        console.print(f"[warning]⚠️  Неизвестный формат экспорта: {args.export}[/]")

    if not (args.load or args.calculate or args.export or args.stats):
        console.print(
            "[yellow]ℹ️  Укажите действия: --load, --calculate, --export [json/csv/html], --stats[/]"
        )

    console.print("\n[success]✅ CLI-режим завершён[/]")


def main():
    """Точка входа с поддержкой CLI и интерактивного режима"""
    parser = argparse.ArgumentParser(
        description="Бухгалтерия v4.0 — система учёта персонала",
        epilog="Примеры:\n"
        "  python main.py --load --calculate --export json\n"
        "  python main.py --theme dark --stats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--load", action="store_true", help="Загрузить список сотрудников"
    )
    parser.add_argument("--calculate", action="store_true", help="Рассчитать зарплату")
    parser.add_argument(
        "--stats", action="store_true", help="Показать статистику и графики"
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv", "html"],
        help="Экспортировать отчёт в указанный формат",
    )
    parser.add_argument(
        "--theme",
        choices=["light", "dark"],
        default="light",
        help="Выбрать тему интерфейса (по умолчанию: light)",
    )
    parser.add_argument("--version", action="version", version="Бухгалтерия v4.0")

    args = parser.parse_args()

    # Если переданы аргументы — запускаем CLI-режим
    if any([args.load, args.calculate, args.export, args.stats, args.theme != "light"]):
        cli_mode(args)
    else:
        # Иначе — интерактивный режим
        try:
            main_loop()
        except SystemExit:
            pass
        except Exception as e:
            log.exception("Критическая ошибка в точке входа")
            sys.exit(1)


if __name__ == "__main__":
    main()
