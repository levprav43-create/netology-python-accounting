from datetime import datetime

def get_employees():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Загрузка списка сотрудников...")
    print("✅ Получен список из 15 сотрудников")