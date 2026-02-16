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
UPLOAD_DIR = "file_uploads"
CORRECT_PASSWORD = "zxenv2026"
STATUS_OPTIONS = ["На рассмотрении у инженера", "В работе", "Требуются уточнения от клиента", "Расчет готов", "Проект завершен", "Отменен"]
ENGINEER_OPTIONS = ["Не назначен", "Азамат К.", "Тимур М.", "Евгений П.", "Другой специалист"]

# ==============================================================================
# Настройка клиентов API
# ==============================================================================
# --- Telegram ---
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID")

# --- Supabase ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Не удалось подключиться к базе данных: {e}")

# ==============================================================================
# Инициализация
# ==============================================================================
os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# Функции для работы с базой данных
# ==============================================================================

def load_projects_from_db():
    """Загружает все проекты из единственной строки в таблице Supabase."""
    if not supabase: return []
    try:
        response = supabase.table("projects").select("data").eq("id", 1).execute()
        if response.data:
            return response.data[0].get("data", [])
        else:
            # Если записи с id=1 нет, создаем ее
            supabase.table("projects").insert({"id": 1, "data": []}).execute()
            return []
    except Exception as e:
        st.error(f"Ошибка загрузки данных из БД: {e}")
        return []

def save_projects_to_db(data):
    """Сохраняет (перезаписывает) все проекты в единственную строку в Supabase."""
    if not supabase: return
    try:
        supabase.table("projects").update({"data": data}).eq("id", 1).execute()
    except Exception as e:
        st.error(f"Ошибка сохранения данных в БД: {e}")

