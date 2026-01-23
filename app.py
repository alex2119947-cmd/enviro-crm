import streamlit as st
import time

# --- Настройка страницы ---
st.set_page_config(page_title="Проект ENVIRO", layout="wide")

# --- Данные клиента (для примера) ---
client_name = "Алексей"

# --- Заголовок страницы ---
st.title(f"Страница проекта: {client_name}")
st.markdown("---")

# --- 1. БЛОК: СТАТУС ЗАЯВКИ ---
st.subheader("1. Статус вашей заявки")

# Отображаем статус, как договорились
st.success("На рассмотрении у инженера")
st.info("Ожидайте ответа. Наш специалист изучает предоставленные вами данные и фотографии.")
st.markdown("---")

# --- 2. БЛОК: ЧАТ С ВИРТУАЛЬНЫМ ПОМОЩНИКОМ ---
st.subheader("2. Чат с вашим персональным ИИ-агентом")

# Инициализация истории чата
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Здравствуйте, {client_name}! Я ваш виртуальный помощник. Я получил вашу заявку и уже передал ее инженеру. Если у вас есть вопросы, задавайте их здесь."}
    ]

# Отображение сообщений из истории
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле для ввода нового сообщения
if prompt := st.chat_input("Напишите ваш вопрос..."):
    # Добавляем сообщение пользователя в историю
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Логика ответов ИИ-агента (прототип) ---
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Переводим запрос пользователя в нижний регистр для простоты сравнения
        prompt_lower = prompt.lower()

        if "привет" in prompt_lower:
            assistant_response = "И вам здравствуйте! Чем могу помочь?"
        elif "цена" in prompt_lower or "стоимость" in prompt_lower or "сколько стоит" in prompt_lower:
            assistant_response = (
                "Стоимость системы всегда индивидуальна. Точную цену мы сможем назвать после того, "
                "как инженер завершит расчеты. Это гарантирует, что цена будет фиксированной и не изменится. "
                "Хотите, чтобы я попросил инженера ускорить расчет?"
            )
        elif "когда" in prompt_lower or "сроки" in prompt_lower:
            assistant_response = "Обычно расчет занимает 1-2 рабочих дня. Как только он будет готов, статус вашей заявки обновится, и мы пришлем вам уведомление."
        else:
            assistant_response = (
                "Спасибо за ваш вопрос. Я записал его и передал инженеру. "
                "Он ответит на него в ближайшее время, когда будет готовить для вас предложение."
            )

        # Анимация печати для реалистичности
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})

st.markdown("---")

# --- 3. БЛОК: КАЛЕНДАРЬ ДЛЯ ЗАПИСИ ---
st.subheader("3. Выберите удобное время для визита инженера")
st.write("Если потребуется очный осмотр, вы можете заранее выбрать удобный для вас слот. Мы свяжемся с вами для подтверждения.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Среда, 28 января, 10:00-12:00"):
        st.success("Отлично! Мы предварительно забронировали для вас этот слот. Ожидайте подтверждения.")

with col2:
    if st.button("Среда, 28 января, 14:00-16:00"):
        st.success("Отлично! Мы предварительно забронировали для вас этот слот. Ожидайте подтверждения.")

with col3:
    if st.button("Четверг, 29 января, 11:00-13:00"):
        st.success("Отлично! Мы предварительн�� забронировали для вас этот слот. Ожидайте подтверждения.")

