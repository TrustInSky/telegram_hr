import io
import os
import pandas as pd
import tempfile
from sqlalchemy.orm import Session
from app.database.models import User, AnonymousQuestion
from app.database.database import AsyncSession
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from datetime import datetime
from app.repositories.catalog_repo import CatalogRepo
import re

def user_create_excel_file(users: list[User]) -> bytes:
    data = [
        {
            "Full Name": user.fullname,
            "Username": user.username or "",
            "Telegram ID": user.telegram_id,
            "T-Points": user.tpoints,
            "Department": user.department,
            "Post": user.post,
            "Birth Date": user.birth_date,
            "Hire Date": user.hire_date,
            "Active": int(user.is_active),
        }
        for user in users
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()


async def parse_excel_file(file_path: str, db: AsyncSession) -> dict:
    print(f"[DEBUG] parse_excel_file вызвана с путем: {file_path}")
    try:
        # Проверка существования файла
        if not os.path.exists(file_path):
            print(f"[ERROR] Файл не существует: {file_path}")
            return {"success": False, "message": "Файл не найден"}
            
        print(f"Начинаем обработку файла: {file_path}")
        
        # Читаем Excel с обработкой дат
        df = pd.read_excel(file_path, parse_dates=["Birth Date", "Hire Date"])
        print(f"Файл успешно прочитан. Найдено {len(df)} записей")
        print(f"Columns: {df.columns.tolist()}")
        
        # Выводим первые несколько строк для проверки
        print("Пример данных:")
        print(df.head(2))
        
        # Проверяем наличие всех необходимых столбцов
        required_columns = ["Full Name", "Telegram ID", "T-Points", 
                            "Department", "Post", "Birth Date", "Hire Date", "Active"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ОШИБКА: Отсутствуют столбцы: {', '.join(missing_columns)}")
            return {"success": False, "message": f"Отсутствуют столбцы: {', '.join(missing_columns)}"}
        
        # Счетчики
        updated = 0
        errors = 0
        error_messages = []
        
        print("Начинаем обработку записей...")
        # Обрабатываем каждую строку
        for index, row in df.iterrows():
            try:
                telegram_id = row["Telegram ID"]
                print(f"Обработка записи {index+1}/{len(df)}: Telegram ID {telegram_id}")
                
                # Используем select вместо query
                from sqlalchemy import select
                from app.database.models import User
                
                # Получаем пользователя по Telegram ID или создаем нового
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    print(f"Создаем нового пользователя с Telegram ID {telegram_id}")
                    user = User(telegram_id=telegram_id)
                    db.add(user)
                else:
                    print(f"Обновляем существующего пользователя с Telegram ID {telegram_id}")
                
                # Обновляем данные пользователя
                user.fullname = row["Full Name"]
                user.username = row["Username"] if not pd.isna(row.get("Username", None)) else None
                user.tpoints = int(row["T-Points"]) if not pd.isna(row.get("T-Points", None)) else 0
                user.department = row["Department"] if not pd.isna(row.get("Department", None)) else None
                user.post = row["Post"] if not pd.isna(row.get("Post", None)) else None
                user.birth_date = row["Birth Date"] if not pd.isna(row.get("Birth Date", None)) else None
                user.hire_date = row["Hire Date"] if not pd.isna(row.get("Hire Date", None)) else None
                user.is_active = bool(row["Active"]) if not pd.isna(row.get("Active", None)) else True
                
                print(f"Данные пользователя успешно обновлены")
                updated += 1
            except Exception as e:
                errors += 1
                error_message = f"Ошибка в строке {index+1} (Telegram ID {row.get('Telegram ID', 'неизвестно')}): {str(e)}"
                print(f"ОШИБКА: {error_message}")
                error_messages.append(error_message)
        
        # Сохраняем изменения в базе данных
        print(f"Сохраняем изменения в базе данных...")
        await db.commit()
        print(f"Изменения сохранены. Обновлено записей: {updated}, ошибок: {errors}")
        
        result = {
            "success": True,
            "updated": updated,
            "errors": errors
        }
        
        if error_messages:
            result["error_messages"] = error_messages
            
        print(f"Результат импорта: {result}")
        return result
    
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА при импорте: {str(e)}")
        await db.rollback()  # Асинхронный метод rollback
        return {"success": False, "message": f"Ошибка при импорте: {str(e)}"}
    

def anon_question_create_excel_file(questions: list[AnonymousQuestion]) -> bytes:
    data = []
    for question in questions:
        status_display = {
            None: "Новый",
            "read": "Прочитано",
            "later": "Отложено"
        }.get(question.question_status, question.question_status)

        data.append({
            "ID": question.id,
            "Вопрос": question.question_text,
            "Статус": status_display,
            "Дата создания": question.submitted_at.strftime('%Y-%m-%d %H:%M'),
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Анонимные вопросы')
        worksheet = writer.sheets['Анонимные вопросы']
        
        from openpyxl.utils import get_column_letter

        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 50)

    output.seek(0)
    return output.getvalue()