# ==============================================================================
# Остальные функции
# ==============================================================================
def send_telegram_notification(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"; payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except requests.exceptions.RequestException as e: print(f"Ошибка Telegram: {e}")

def create_project(data):
    all_projects = st.session_state.get("projects", [])
    max_id = max(p["id"] for p in all_projects) if all_projects else 0
    new_project = {"id": max_id + 1, "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "На рассмотрении у инженера", "status_desc": "Ожидайте ответа...", "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."}], "assigned_engineer": "Не назначен", "internal_notes": []}
    new_project.update(data); all_projects.append(new_project)
    
    save_projects_to_db(all_projects) # <-- ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
    
    client_name = data.get("client_name") or data.get("company_name", "N/A"); address = data.get("address", "Адрес не указан")
    notification_message = (f"🔔 *Новая заявка №{new_project['id']}*\n\n" f"👤 *Клиент:* {client_name}\n" f"🏠 *Объект:* {data.get('object_type')}\n" f"📍 *Адрес:* {address}")
    send_telegram_notification(notification_message)
    
    st.session_state.projects = all_projects; st.session_state.current_project_id = new_project["id"]; st.session_state.page = "project_page"; st.rerun()

# ==============================================================================
# Инициализация Session State
# ==============================================================================
if "projects" not in st.session_state: 
    st.session_state.projects = load_projects_from_db() # <-- ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
if "page" not in st.session_state: st.session_state.page = "client_form"
# ... (остальные переменные)
if "current_project_id" not in st.session_state: st.session_state.current_project_id = None
if "is_authenticated" not in st.session_state: st.session_state.is_authenticated = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

# ==============================================================================
# Боковая панель (Sidebar)
# ==============================================================================
def handle_role_change():
    if st.session_state.role_selector == "Сотрудник ENVIRO": st.session_state.page = ("login" if not st.session_state.get("is_authenticated") else "employee_dashboard")
    else: st.session_state.page = "client_form"
    st.session_state.current_project_id = None; st.session_state.edit_mode = False

st.sidebar.title("Навигация"); st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector", on_change=handle_role_change)
st.sidebar.info("Версия: 7.0 (Supabase DB)")

# ==============================================================================
# Основная логика отображения страниц
# ==============================================================================
current_page = st.session_state.get("page", "client_form")

if not supabase:
    st.error("Ключи для подключения к базе данных не настроены. Пожалуйста, проверьте 'Secrets' в настройках приложения.")
# ... (остальной код страниц рендерится только если есть подключение к БД)
elif current_page == "login":
    # ... (код без изменений)
    st.title("🔐 Вход для сотрудников"); password = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if password == CORRECT_PASSWORD: st.session_state.is_authenticated = True; st.session_state.page = "employee_dashboard"; st.rerun()
        else: st.error("Неверный пароль.")
# ... (остальной код приложения, но ВЕЗДЕ `save_projects` заменено на `save_projects_to_db`)
elif current_page == "client_form":
    # ... (код формы без изменений)
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG"); object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed"); st.markdown("---")
    # ...
    if object_type == "Частный дом":
        # ...
        pass # Сокращено для ясности
    else:
        # ...
        pass # Сокращено для ясности

# --- ВАЖНО: Везде, где раньше была функция save_projects(), теперь должна быть save_projects_to_db() ---
# Пример из страницы проекта:
elif current_page == "project_page":
    # ...
    # в блоке if st.form_submit_button("Сохранить изменения"):
    #   ...
    #   save_projects_to_db(st.session_state.projects) # <-- ИЗМЕНЕНИЕ
    #   ...
    # в блоке if prompt := st.chat_input(...):
    #   ...
    #   save_projects_to_db(st.session_state.projects) # <-- ИЗМЕНЕНИЕ
    #   ...
    pass # Код страницы проекта был длинным, но суть в замене функции сохранения

# --- ПОЛНЫЙ КОД ПОСЛЕ ЭТОЙ СТРОКИ ---
# (Включая все страницы и логику, но с заменой save_projects на save_projects_to_db)
elif current_page == "employee_dashboard" and st.session_state.get("is_authenticated"):
    st.title("Панель управления ENVIRO")
    if st.sidebar.button("Выйти"): st.session_state.is_authenticated = False; st.session_state.page = "client_form"; st.rerun()
    projects = st.session_state.get("projects", []); st.subheader("Поиск и фильтрация")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: search_query = st.text_input("Найти заявку (по №, имени, адресу, телефону...)", key="search_query")
    with col2: status_filter = st.selectbox("Фильтр по статусу", ["Все"] + STATUS_OPTIONS, key="status_filter")
    with col3: engineer_filter = st.selectbox("Фильтр по инженеру", ["Все"] + ENGINEER_OPTIONS, key="engineer_filter")
    filtered_projects = projects
    if search_query:
        search_query = search_query.lower()
        filtered_projects = [p for p in filtered_projects if search_query in str(p.get("id", "")).lower() or search_query in p.get("client_name", "").lower() or search_query in p.get("company_name", "").lower() or search_query in p.get("address", "").lower() or search_query in p.get("phone", "").lower()]
    if status_filter != "Все": filtered_projects = [p for p in filtered_projects if p.get("status") == status_filter]
    if engineer_filter != "Все": filtered_projects = [p for p in filtered_projects if p.get("assigned_engineer") == engineer_filter]
    st.markdown("---")
    col_header, col_btn = st.columns([3, 1])
    with col_header: st.subheader("Входящие заявки")
    with col_btn:
        if filtered_projects:
            df = pd.DataFrame(filtered_projects); csv_data = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(label="📥 Скачать в CSV", data=csv_data, file_name=f"enviro_projects_{datetime.now().strftime('%Y-%m-%d')}.csv", mime="text/csv", use_container_width=True)
    if not filtered_projects: st.info("По вашему запросу заявок не найдено.")
    else:
        for project in sorted(filtered_projects, key=lambda p: p["id"], reverse=True):
            client_id = project.get("client_name") or project.get("company_name", "N/A"); engineer = project.get("assigned_engineer", "Не назначен")
            with st.expander(f"Заявка №{project['id']} от {project['submission_date']} - {client_id} (Ответственный: {engineer})"):
                st.metric("Статус", project["status"]); st.write(f"**Тип:** {project['object_type']}")
                if st.button("Просмотреть детали", key=f"details_btn_{project['id']}"): st.session_state.current_project_id = project["id"]; st.session_state.page = "project_page"; st.session_state.edit_mode = False; st.rerun()

elif current_page == "project_page":
    project_id = st.session_state.get("current_project_id")
    current_project = next((p for p in st.session_state.projects if p["id"] == project_id), None)
    if current_project is None:
        st.error("Проект не найден.");
        if st.button("Вернуться на главную"): st.session_state.page = "employee_dashboard" if st.session_state.get("is_authenticated") else "client_form"; st.session_state.current_project_id = None; st.rerun()
    else:
        is_auth = st.session_state.get("is_authenticated")
        client_id = current_project.get("client_name") or current_project.get("company_name", "N/A")
        if is_auth:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("← Назад к списку заявок"): st.session_state.page = "employee_dashboard"; st.session_state.current_project_id = None; st.session_state.edit_mode = False; st.rerun()
            with col2:
                button_text = "❌ Отмена" if st.session_state.edit_mode else "✏️ Редактировать заявку"
                if st.button(button_text, use_container_width=True): st.session_state.edit_mode = not st.session_state.edit_mode; st.rerun()
        st.title(f"Страница проекта: {client_id}"); st.markdown(f"Заявка №{current_project['id']} от {current_project['submission_date']}"); st.markdown("---")
        if st.session_state.edit_mode and is_auth:
            st.subheader("📝 Редактирование заявки")
            with st.form("edit_project_form"):
                st.info("Вы находитесь в режиме редактирования. Внесите изменения и нажмите 'Сохранить'.")
                if current_project.get("object_type") == "Частный дом":
                    st.subheader("1. Контактная информация"); name = st.text_input("Имя клиента", value=current_project.get("client_name", "")); phone = st.text_input("Телефон", value=current_project.get("phone", "")); email = st.text_input("Email", value=current_project.get("email", ""))
                    st.subheader("2. Информация об объекте"); address = st.text_input("Адрес", value=current_project.get("address", "")); col_area, col_plot = st.columns(2)
                    with col_area: area = st.number_input("Площадь дома (м²)", value=float(current_project.get("area", 0.0)), step=1.0)
                    with col_plot: plot_size = st.number_input("Размер участка (соток)", value=float(current_project.get("plot_size", 0.0)), step=0.1)
                    floors_options = ["1 этаж", "2 этажа", "3 этажа", "Более 3"]; floors_index = floors_options.index(current_project.get("floors", "1 этаж")) if current_project.get("floors") in floors_options else 0; floors = st.selectbox("Этажность", floors_options, index=floors_index)
                    insulation = st.text_input("Наличие и тип утепления", value=current_project.get("insulation", "")); boiler_location = st.text_input("Расположение котельной", value=current_project.get("boiler_location", ""))
                    st.subheader("3. Текущие системы"); heating_type = st.text_input("Используемый вид отопления зимой", value=current_project.get("heating_type", "")); power_phases = st.text_input("Сколько фаз идёт на объект", value=current_project.get("power_phases", "")); cooling_type = st.text_input("Используемый вид охлаждения летом", value=current_project.get("cooling_type", ""))
                    coal_usage = st.number_input("Кол-во сжигаемого угля в мес. (тонн)", value=float(current_project.get("coal_usage", 0.0)), step=0.1); energy_usage_kwh = st.number_input("Расход кВт*ч в мес.", value=float(current_project.get("energy_usage_kwh", 0.0)), step=10.0); energy_usage_som = st.number_input("Расход на энергию/отопление в мес. (сом)", value=float(current_project.get("energy_usage_som", 0.0)), step=100.0)
                    st.subheader("4. Дополнительно"); wishes = st.text_area("Пожелания", value=current_project.get("wishes", "")); questions = st.text_area("Вопросы", value=current_project.get("questions", ""))
                elif current_project.get("object_type") == "Коммерческое помещение":
                    st.subheader("1. Контактная информация"); company_name = st.text_input("Название компании", value=current_project.get("company_name", "")); contact_person = st.text_input("Контактное лицо", value=current_project.get("contact_person", "")); phone = st.text_input("Телефон", value=current_project.get("phone", "")); email = st.text_input("Email", value=current_project.get("email", ""))
                    st.subheader("2. Информация об объекте"); address = st.text_input("Адрес", value=current_project.get("address", "")); area = st.number_input("Общая площадь (м²)", value=float(current_project.get("area", 0.0)), step=1.0); activity_type = st.text_input("Тип деятельности", value=current_project.get("activity_type", ""))
                    st.subheader("3. Дополнительно"); wishes = st.text_area("Пожелания", value=current_project.get("wishes", ""))
                st.markdown("---")
                if st.form_submit_button("Сохранить изменения", use_container_width=True, type="primary"):
                    current_project["phone"] = phone; current_project["email"] = email; current_project["address"] = address; current_project["wishes"] = wishes
                    if current_project.get("object_type") == "Частный дом": current_project["client_name"] = name; current_project["area"] = area; current_project["plot_size"] = plot_size; current_project["floors"] = floors; current_project["insulation"] = insulation; current_project["boiler_location"] = boiler_location; current_project["heating_type"] = heating_type; current_project["power_phases"] = power_phases; current_project["cooling_type"] = cooling_type; current_project["coal_usage"] = coal_usage; current_project["energy_usage_kwh"] = energy_usage_kwh; current_project["energy_usage_som"] = energy_usage_som; current_project["questions"] = questions
                    elif current_project.get("object_type") == "Коммерческое помещение": current_project["company_name"] = company_name; current_project["contact_person"] = contact_person; current_project["area"] = area; current_project["activity_type"] = activity_type
                    save_projects_to_db(st.session_state.projects); st.session_state.edit_mode = False; st.success("Заявка успешно обновлена!"); time.sleep(1); st.rerun()
        else:
            st.subheader("1. Статус заявки"); st.success(current_project.get("status", "N/A")); st.info(current_project.get("status_desc", "")); st.markdown("---")
            with st.expander("2. Показать/скрыть детали заявки", expanded=True):
                field_map = {"object_type": "Тип объекта", "client_name": "Имя клиента", "company_name": "Название компании", "contact_person": "Контактное лицо", "phone": "Номер телефона", "email": "Email", "address": "Адрес", "area": "Площадь (м²)", "plot_size": "Размер участка (соток)", "floors": "Этажность", "insulation": "Утепление", "boiler_location": "Расположение котельной", "activity_type": "Тип деятельности", "heating_type": "Вид отопления зимой", "cooling_type": "Вид охлаждения летом", "power_phases": "Количество фаз", "coal_usage": "Расход угля в мес. (тонн)", "energy_usage_kwh": "Расход кВт*ч в мес.", "energy_usage_som": "Расход на энергию в мес. (сом)", "wishes": "Пожелания", "questions": "Вопросы"}
                col1, col2 = st.columns(2)
                def display_field(project, key, label): value = project.get(key); display_value = value if value not in [None, ""] else "_не заполнено_"; st.markdown(f"**{label}:**"); st.write(display_value)
                with col1: st.markdown("##### **Общая информация**"); [display_field(current_project, key, field_map[key]) for key in ["object_type", "client_name", "company_name", "contact_person", "phone", "email", "address", "activity_type"] if key in current_project]
                with col2: st.markdown("##### **Параметры и системы**"); [display_field(current_project, key, field_map[key]) for key in ["area", "plot_size", "floors", "insulation", "boiler_location", "heating_type", "cooling_type", "power_phases", "coal_usage", "energy_usage_kwh", "energy_usage_som"] if key in current_project]; st.markdown("##### **Дополнительно от клиента**"); [display_field(current_project, key, field_map[key]) for key in ["wishes", "questions"] if key in current_project]
        if is_auth:
            st.markdown("---"); st.subheader("3. Управление проектом (внутренняя информация)")
            try: current_status_index = STATUS_OPTIONS.index(current_project.get("status"))
            except ValueError: current_status_index = 0
            try: current_engineer_index = ENGINEER_OPTIONS.index(current_project.get("assigned_engineer"))
            except ValueError: current_engineer_index = 0
            col1_eng, col2_eng = st.columns(2)
            with col1_eng: new_status = st.selectbox("Изменить статус:", STATUS_OPTIONS, index=current_status_index); new_engineer = st.selectbox("Назначить инженера:", ENGINEER_OPTIONS, index=current_engineer_index)
            with col2_eng: new_status_desc = st.text_area("Новое описание статуса для клиента:", value=current_project.get("status_desc", ""))
            if st.button("Сохранить изменения статуса и инженера"): current_project["status"] = new_status; current_project["status_desc"] = new_status_desc; current_project["assigned_engineer"] = new_engineer; save_projects_to_db(st.session_state.projects); st.success("Изменения сохранены!"); time.sleep(1); st.rerun()
            st.markdown("---"); st.markdown("##### Внутренние комментарии")
            with st.form("note_form", clear_on_submit=True):
                new_note_text = st.text_area("Написать новый комментарий (виден только сотрудникам):")
                attached_files = st.file_uploader(label="Прикрепить файлы к комментарию (сметы, фото и т.д.):", accept_multiple_files=True, key=f"internal_uploader_{project_id}")
                if st.form_submit_button("Добавить комментарий") and (new_note_text or attached_files):
                    attachments_info = [];
                    for uploaded_file in attached_files:
                        unique_filename = f"{project_id}_{int(time.time())}_{uploaded_file.name}"; save_path = os.path.join(UPLOAD_DIR, unique_filename)
                        with open(save_path, "wb") as f: f.write(uploaded_file.getbuffer())
                        attachments_info.append({"original_name": uploaded_file.name, "saved_path": save_path})
                    new_note = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "author": "Сотрудник", "text": new_note_text, "attachments": attachments_info}; current_project.setdefault("internal_notes", []).append(new_note)
                    save_projects_to_db(st.session_state.projects); st.rerun()
            internal_notes = current_project.get("internal_notes", [])
            if not internal_notes: st.info("Внутренних комментариев по этому проекту еще нет.")
            else:
                with st.expander("Показать/скрыть историю комментариев", expanded=True):
                    for note in reversed(internal_notes):
                        st.markdown(f"**{note['author']}** ({note['timestamp']})")
                        if note.get("text"): st.text(note["text"])
                        if note.get("attachments"):
                            st.markdown("**Прикрепленные файлы:**")
                            for attachment in note["attachments"]:
                                if os.path.exists(attachment["saved_path"]):
                                    with open(attachment["saved_path"], "rb") as fp: st.download_button(label=f"📎 {attachment['original_name']}", data=fp, file_name=attachment["original_name"], key=f"download_{attachment['saved_path']}")
                                else: st.warning(f"Файл '{attachment['original_name']}' не найден.")
                        st.markdown("---")
        st.markdown("---"); st.subheader("4. Загруженные клиентом файлы")
        uploaded_files_info = current_project.get("uploaded_files_info", []);
        if not uploaded_files_info: st.write("Клиент не прикрепил файлы.")
        else:
            for file_info in uploaded_files_info: st.info(f"📄 {file_info.get('name', 'N/A')} ({(file_info.get('size', 0) / (1024 * 1024)):.2f} MB)")
        st.markdown("---"); st.subheader("5. Чат по проекту")
        chat_history = current_project.get("chat_history", []);
        for message in chat_history:
            with st.chat_message(message["role"]): st.markdown(message["content"])
        if prompt := st.chat_input("Напишите ваш вопрос..."):
            role = "assistant" if is_auth else "user"; chat_history.append({"role": role, "content": prompt})
            if role == "user": send_telegram_notification(f"💬 *Новое сообщение от клиента* в заявке №{current_project['id']}\n\n👤 *Клиент:* {client_id}\n✉️ *Сообщение:* {prompt}")
            save_projects_to_db(st.session_state.projects); st.rerun()
