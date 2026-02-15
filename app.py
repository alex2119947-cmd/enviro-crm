# ==============================================================================
# Библиотеки
# ==============================================================================
import base64
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
STATUS_OPTIONS = [
    "На рассмотрении у инженера", "В работе", "Требуются уточнения от клиента",
    "Расчет готов", "Проект завершен", "Отменен"
]
ENGINEER_OPTIONS = [
    "Не назначен", "Азамат К.", "Тимур М.", "Евгений П.", "Другой специалист"
]

# ==============================================================================
# Настройка Telegram
# ==============================================================================
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except (KeyError, FileNotFoundError):
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = None, None

# ==============================================================================
# Инициализация
# ==============================================================================
os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(
    page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed"
)

# ==============================================================================
# Функции
# ==============================================================================

def send_telegram_notification(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except requests.exceptions.RequestException as e: print(f"Ошибка Telegram: {e}")

def load_projects():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return []

def save_projects(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def create_project(data):
    all_projects = st.session_state.get("projects", [])
    max_id = max(p["id"] for p in all_projects) if all_projects else 0
    new_project = {
        "id": max_id + 1, "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "На рассмотрении у инженера", "status_desc": "Ожидайте ответа...",
        "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {data.get('client_name') or data.get('contact_person')}! Ваша заявка принята."}],
        "assigned_engineer": "Не назначен", "internal_notes": []
    }
    new_project.update(data); all_projects.append(new_project); save_projects(all_projects)
    client_name = data.get("client_name") or data.get("company_name", "N/A"); address = data.get("address", "Адрес не указан")
    notification_message = (f"🔔 *Новая заявка №{new_project['id']}*\n\n" f"👤 *Клиент:* {client_name}\n" f"🏠 *Объект:* {data.get('object_type')}\n" f"📍 *Адрес:* {address}")
    send_telegram_notification(notification_message)
    st.session_state.projects = all_projects; st.session_state.current_project_id = new_project["id"]; st.session_state.page = "project_page"; st.rerun()

# ==============================================================================
# Инициализация Session State
# ==============================================================================
if "projects" not in st.session_state: st.session_state.projects = load_projects()
if "page" not in st.session_state: st.session_state.page = "client_form"
if "current_project_id" not in st.session_state: st.session_state.current_project_id = None
if "is_authenticated" not in st.session_state: st.session_state.is_authenticated = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

# ==============================================================================
# Боковая панель (Sidebar)
# ==============================================================================
def handle_role_change():
    if st.session_state.role_selector == "Сотрудник ENVIRO": st.session_state.page = ("login" if not st.session_state.get("is_authenticated") else "employee_dashboard")
    else: st.session_state.page = "client_form"
    st.session_state.current_project_id = None
    st.session_state.edit_mode = False

st.sidebar.title("Навигация"); st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector", on_change=handle_role_change)
st.sidebar.info("Версия: 6.0 (Стабильная)")

# ==============================================================================
# Основная логика отображения страниц
# ==============================================================================
current_page = st.session_state.get("page", "client_form")

if current_page == "login":
    st.title("🔐 Вход для сотрудников"); password = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if password == CORRECT_PASSWORD: st.session_state.is_authenticated = True; st.session_state.page = "employee_dashboard"; st.rerun()
        else: st.error("Неверный пароль.")

