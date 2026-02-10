import streamlit as st
import time
from datetime import datetime
import base64
import os
import json
import requests # <-- 1. Добавляем новую библиотеку. Не забудьте ее установить! (pip install requests)

# --- КОНФИГУРАЦИЯ ---
DATA_FILE = "projects.json"
UPLOAD_DIR = "file_uploads"
CORRECT_PASSWORD = "zxenv2026"
STATUS_OPTIONS = ["На рассмотрении у инженера", "В работе", "Требуются уточнения от клиента", "Расчет готов", "Проект завершен", "Отменен"]
ENGINEER_OPTIONS = ["Не назначен", "Азамат К.", "Тимур М.", "Евгений П.", "Другой специалист"]

# --- НАСТРОЙКИ TELEGRAM ---
# Мы будем использовать секреты Streamlit для безопасности
# st.secrets["TELEGRAM_TOKEN"] и st.secrets["TELEGRAM_CHAT_ID"]
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except (KeyError, FileNotFoundError):
    # Заглушки, если секреты не настроены. Уведомления работать не будут.
    TELEGRAM_TOKEN = None
    TELEGRAM_CHAT_ID = None

os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed")

# <<< 2. НОВАЯ ФУНКЦИЯ ДЛЯ ОТПРАВКИ УВЕДОМЛЕНИЙ >>>
def send_telegram_notification(message):
    """Отправляет сообщение в Telegram, если настроены токен и ID чата."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram-уведомления не настроены. Пропускаем отправку.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Ошибка отправки уведомления в Telegram: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Исключение при отправке уведомления в Telegram: {e}")

# ... (Остальные функции load_projects, save_projects, video_to_base64 без изменений) ...
def load_projects(): #...
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []
def save_projects(data): #...
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def video_to_base64(path): #...
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

def create_project(data):
    all_projects = st.session_state.projects
    max_id = max(p['id'] for p in all_projects) if all_projects else 0
    new_project = {
        "id": max_id + 1, "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "На рассмотрении у инженера", "status_desc": "Ожидайте ответа...",
        "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."}],
        "assigned_engineer": "Не назначен", "internal_notes": []
    }
    new_project.update(data)
    all_projects.append(new_project)
    save_projects(all_projects) 
    
    # <<< 3. ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ О НОВОЙ ЗАЯВКЕ >>>
    client_name = data.get('client_name') or data.get('company_name', 'N/A')
    address = data.get('address', 'Адрес не указан')
    notification_message = (
        f"🔔 *Новая заявка №{new_project['id']}*\n\n"
        f"👤 *Клиент:* {client_name}\n"
        f"🏠 *Объект:* {data.get('object_type')}\n"
        f"📍 *Адрес:* {address}"
    )
    send_telegram_notification(notification_message)
    
    st.session_state.projects = all_projects
    st.session_state.current_project_id = new_project["id"]
    st.session_state.page = "project_page"
    st.rerun()

# ... (Весь остальной код до конца остается таким же, за одним исключением) ...
# ... (ИНИЦИАЛИЗАЦИЯ, НАВИГАЦИЯ, СТРАНИЦА ВХОДА, АНКЕТЫ, ПАНЕЛЬ УПРАВЛЕНИЯ) ...

# В самом конце, в блоке "Чат по проекту", нужно внести одно изменение
elif st.session_state.get('page') == "project_page":
    # ... (весь код страницы проекта до блока чата)
    # ...
    # --- БЛОК 5: ЧАТ ПО ПРОЕКТУ ---
    st.markdown("---"); st.subheader("5. Чат по проекту");
    for message in current_project.get("chat_history", []):
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Напишите ваш вопрос..."):
        role = "assistant" if is_auth else "user"
        current_project["chat_history"].append({"role": role, "content": prompt})
        
        # <<< 4. ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ О НОВОМ СООБЩЕНИИ ОТ КЛИЕНТА >>>
        if role == "user":
            notification_message = (
                f"💬 *Новое сообщение от клиента* в заявке №{current_project['id']}\n\n"
                f"👤 *Клиент:* {client_identifier}\n"
                f"✉️ *Сообщение:* {prompt}"
            )
            send_telegram_notification(notification_message)
            
        save_projects(st.session_state.projects)
        st.rerun()
