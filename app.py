# ==============================================================================
# Библиотеки
# ==============================================================================
import json
import os
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from supabase import Client, create_client

# ==============================================================================
# Конфигурация
# ==============================================================================
UPLOAD_DIR = "file_uploads" # Эта папка больше не используется, но оставим для совместимости
CORRECT_PASSWORD = "zxenv2026"
STATUS_OPTIONS = ["На рассмотрении у инженера", "В работе", "Требуются уточнения от клиента", "Расчет готов", "Проект завершен", "Отменен"]
ENGINEER_OPTIONS = ["Не назначен", "Азамат К.", "Тимур М.", "Евгений П.", "Другой специалист"]
SUPABASE_BUCKET_NAME = "project_files" # Имя вашего "бакета"

# ==============================================================================
# Настройка клиентов API
# ==============================================================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        pass

TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID")

# ==============================================================================
# Инициализация
# ==============================================================================
st.set_page_config(page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# Функции
# ==============================================================================

def load_projects_from_db():
    if not supabase: return []
    try:
        response = supabase.table("projects").select("data").eq("id", 1).execute()
        if response.data: return response.data[0].get("data", [])
        else: supabase.table("projects").insert({"id": 1, "data": []}).execute(); return []
    except Exception as e:
        st.error(f"Ошибка загрузки данных из БД: {e}"); return []

def save_projects_to_db(data):
    if not supabase: return
    try: supabase.table("projects").update({"data": data}).eq("id", 1).execute()
    except Exception as e: st.error(f"Ошибка сохранения данных в БД: {e}")

def send_telegram_notification(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"; payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except requests.exceptions.RequestException: pass

# <<< НОВАЯ ФУНКЦИЯ ЗАГРУЗКИ ФАЙЛОВ >>>
def upload_file_to_storage(file, project_id):
    if not supabase: return None
    try:
        # Создаем уникальное имя файла
        file_path = f"{project_id}/{int(time.time())}_{file.name}"
        # Загружаем файл в Supabase Storage
        supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(file_path, file.getvalue())
        # Получаем публичную ссылку на файл
        public_url = supabase.storage.from_(SUPABASE_BUCKET_NAME).get_public_url(file_path)
        return {"name": file.name, "url": public_url}
    except Exception as e:
        st.error(f"Ошибка загрузки файла '{file.name}': {e}")
        return None

def create_project(data, uploaded_files):
    all_projects = st.session_state.get("projects", [])
    max_id = max(p["id"] for p in all_projects) if all_projects else 0
    new_project_id = max_id + 1
    
    # Загружаем файлы в Storage
    files_info = [upload_file_to_storage(f, new_project_id) for f in uploaded_files]
    # Убираем None, если какие-то файлы не загрузились
    data["uploaded_files_info"] = [f for f in files_info if f is not None]

    new_project = {"id": new_project_id, "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "На рассмотрении у инженера", "status_desc": "Ожидайте ответа...", "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."}], "assigned_engineer": "Не назначен", "internal_notes": []}
    new_project.update(data); all_projects.append(new_project)
    save_projects_to_db(all_projects)
    client_name = data.get("client_name") or data.get("company_name", "N/A"); address = data.get("address", "Адрес не указан")
    send_telegram_notification(f"🔔 *Новая заявка №{new_project_id}*\n\n👤 *Клиент:* {client_name}\n🏠 *Объект:* {data.get('object_type')}\n📍 *Адрес:* {address}")
    st.session_state.projects = all_projects; st.session_state.current_project_id = new_project_id; st.session_state.page = "project_page"; st.rerun()

# ==============================================================================
# Инициализация Session State
# ==============================================================================
if "projects" not in st.session_state: st.session_state.projects = load_projects_from_db()
if "page" not in st.session_state: st.session_state.page = "client_form"
# ... (остальные)

# ==============================================================================
# Боковая панель
# ==============================================================================
st.sidebar.info("Версия: 8.0 (Supabase Storage)")
# ... (остальной код панели)

# ==============================================================================
# Основная логика
# ==============================================================================
# ... (код до страницы проекта)

# --- СТРАНИЦА ДЕТАЛЕЙ ПРОЕКТА ---
elif supabase and current_page == "project_page":
    # ... (код до блока комментариев)
    with st.form("note_form", clear_on_submit=True):
        new_note_text = st.text_area("Написать новый комментарий (виден только сотрудникам):")
        attached_files = st.file_uploader("Прикрепить файлы к комментарию:", accept_multiple_files=True, key=f"internal_uploader_{project_id}")
        if st.form_submit_button("Добавить комментарий") and (new_note_text or attached_files):
            # <<< ИЗМЕНЕНИЕ ЗДЕСЬ >>>
            attachments_info = [upload_file_to_storage(f, project_id) for f in attached_files]
            new_note = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "author": "Сотрудник", "text": new_note_text, "attachments": [f for f in attachments_info if f]}
            current_project.setdefault("internal_notes", []).append(new_note)
            save_projects_to_db(st.session_state.projects); st.rerun()
    
    internal_notes = current_project.get("internal_notes", [])
    if not internal_notes: st.info("Внутренних комментариев по этому проекту еще нет.")
    else:
        with st.expander("Показать/скрыть историю комментариев", expanded=True):
            for note in reversed(internal_notes):
                st.markdown(f"**{note['author']}** ({note['timestamp']})")
                if note.get("text"): st.text(note["text"])
                # <<< ИЗМЕНЕНИЕ ЗДЕСЬ >>>
                if note.get("attachments"):
                    st.markdown("**Прикрепленные файлы:**")
                    for attachment in note["attachments"]:
                        st.link_button(f"📎 {attachment['name']}", attachment['url'])
                st.markdown("---")
    
    st.markdown("---"); st.subheader("4. Загруженные клиентом файлы")
    uploaded_files_info = current_project.get("uploaded_files_info", []);
    if not uploaded_files_info: st.write("Клиент не прикрепил файлы.")
    else:
        # <<< ИЗМЕНЕНИЕ ЗДЕСЬ >>>
        for file_info in uploaded_files_info:
            st.link_button(f"📄 {file_info['name']}", file_info['url'])
            
    # ... (остальной код чата)
