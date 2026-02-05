from datetime import datetime
from application.salary import *
from application.db.people import *

if __name__ == '__main__':
    print(f"\n⚠️  Запуск через 'грязный' импорт (не рекомендуется в продакшене)")
    print(f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
    
    get_employees()
    calculate_salary()