import streamlit as st
import time
from datetime import datetime
import base64
import os
import json

# --- КОНФИГУРАЦИЯ ---
DATA_FILE = "projects.json"
UPLOAD_DIR = "file_uploads" # <-- Папка для загрузки файлов
CORRECT_PASSWORD = "zxenv2026"
STATUS_OPTIONS = ["На рассмотрении у инженера", "В работе", "Требуются уточнения от клиента", "Расчет готов", "Проект завершен", "Отменен"]
ENGINEER_OPTIONS = ["Не назначен", "Азамат К.", "Тимур М.", "Евгений П.", "Другой специалист"]

# --- УБЕДИМСЯ, ЧТО ПАПКА ДЛЯ ЗАГРУЗОК СУЩЕСТВУЕТ ---
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="CRM ENVIRO.KG", layout="wide", initial_sidebar_state="collapsed")

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ (без изменений) ---
def load_projects():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []

def save_projects(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (без изменений) ---
def video_to_base64(path):
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
    st.session_state.projects = all_projects
    st.session_state.current_project_id = new_project["id"]
    st.session_state.page = "project_page"
    st.rerun()

# --- ИНИЦИАЛИЗАЦИЯ И НАВИГАЦИЯ (без изменений) ---
if 'projects' not in st.session_state: st.session_state.projects = load_projects()
# ... (остальные переменные session_state)
st.sidebar.title("Навигация")
# ... (код radio и on_change)
def handle_role_change():
    st.session_state.page = "client_form"
    if st.session_state.role_selector == "Сотрудник ENVIRO":
        st.session_state.page = "login" if not st.session_state.get('is_authenticated') else "employee_dashboard"
    st.session_state.current_project_id = None
st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector", on_change=handle_role_change)
st.sidebar.info("Версия: 4.3 (Файлы в комментариях)")

# ==============================================================================
#                     СТРАНИЦЫ ВХОДА, АНКЕТ, ПАНЕЛИ УПРАВЛЕНИЯ (без изменений)
# ==============================================================================
if st.session_state.get('page', 'client_form') == "login":
    # ... (код страницы входа)
    st.title("🔐 Вход для сотрудников")
    password = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if password == CORRECT_PASSWORD: st.session_state.is_authenticated = True; st.session_state.page = "employee_dashboard"; st.rerun()
        else: st.error("Неверный пароль.")
elif st.session_state.get('page', 'client_form') == "client_form":
    # ... (весь код анкет)
    st.title("📋 Заявка в инженерный отдел ENVIRO.KG")
    object_type = st.radio("Тип объекта:", ('Частный дом', 'Коммерческое помещение'), horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    def shared_form_elements():
        st.subheader("5. Загрузка файлов")
        return st.file_uploader("Прикрепите фото, планы или другие документы (PDF, DOC, JPG, PNG)", type=['jpg', 'png', 'jpeg', 'pdf', 'doc', 'docx'], accept_multiple_files=True)
    if object_type == 'Частный дом':
        st.header("Анкета для Частного Дома")
        with st.form("private_house_form", clear_on_submit=True):
            st.subheader("1. Контактная информация"); name = st.text_input("Имя клиента \*"); phone = st.text_input("Номер телефона \*"); email = st.text_input("Email")
            st.subheader("2. Информация об объекте"); address = st.text_input("Точный адрес \*"); col1, col2 = st.columns(2)
            with col1: area = st.number_input("Площадь дома (м²)", min_value=10); plot_size = st.number_input("Размер участка (в сотках)", min_value=1)
            with col2: floors = st.selectbox("Этажность", ["1 этаж", "2 этажа", "3 этажа", "Более 3"]); insulation = st.text_input("Наличие и тип утепления \*"); boiler_location = st.text_input("Расположение котельной")
            st.subheader("3. Текущие системы"); col3, col4 = st.columns(2)
            with col3: heating_type = st.text_input("Используемый вид отопления зимой"); power_phases = st.text_input("Сколько фаз идёт на объект"); cooling_type = st.text_input("Используемый вид охлаждения летом")
            with col4: coal_usage = st.number_input("Кол-во сжигаемого угля в мес. (тонн)"); energy_usage_kwh = st.number_input("Расход кВт\*ч в мес."); energy_usage_som = st.number_input("Расход на энергию/отопление в мес. (сом)")
            st.subheader("4. Дополнительно"); wishes = st.text_area("Ваши пожелания"); questions = st.text_area("Ваши вопросы"); uploaded_files = shared_form_elements(); st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not name or not phone or not address: st.error("Заполните обязательные поля (\*).")
                else: files_info = [{"name": f.name, "size": f.size} for f in uploaded_files]; create_project({"object_type": "Частный дом", "client_name": name, "phone": phone, "email": email, "address": address, "area": area, "plot_size": plot_size, "floors": floors, "insulation": insulation, "boiler_location": boiler_location, "heating_type": heating_type, "power_phases": power_phases, "cooling_type": cooling_type, "coal_usage": coal_usage, "energy_usage_kwh": energy_usage_kwh, "energy_usage_som": energy_usage_som, "wishes": wishes, "questions": questions, "uploaded_files_info": files_info})
    elif object_type == 'Коммерческое помещение':
        st.header("Анкета для Коммерческого Объекта")
        with st.form("commercial_form", clear_on_submit=True):
            st.subheader("1. Контактная информация"); company_name = st.text_input("Название компании \*"); contact_person = st.text_input("Контактное лицо \*"); phone = st.text_input("Номер телефона \*"); email = st.text_input("Email")
            st.subheader("2. Информация об объекте"); address = st.text_input("Адрес объекта \*"); activity_type = st.text_input("Тип деятельности", placeholder="Например, кафе, офис, производство"); area = st.number_input("Общая площадь (м²)", min_value=10)
            st.subheader("3. Дополнительно"); wishes = st.text_area("Ваши пожелания и технические требования"); uploaded_files = shared_form_elements(); st.markdown("---")
            submitted = st.form_submit_button("Отправить заявку")
            if submitted:
                if not company_name or not contact_person or not phone: st.error("Заполните обязательные поля (\*).")
                else: files_info = [{"name": f.name, "size": f.size} for f in uploaded_files]; create_project({"object_type": "Коммерческое помещение", "company_name": company_name, "contact_person": contact_person, "phone": phone, "email": email, "address": address, "activity_type": activity_type, "area": area, "wishes": wishes, "uploaded_files_info": files_info})
    st.markdown("---"); st.header("ENVIRO — в действии"); video_path = "enviro1.mp4"; video_base64 = video_to_base64(video_path)
    if video_base64: st.markdown(f'<video autoplay loop muted playsinline width="100%"><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video>', unsafe_allow_html=True)
elif st.session_state.get('page') == "employee_dashboard" and st.session_state.get('is_authenticated'):
    # ... (код панели управления)
    st.title("Панель управления ENVIRO")
    st.subheader("Входящие заявки")
    if st.sidebar.button("Выйти"): st.session_state.is_authenticated = False; st.session_state.page = "client_form"; st.rerun()
    if not st.session_state.projects: st.info("Пока нет ни одной заявки от клиентов.")
    else:
        sorted_projects = sorted(st.session_state.projects, key=lambda p: p['id'], reverse=True)
        for project in sorted_projects:
            client_identifier = project.get('client_name') or project.get('company_name', 'N/A')
            engineer = project.get('assigned_engineer', 'Не назначен')
            with st.expander(f"Заявка №{project['id']} от {project['submission_date']} - {client_identifier} (Ответственный: {engineer})"):
                st.metric("Статус", project['status'])
                st.write(f"**Тип:** {project['object_type']}")
                if st.button("Просмотреть детали", key=f"details_btn_{project['id']}"): st.session_state.current_project_id = project['id']; st.session_state.page = "project_page"; st.rerun()

# ==============================================================================
#                СТРАНИЦА ПРОЕКТА (ОСНОВНЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ)
# ==============================================================================
elif st.session_state.get('page') == "project_page":
    project_id = st.session_state.get('current_project_id')
    current_project = next((p for p in st.session_state.projects if p['id'] == project_id), None)
    
    if current_project is None:
        st.error("Проект не найден."); # ... (код кнопки "Вернуться")
    else:
        is_auth = st.session_state.get('is_authenticated')
        client_identifier = current_project.get('client_name') or current_project.get('company_name', 'N/A')

        if is_auth and st.button("← Назад к списку заявок"):
            st.session_state.page = "employee_dashboard"; st.session_state.current_project_id = None; st.rerun()

        st.title(f"Страница проекта: {client_identifier}")
        st.markdown(f"Заявка №{current_project['id']} от {current_project['submission_date']}\n\n---")
        
        # --- БЛОКИ 1 и 2 (без изменений) ---
        st.subheader("1. Статус заявки"); st.success(current_project['status']); st.info(current_project['status_desc']); st.markdown("---")
        with st.expander("2. Показать/скрыть детали заявки"):
             # ... (весь код красивого отображения деталей) ...
            field_map = {"object_type": "Тип объекта", "client_name": "Имя клиента", "company_name": "Название компании","contact_person": "Контактное лицо", "phone": "Номер телефона", "email": "Email", "address": "Адрес", "area": "Площадь (м²)", "plot_size": "Размер участка (соток)", "floors": "Этажность", "insulation": "Утепление", "boiler_location": "Расположение котельной", "activity_type": "Тип деятельности", "heating_type": "Вид отопления зимой", "cooling_type": "Вид охлаждения летом", "power_phases": "Количество фаз", "coal_usage": "Расход угля в мес. (тонн)", "energy_usage_kwh": "Расход кВт*ч в мес.", "energy_usage_som": "Расход на энергию в мес. (сом)", "wishes": "Пожелания", "questions": "Вопросы"}
            col1, col2 = st.columns(2)
            def display_field(project, key, label):
                value = project.get(key)
                if value: st.markdown(f"**{label}:**\n\n{value}")
                else: st.markdown(f"**{label}:**\n\n_не заполнено_")
            with col1:
                st.markdown("##### **Общая информация**")
                for key in ["object_type", "client_name", "company_name", "contact_person", "phone", "email", "address", "activity_type"]:
                     if key in current_project: display_field(current_project, key, field_map[key])
            with col2:
                st.markdown("##### **Параметры и системы**")
                for key in ["area", "plot_size", "floors", "insulation", "boiler_location", "heating_type", "cooling_type", "power_phases", "coal_usage", "energy_usage_kwh", "energy_usage_som"]:
                     if key in current_project: display_field(current_project, key, field_map[key])
            st.markdown("##### **Дополнительно от клиента**")
            for key in ["wishes", "questions"]:
                 if key in current_project: display_field(current_project, key, field_map[key])

        # --- БЛОК 3: УПРАВЛЕНИЕ ПРОЕКТОМ ---
        if is_auth:
            st.markdown("---"); st.subheader("3. Управление проектом (внутренняя информация)")
            # ... (код смены статуса и инженера без изменений) ...
            try: current_status_index = STATUS_OPTIONS.index(current_project.get('status'))
            except ValueError: current_status_index = 0
            try: current_engineer_index = ENGINEER_OPTIONS.index(current_project.get('assigned_engineer'))
            except ValueError: current_engineer_index = 0
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("Изменить статус:", STATUS_OPTIONS, index=current_status_index)
                new_engineer = st.selectbox("Назначить инженера:", ENGINEER_OPTIONS, index=current_engineer_index)
            with col2:
                new_status_desc = st.text_area("Новое описание статуса для клиента:", value=current_project.get('status_desc', ''))
            if st.button("Сохранить изменения статуса и инженера"):
                current_project['status'] = new_status
                current_project['status_desc'] = new_status_desc
                current_project['assigned_engineer'] = new_engineer
                save_projects(st.session_state.projects)
                st.success("Изменения сохранены!"); time.sleep(1); st.rerun()

            st.markdown("---")
            # --- Внутренние комментарии (ИЗМЕНЕНИЯ ЗДЕСЬ) ---
            st.markdown("##### Внутренние комментарии")
            
            with st.form("note_form", clear_on_submit=True):
                new_note_text = st.text_area("Написать новый комментарий (виден только сотрудникам):")
                # <<< 1. ДОБАВЛЕН ЗАГРУЗЧИК ФАЙЛОВ >>>
                attached_files = st.file_uploader(
                    "Прикрепить файлы (только для сотрудников)", 
                    accept_multiple_files=True,
                    key=f"internal_uploader_{project_id}"
                )
                submitted_note = st.form_submit_button("Добавить комментарий")

                if submitted_note and (new_note_text or attached_files):
                    note_author = "Сотрудник"
                    # <<< 2. ЛОГИКА СОХРАНЕНИЯ ФАЙЛОВ >>>
                    attachments_info = []
                    for uploaded_file in attached_files:
                        # Создаем уникальное имя файла, чтобы избежать перезаписи
                        unique_filename = f"{project_id}_{int(time.time())}_{uploaded_file.name}"
                        save_path = os.path.join(UPLOAD_DIR, unique_filename)
                        
                        # Записываем файл на диск
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        attachments_info.append({
                            "original_name": uploaded_file.name,
                            "saved_path": save_path
                        })

                    new_note = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "author": note_author, "text": new_note_text,
                        "attachments": attachments_info # <-- Добавляем информацию о файлах
                    }
                    current_project.setdefault('internal_notes', []).append(new_note)
                    save_projects(st.session_state.projects)
                    st.rerun()

            # --- Отображение существующих комментариев ---
            internal_notes = current_project.get('internal_notes', [])
            if not internal_notes:
                st.info("Внутренних комментариев по этому проекту еще нет.")
            else:
                with st.expander("Показать/скрыть историю комментариев", expanded=True):
                    for note in reversed(internal_notes):
                        st.markdown(f"**{note['author']}** ({note['timestamp']})")
                        if note['text']: st.text(note['text'])
                        
                        # <<< 3. ОТОБРАЖЕНИЕ ССЫЛОК НА СКАЧИВАНИЕ >>>
                        if 'attachments' in note and note['attachments']:
                            st.markdown("**Прикрепленные файлы:**")
                            for attachment in note['attachments']:
                                file_path = attachment['saved_path']
                                if os.path.exists(file_path):
                                    with open(file_path, "rb") as fp:
                                        st.download_button(
                                            label=f"📎 {attachment['original_name']}",
                                            data=fp,
                                            file_name=attachment['original_name'],
                                            key=f"download_{file_path}"
                                        )
                                else:
                                    st.warning(f"Файл '{attachment['original_name']}' не найден на сервере.")
                        st.markdown("---")


        # --- БЛОКИ 4 и 5 (без существенных изменений) ---
        st.markdown("---"); st.subheader("4. Загруженные файлы"); # ... (код)
        uploaded_files_info = current_project.get("uploaded_files_info", [])
        if uploaded_files_info:
            for file_info in uploaded_files_info:
                size_mb = file_info.get('size', 0) / (1024*1024); st.info(f"📄 {file_info.get('name', 'N/A')} ({size_mb:.2f} MB)")
        else: st.write("Клиент не прикрепил файлы.")

        st.markdown("---"); st.subheader("5. Чат по проекту"); # ... (код)
        for message in current_project.get("chat_history", []):
            with st.chat_message(message["role"]): st.markdown(message["content"])
        if prompt := st.chat_input("Напишите ваш вопрос..."):
            role = "assistant" if is_auth else "user"; current_project["chat_history"].append({"role": role, "content": prompt})
            save_projects(st.session_state.projects); st.rerun()
