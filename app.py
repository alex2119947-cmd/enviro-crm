import streamlit as st
import time
from datetime import datetime

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Прототип CRM ENVIRO", layout="wide")

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
# Это "база данных" нашего прототипа
if 'projects' not in st.session_state:
    st.session_state.projects = []

# Отслеживание текущей страницы
if 'page' not in st.session_state:
    st.session_state.page = "client_form"

# --- БОКОВАЯ ПАНЕЛЬ ДЛЯ НАВИГАЦИИ (переключение ролей) ---
st.sidebar.title("Навигация")
role = st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"))

if role == "Новый клиент":
    st.session_state.page = "client_form"
else:
    st.session_state.page = "employee_dashboard"

# ==============================================================================
#                     ВИД КЛИЕНТА: ФОРМА ЗАЯВКИ
# ==============================================================================
if st.session_state.page == "client_form":
    st.title("📋 Анкета для нового клиента")
    st.write("Пожалуйста, заполните эту форму максимально подробно. Это поможет нам подготовить для вас наилучшее предложение.")
    
    with st.form("client_form_enviro"):
        st.subheader("1. Контактная информация")
        name = st.text_input("Имя клиента *", placeholder="Алексей")
        phone = st.text_input("Номер телефона *", placeholder="+996 (XXX) XX-XX-XX")
        email = st.text_input("Email", placeholder="example@email.com")

        st.subheader("2. Информация об объекте")
        col1, col2 = st.columns(2)
        with col1:
            address = st.text_input("Точный адрес *")
            area = st.number_input("Площадь дома (м²) *", min_value=10)
            plot_size = st.number_input("Размер участка (в сотках)", min_value=1)
        with col2:
            floors = st.selectbox("Этажность", ["1 этаж", "2 этажа", "3 этажа", "Более 3"])
            insulation = st.text_input("Наличие и тип утепления *", placeholder="Базальтовая вата 10 см")
            boiler_location = st.text_input("Расположение котельной", placeholder="В подвале / на 1 этаже")
        
        st.subheader("3. Текущие системы (если дом построен)")
        col3, col4 = st.columns(2)
        with col3:
            heating_type = st.text_input("Используемый вид отопления зимой", placeholder="Электрокотел / Газовый котел")
        with col4:
            cooling_type = st.text_input("Используемый вид охлаждения летом", placeholder="Кондиционеры / Ничего")
        
        power_supply = st.text_input("Наличие и мощность электросетей (кВт)", placeholder="3 фазы, 15 кВт")

        st.subheader("4. Дополнительно")
        wishes = st.text_area("Ваши пожелания")
        questions = st.text_area("Ваши вопросы")

        st.markdown("---")
        submitted = st.form_submit_button("Отправить заявку")

        if submitted:
            # Простая валидация
            if not name or not phone or not address or not area or not insulation:
                st.error("Пожалуйста, заполните все обязательные поля, отмеченные звездочкой (*).")
            else:
                # Создаем новый "проект"
                new_project = {
                    "id": len(st.session_state.projects) + 1,
                    "client_name": name,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "area": area,
                    "plot_size": plot_size,
                    "floors": floors,
                    "insulation": insulation,
                    "boiler_location": boiler_location,
                    "heating_type": heating_type,
                    "cooling_type": cooling_type,
                    "power_supply": power_supply,
                    "wishes": wishes,
                    "questions": questions,
                    "status": "На рассмотрении у инженера",
                    "status_desc": "Ожидайте ответа. Наш специалист изучает предоставленные вами данные.",
                    "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "chat_history": [
                        {"role": "assistant", "content": f"Здравствуйте, {name}! Я ваш виртуальный помощник. Ваша заявка принята и уже передана инженеру."}
                    ]
                }
                st.session_state.projects.append(new_project)
                st.session_state.current_project_id = new_project["id"]
                st.session_state.page = "project_page"
                st.experimental_rerun() # Перезагружаем страницу, чтобы показать страницу проекта

# ==============================================================================
#                ВИД СОТРУДНИКА: ПАНЕЛЬ УПРАВЛЕНИЯ
# ==============================================================================
elif st.session_state.page == "employee_dashboard":
    st.title("Панель управления ENVIRO")
    st.subheader("Входящие заявки")

    if not st.session_state.projects:
        st.info("Пока нет ни одной заявки от клиентов.")
    else:
        # Отображаем заявки в обратном порядке (новые сверху)
        for project in reversed(st.session_state.projects):
            with st.expander(f"Заявка №{project['id']} от {project['submission_date']} - {project['client_name']} ({project['address']})"):
                st.metric("Статус", project['status'])
                st.write(f"**Клиент:** {project['client_name']}")
                st.write(f"**Телефон:** {project['phone']}")
                st.write(f"**Площадь дома:** {project['area']} м²")

                if st.button("Просмотреть детали", key=f"details_{project['id']}"):
                    st.session_state.current_project_id = project['id']
                    st.session_state.page = "project_page"
                    st.experimental_rerun()

# ==============================================================================
#                ОБЩИЙ ВИД: СТРАНИЦА КОНКРЕТНОГО ПРОЕКТА
# ==============================================================================
elif st.session_state.page == "project_page":
    # Находим текущий проект
    current_project = next((p for p in st.session_state.projects if p['id'] == st.session_state.current_project_id), None)

    if current_project is None:
        st.error("Проект не найден. Пожалуйста, вернитесь на главную страницу.")
        st.session_state.page = "client_form"
        if st.button("Вернуться"):
            st.experimental_rerun()

    else:
        st.title(f"Страница проекта: {current_project['client_name']}")
        st.markdown("---")

        # --- 1. БЛОК: СТАТУС ЗАЯВКИ ---
        st.subheader("1. Статус вашей заявки")
        st.success(current_project['status'])
        st.info(current_project['status_desc'])
        st.markdown("---")

        # --- Детали заявки (может видеть и клиент, и сотрудник) ---
        with st.expander("Показать/скрыть детали заявки"):
             st.json(current_project) # Простой способ показать все данные

        # --- 2. БЛОК: ЧАТ ---
        st.subheader("2. Чат по проекту")
        
        # Отображение сообщений
        for message in current_project["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Поле для ввода
        if prompt := st.chat_input("Напишите ваш вопрос..."):
            current_project["chat_history"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Логика ИИ-агента
            with st.chat_message("assistant"):
                # ... (логика ответов бота осталась та же) ...
                 message_placeholder = st.empty()
                 time.sleep(1)
                 assistant_response = "Спасибо за ваше сообщение. Я передал его инженеру."
                 message_placeholder.markdown(assistant_response)

            current_project["chat_history"].append({"role": "assistant", "content": assistant_response})
            st.experimental_rerun()

        st.markdown("---")

        # --- 3. БЛОК: КАЛЕНДАРЬ ---
        st.subheader("3. Выберите удобное время для визита инженера")
        st.write("Если потребуется очный осмотр, вы можете заранее выбрать удобный для вас слот.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Пятница, 30 января, 10:00-12:00"):
                st.success("Слот предварительно забронирован. Ожидайте подтверждения.")
                current_project['status'] = "Согласование визита"
                st.experimental_rerun()
        # ... и так далее для других кнопок


