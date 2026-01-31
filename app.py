import streamlit as st
import time
from datetime import datetime
import base64
import os

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Прототип CRM ENVIRO", layout="wide")

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КОДИРОВАНИЯ ВИДЕО ---
def video_to_base64(path):
    """Кодирует видеофайл в base64 для встраивания в HTML."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode()

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
# ... (остальная часть инициализации без изменений) ...
if 'projects' not in st.session_state:
    st.session_state.projects = []
if 'page' not in st.session_state:
    st.session_state.page = "client_form"
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None

# --- БОКОВАЯ ПАНЕЛЬ ДЛЯ НАВИГАЦИИ ---
st.sidebar.title("Навигация")
role = st.sidebar.radio("Выберите вашу роль:", ("Новый клиент", "Сотрудник ENVIRO"), key="role_selector")

if role == "Сотрудник ENVIRO":
    if st.sidebar.button("Посмотреть все заявки"):
        st.session_state.page = "employee_dashboard"
        st.experimental_rerun()
else:
    if st.session_state.page != "client_form":
         if st.sidebar.button("Заполнить новую анкету"):
            st.session_state.page = "client_form"
            st.session_state.current_project_id = None
            st.experimental_rerun()

st.sidebar.info("Версия прототипа: 2.3")


# ==============================================================================
#                     ВИД КЛИЕНТА: ФОРМА ЗАЯВКИ (ГЛАВНАЯ СТРАНИЦА)
# ==============================================================================
if st.session_state.page == "client_form":
    
    st.header("ENVIRO — комплексные инженерные решения для вашего дома")

    # --- ИЗМЕНЕНИЕ: ЗАМЕНЯЕМ st.video НА HTML-КОД С АВТОПРОИГРЫВАНИЕМ ---
    video_path = "enviro1.mp4"
    video_base64 = video_to_base64(video_path)

    if video_base64:
        video_html = f"""
            <video autoplay loop muted playsinline width="100%">
              <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
              Your browser does not support the video tag.
            </video>
            """
        st.markdown(video_html, unsafe_allow_html=True)
    else:
        # Запасной вариант, если видеофайл не найден
        st.warning("Видео-заставка не найдена. Убедитесь, что файл 'enviro1.mp4' загружен в репозиторий.")

    st.markdown("---")

    st.title("📋 Анкета для нового клиента")
    st.write("Пожалуйста, заполните эту форму максимально подробно.")
    
    with st.form("client_form_enviro"):
        # ... (остальной код анкеты остался без изменений) ...
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
            if not name or not phone or not address or not area or not insulation:
                st.error("Пожалуйста, заполните все обязательные поля, отмеченные звездочкой (*).")
            else:
                new_project = {
                    "id": len(st.session_state.projects) + 1, "client_name": name, "phone": phone, "email": email, "address": address, "area": area, "plot_size": plot_size, "floors": floors, "insulation": insulation, "boiler_location": boiler_location, "heating_type": heating_type, "cooling_type": cooling_type, "power_supply": power_supply, "wishes": wishes, "questions": questions, "status": "На рассмотрении у инженера", "status_desc": "Ожидайте ответа. Наш специалист изучает предоставленные вами данные.", "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "chat_history": [{"role": "assistant", "content": f"Здравствуйте, {name}! Я ваш виртуальный помощник. Ваша заявка принята и уже передана инженеру."}]
                }
                st.session_state.projects.append(new_project)
                st.session_state.current_project_id = new_project["id"]
                st.session_state.page = "project_page"
                st.experimental_rerun()

# ==============================================================================
#                Остальные страницы (Панель управления и Страница проекта)
#                Остались без изменений.
# ==============================================================================
elif st.session_state.page == "employee_dashboard":
    st.title("Панель управления ENVIRO")
    st.subheader("Входящие заявки")
    if not st.session_state.projects:
        st.info("Пока нет ни одной заявки от клиентов.")
    else:
        for project in reversed(st.session_state.projects):
            with st.expander(f"Заявка №{project['id']} от {project['submission_date']} - {project['client_name']} ({project['address']})"):
                st.metric("Статус", project['status'])
                st.write(f"**Клиент:** {project['client_name']}, **Телефон:** {project['phone']}")
                st.write(f"**Площадь дома:** {project['area']} м²")
                if st.button("Просмотреть детали", key=f"details_btn_{project['id']}"):
                    st.session_state.current_project_id = project['id']
                    st.session_state.page = "project_page"
                    st.experimental_rerun()

elif st.session_state.page == "project_page":
    current_project = next((p for p in st.session_state.projects if p['id'] == st.session_state.current_project_id), None)
    if current_project is None:
        st.error("Проект не найден. Пожалуйста, выберите заявку из панели управления.")
        if st.button("Вернуться в панель управления"):
            st.session_state.page = "employee_dashboard"
            st.experimental_rerun()
    else:
        st.title(f"Страница проекта: {current_project['client_name']}")
        st.markdown(f"Заявка №{current_project['id']} от {current_project['submission_date']}")
        st.markdown("---")
        st.subheader("1. Статус заявки")
        st.success(current_project['status'])
        st.info(current_project['status_desc'])
        st.markdown("---")
        with st.expander("Показать/скрыть полные детали заявки"):
             display_data = current_project.copy()
             display_data.pop('chat_history', None)
             st.json(display_data)
        st.subheader("2. Чат по проекту")
        for message in current_project["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if prompt := st.chat_input("Напишите ваш вопрос..."):
            current_project["chat_history"].append({"role": "user", "content": prompt})
            st.experimental_rerun()
