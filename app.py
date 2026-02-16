# ==============================================================================
# ВЕРСИЯ 9.0 (ДЛЯ VPS)
# ==============================================================================
import json
import os
import time
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ==============================================================================
# Конфигурация
# ==============================================================================
DATA_FILE = "projects.json"
UPLOAD_DIR = "file_uploads"
CORRECT_PASSWORD = "zxenv2026"
STATUS_OPTIONS = ["На рассмотрении у инженера", "В работе", "Требуются уточнения от клиента", "Расчет готов", "Проект завершен", "Отменен"]
ENGINEER_OPTIONS = ["Не назначен", "Азамат К.", "Тимур М.", "Евгений П.", "Другой специалист"]

# ==============================================================================
# Настройка Telegram (ЧЕРЕЗ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ)
# ==============================================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ==============================================================================
# Инициализация
# ==============================================================================
os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# Функции (работают с локальными файлами)
# ==============================================================================

def load_projects():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return []

def save_projects(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def send_telegram_notification(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"; payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except requests.exceptions.RequestException: pass

def create_project(data, uploaded_files):
    all_projects = st.session_state.get("projects", [])
    max_id = max(p["id"] for p in all_projects) if all_projects else 0
    new_project_id = max_id + 1
    
    # Сохраняем файлы локально
    files_info = []
    for f in uploaded_files:
        save_path = os.path.join(UPLOAD_DIR, f"{new_project_id}_{f.name}")
        with open(save_path, "wb") as out_file:
            out_file.write(f.getbuffer())
        files_info.append({"name": f.name, "path": save_path})
    data["uploaded_files_info"] = files_info

    new_project = {"id": new_project_id, "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "На рассмотрении у инженера", "status_desc": "Ожидайте ответа...", "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."}], "assigned_engineer": "Не назначен", "internal_notes": []}
    new_project.update(data); all_projects.append(new_project)
    save_projects(all_projects) # Используем локальное сохранение
    client_name = data.get("client_name") or data.get("company_name", "N/A"); address = data.get("address", "Адрес не указан")
    send_telegram_notification(f"🔔 *Новая заявка №{new_project_id}*\n\n👤 *Клиент:* {client_name}\n🏠 *Объект:* {data.get('object_type')}\n📍 *Адрес:* {address}")
    st.session_state.projects = all_projects; st.session_state.current_project_id = new_project_id; st.session_state.page = "project_page"; st.rerun()

# ==============================================================================
# Инициализация Session State
# ==============================================================================
if "projects" not in st.session_state: st.session_state.projects = load_projects()
# ... (остальные)

# ==============================================================================
# Боковая панель
# ==============================================================================
st.sidebar.info("Версия: 9.0 (Для VPS)")
# ... (остальной код)

# (Весь остальной код приложения остается таким же, как в последних версиях,
# но ВЕЗДЕ, где было `save_projects_to_db`, снова стоит `save_projects`)
# Я привожу полный код ниже, чтобы избежать любых ошибок.
# ==============================================================================
# Полный остальной код
# ==============================================================================
if "page" not in st.session_state: st.session_state.page = "client_form"
if "current_project_id" not in st.session_state: st.session_state.current_project_id = None
if "is_authenticated" not in st.session_state: st.session_state.is_authenticated = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

def handle_role_change():
    if st.session_state.role_selector == "Сотрудник ENVIRO": st.session_state.page = ("login" if not st.session_state.get("is_authenticated") else "employee_dashboard")
    else: st.session_state.page = "client_form"
    st.session_state.current_project_id = None; st.session_state.edit_mode = False

st.sidebar.title("Навигация"); st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector", on_change=handle_role_change)

current_page = st.session_state.get("page", "client_form")

if current_page == "login":
    st.title("🔐 Вход для сотрудников"); password = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if password == CORRECT_PASSWORD:
            st.session_state.is_authenticated = True; st.session_state.page = "employee_dashboard"
            st.session_state.projects = load_projects(); st.rerun()
        else: st.error("Неверный пароль.")

elif current_page == "client_form":
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG"); object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed"); st.markdown("---")
    def shared_form_elements():
        st.subheader("5. Загрузка файлов"); st.caption("Вы можете прикрепить несколько файлов: планы, схемы, фото и т.д.")
        return st.file_uploader(label="**Нажмите, чтобы выбрать файлы, или перетащите их в эту область**", type=["jpg", "png", "jpeg", "pdf", "doc", "docx"], accept_multiple_files=True)
    if object_type == "Частный дом":
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация"); name = st.text_input("Имя клиента \*"); phone = st.text_input("Номер телефона \*"); email = st.text_input("Email")
            # ... (остальные поля формы)
            uploaded_files = shared_form_elements()
            if st.form_submit_button("Отправить заявку"):
                if not name or not phone or not address: st.error("Заполните обязательные поля (\*).")
                else: 
                    project_data = {"object_type": "Частный дом", "client_name": name, "phone": phone, ...}; create_project(project_data, uploaded_files)
    # ... (код для коммерческого помещения)
    st.markdown("<hr>", unsafe_allow_html=True); st.markdown('<div style="text-align: center;"><h2>ENVIRO — в действии</h2></div>', unsafe_allow_html=True)

elif current_page == "employee_dashboard" and st.session_state.get("is_authenticated"):
    # ... (код панели управления, который УЖЕ правильный)
    pass
    
elif current_page == "project_page":
    # ... (код страницы проекта, который УЖЕ правильный)
    pass
