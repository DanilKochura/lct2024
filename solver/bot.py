import time
from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from solver_bot import solve_schedules_bot

bots = ["Бухта Север и Диксон", "Дудинка", "кромка льда на Западе", "Варандей-Приразломное",
        "Штокман", "Окно в Европу", "Победа месторождение", "Карское - 3 (центр)", "пролив Вилькицкого - 3",
        "Лаптевых - 4 (юг)", "Вход в Обскую губу", "Новый порт", "Лаптевых - 1 (центр)",
        "Карское - 1 (сбор каравана)", "Лескинское м-е", "Карские ворота", "Мыс Желания",
        "остров Врангеля", "Восточно-Сибирское 1", "пролив Вилькицкого - восток", "пролив Вилькицкого - запад",
        "около Новой Земли", "Пролив Санникова - 1", "Пролив Санникова - 2", "устье Лены", "Сабетта", "мыс.Наглёйнын",
        "пролив Лонга", "Восточно-Сибирское 3", "Архангельск", "Лаптевых - 3 (восток)", "МОТ Печора",
        "Хатангский залив", "Восточно-Сибирское - 2 (запад)", "Ленинградское-Русановское", "терминал Утренний",
        "Таймырский залив", "Берингово", "кромка льда на Востоке", "Рейд Певек", "Лаптевых - 2 (центр)", "Рейд Мурманска",
        "остров Котельный", "Карское - 2 (прибрежный)", "Индига", "Берингов пролив", "Окно в Азию"
        ]

ports_buttons = [["Окно в Европу", "Новый порт", "пролив Лонга"], ["Индига", "Дудинка", "устье Лены"], ["Штокман", "терминал Утренний", "Победа месторождение"]]

# Ваш токен, полученный от BotFather
TOKEN = '7350169585:AAGb_eAavS9G376d1ZHk0VECCIJ7pyVhXh8'

# Определение состояний разговора
NAME, SPEED, ICE_CLASS, DEPARTURE, DESTINATION, MONTH, DAY = range(7)

# Словарь месяцев для преобразования текста в номер месяца
MONTHS = {
    'Январь': 1,
    'Февраль': 2,
    'Март': 3,
    'Апрель': 4,
    'Май': 5,
    'Июнь': 6,
    'Июль': 7,
    'Август': 8,
    'Сентябрь': 9,
    'Октябрь': 10,
    'Ноябрь': 11,
    'Декабрь': 12,
}

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Введите <b>название судна</b>:', parse_mode=ParseMode.HTML)
    return NAME

# Функция для получения названия судна
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text('Введите <b>скорость судна</b> (число):', parse_mode=ParseMode.HTML)
    return SPEED

# Функция для получения скорости судна
async def get_speed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        speed = int(update.message.text)
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите <b>число</b>.', parse_mode=ParseMode.HTML)
        return SPEED

    context.user_data['speed'] = speed
    ice_classes = [['нет', 'Arc4', 'Arc5', 'Arc6', 'Arc7']]
    await update.message.reply_text('Выберите <b>ледовый класс</b> судна:', reply_markup=ReplyKeyboardMarkup(ice_classes, one_time_keyboard=True), parse_mode=ParseMode.HTML)
    return ICE_CLASS

# Функция для получения ледового класса
async def get_ice_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ice_class = update.message.text
    if ice_class not in ['нет', 'Arc4', 'Arc5', 'Arc6', 'Arc7']:
        await update.message.reply_text('Пожалуйста, выберите ледовый класс из предложенных вариантов.')
        return DEPARTURE
    context.user_data['ice_class'] = update.message.text
    await update.message.reply_text('Выберите <b>пункт отправления</b>:', reply_markup=ReplyKeyboardMarkup(ports_buttons, one_time_keyboard=True), parse_mode=ParseMode.HTML)
    return DEPARTURE

# Функция для получения пункта отправления
async def get_departure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    departure = update.message.text
    if departure not in bots:
        await update.message.reply_text('Пожалуйста, выберите пункт отправления из предложенных вариантов.')
        return DEPARTURE
    context.user_data['departure'] = departure
    await update.message.reply_text('Выберите <b>пункт назначения</b>:', reply_markup=ReplyKeyboardMarkup(ports_buttons, one_time_keyboard=True), parse_mode=ParseMode.HTML)
    return DESTINATION

# Функция для получения пункта назначения
async def get_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    destination = update.message.text
    if destination not in bots:
        await update.message.reply_text('Пожалуйста, выберите пункт назначения из предложенных вариантов.')
        return DESTINATION
    context.user_data['destination'] = destination
    months = [['Март', 'Апрель'], ['Май', 'Июнь', 'Июль', 'Август'], ['Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']]
    await update.message.reply_text('Выберите <b>месяц отправления</b>:', reply_markup=ReplyKeyboardMarkup(months, one_time_keyboard=True), parse_mode=ParseMode.HTML)
    return MONTH

# Функция для получения месяца отправления
async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['month'] = update.message.text
    await update.message.reply_text('Введите <b>день отправления</b> (число):', parse_mode=ParseMode.HTML)
    return DAY

# Функция для получения дня отправления и проверки даты
async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        day = int(update.message.text)
        month = MONTHS[context.user_data['month']]
        year = 2022  # Используем текущий год для проверки даты
        context.user_data['date_true'] = datetime(year, month, day)  # Проверка корректности даты
        context.user_data['day'] = day
    except (ValueError, KeyError):
        await update.message.reply_text('Пожалуйста, введите корректную <b>дату</b>.', parse_mode=ParseMode.HTML)
        return DAY

    # Отправка сообщения о начале расчета
    loading_message = await update.message.reply_text('🤖 <i>Расчитываю....</i>', parse_mode=ParseMode.HTML)

    user_data = context.user_data
    await update.message.reply_text(
        f"<b>Название судна</b>: {user_data['name']}\n"
        f"<b>Скорость судна</b>: {user_data['speed']}\n"
        f"<b>Ледовый класс</b>: {user_data['ice_class']}\n"
        f"<b>Пункт отправления</b>: {user_data['departure']}\n"
        f"<b>Пункт назначения</b>: {user_data['destination']}\n"
        f"<b>Дата отправления</b>: {user_data['day']} {user_data['month']}",
        parse_mode=ParseMode.HTML
    )

    # Отправка "чат-экшн" уведомления (typing)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    gant, routes = solve_schedules_bot(user_data['name'], user_data['ice_class'], user_data['speed'], user_data['departure'], user_data['destination'], user_data['date_true'])

    # Удаление сообщения "Расчитываю...."
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_message.message_id)

    for route in routes:
        await update.message.reply_text(
            route,
            parse_mode=ParseMode.HTML
        )


    # Отправка изображения
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(gant, 'rb'))

    return ConversationHandler.END

# Функция для отмены разговора
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('<i>Диалог отменен.</i>', parse_mode=ParseMode.HTML)
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SPEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_speed)],
            ICE_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ice_class)],
            DEPARTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_departure)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_destination)],
            MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_month)],
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
