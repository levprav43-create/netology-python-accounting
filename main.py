from datetime import datetime
from application.salary import calculate_salary
from application.db.people import get_employees

if __name__ == '__main__':
    print("=" * 50)
    print(f"📅 Старт программы 'Бухгалтерия' | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 50)
    print()
    
    get_employees()
    print()
    calculate_salary()
    
    print()
    print("=" * 50)
    print(f"✅ Программа завершена | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 50)