elif current_page == "client_form":
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG"); object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed"); st.markdown("---")
    def shared_form_elements():
        st.subheader("5. Загрузка файлов"); st.caption("Вы можете прикрепить несколько файлов: планы, схемы, фото и т.д.")
        return st.file_uploader(label="**Нажмите, чтобы выбрать файлы, или перетащите их в эту область**", type=["jpg", "png", "jpeg", "pdf", "doc", "docx"], accept_multiple_files=True)
    if object_type == "Частный дом":
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация"); name = st.text_input("Имя клиента \*"); phone = st.text_input("Номер телефона \*"); email = st.text_input("Email")
            st.subheader("2. Информация об объекте"); address = st.text_input("Точный адрес \*"); col1, col2 = st.columns(2)
            with col1: area = st.number_input("Площадь дома (м²)", min_value=0.0, step=1.0); plot_size = st.number_input("Размер участка (в сотках)", min_value=0.0, step=0.1)
            with col2: floors = st.selectbox("Этажность", ["1 этаж", "2 этажа", "3 этажа", "Более 3"]); insulation = st.text_input("Наличие и тип утепления \*"); boiler_location = st.text_input("Расположение котельной")
            st.subheader("3. Текущие системы"); col3, col4 = st.columns(2)
            with col3: heating_type = st.text_input("Используемый вид отопления зимой"); power_phases = st.text_input("Сколько фаз идёт на объект"); cooling_type = st.text_input("Используемый вид охлаждения летом")
            with col4: coal_usage = st.number_input("Кол-во сжигаемого угля в мес. (тонн)", value=0.0, step=0.1, min_value=0.0); energy_usage_kwh = st.number_input("Расход кВт\*ч в мес.", value=0.0, step=10.0, min_value=0.0); energy_usage_som = st.number_input("Расход на энергию/отопление в мес. (сом)", value=0.0, step=100.0, min_value=0.0)
            st.subheader("4. Дополнительно"); wishes = st.text_area("Ваши пожелания"); questions = st.text_area("Ваши вопросы"); uploaded_files = shared_form_elements()
            if st.form_submit_button("Отправить заявку"):
                if not name or not phone or not address: st.error("Заполните обязательные поля (\*).")
                else: 
                    project_data = {"object_type": "Частный дом", "client_name": name, "phone": phone, "email": email, "address": address, "area": float(area), "plot_size": float(plot_size), "floors": floors, "insulation": insulation, "boiler_location": boiler_location, "heating_type": heating_type, "power_phases": power_phases, "cooling_type": cooling_type, "coal_usage": float(coal_usage), "energy_usage_kwh": float(energy_usage_kwh), "energy_usage_som": float(energy_usage_som), "wishes": wishes, "questions": questions, "uploaded_files_info": [{"name": f.name, "size": f.size} for f in uploaded_files]}; create_project(project_data)
    else:
        with st.form("commercial_form", clear_on_submit=True):
            st.subheader("1. Контактная информация"); company_name = st.text_input("Название компании \*"); contact_person = st.text_input("Контактное лицо \*"); phone = st.text_input("Номер телефона \*"); email = st.text_input("Email")
            st.subheader("2. Информация об объекте"); address = st.text_input("Адрес объекта \*"); activity_type = st.text_input("Тип деятельности", placeholder="Например, кафе, офис, производство"); area = st.number_input("Общая площадь (м²)", min_value=0.0, step=1.0)
            st.subheader("3. Дополнительно"); wishes = st.text_area("Ваши пожелания и технические требования"); uploaded_files = shared_form_elements()
            if st.form_submit_button("Отправить заявку"):
                if not company_name or not contact_person or not phone: st.error("Заполните обязательные поля (\*).")
                else: 
                    project_data = {"object_type": "Коммерческое помещение", "company_name": company_name, "contact_person": contact_person, "phone": phone, "email": email, "address": address, "activity_type": activity_type, "area": float(area), "wishes": wishes, "uploaded_files_info": [{"name": f.name, "size": f.size} for f in uploaded_files]}; create_project(project_data)
    st.markdown("<hr>", unsafe_allow_html=True); st.markdown('<div style="text-align: center;"><h2>ENVIRO — в действии</h2></div>', unsafe_allow_html=True)

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
                    save_projects(st.session_state.projects); st.session_state.edit_mode = False; st.success("Заявка успешно обновлена!"); time.sleep(1); st.rerun()
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
            if st.button("Сохранить изменения статуса и инженера"): current_project["status"] = new_status; current_project["status_desc"] = new_status_desc; current_project["assigned_engineer"] = new_engineer; save_projects(st.session_state.projects); st.success("Изменения сохранены!"); time.sleep(1); st.rerun()
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
                    save_projects(st.session_state.projects); st.rerun()
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
            save_projects(st.session_state.projects); st.rerun()
