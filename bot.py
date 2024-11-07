from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

import db_functions  # Импортируем модуль для работы с базой данных

# этапы бота
ASK_NAME, CHOOSE_STATUS, ENTER_CODE, ADD_GROUP, ENTER_GROUP, ENTER_ANOTHER_MEMBER = range(6)

codes = {
    "👨‍💻 Администратор": "1",
    "👨‍🎓 Староста": "2",
    "👩‍🏫 Преподаватель": "3",
}

# функция при старте бота, ввод фио
async def start(update: Update, context):
    message = "👋 Пожалуйста, введите ваше ФИО в формате: Иванов Иван Иванович"
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
    return ASK_NAME

async def ask_name(update: Update, context):
    full_name = update.message.text
    context.user_data['full_name'] = full_name

    message = "👇Выберите свой статус:"
    reply_keyboard = [['🎓 Студент', '👨‍🎓 Староста'], ['👩‍🏫 Преподаватель', '👨‍💻 Администратор']]

    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CHOOSE_STATUS

# обработка выбора статуса
async def choose_status(update: Update, context):
    user_status = update.message.text
    context.user_data['status'] = user_status

    # Для "Студента" пропускаем ввод кода и сразу завершаем авторизацию
    if user_status == '🎓 Студент':
        await update.message.reply_text(f"✅ Вы успешно вошли как {user_status}. Ваше ФИО: {context.user_data['full_name']}")
        return ConversationHandler.END

    await update.message.reply_text(
        f"Вы выбрали: {user_status}. Введите код доступа:",
        reply_markup=ReplyKeyboardMarkup([['🔙Назад']], resize_keyboard=True)
    )
    return ENTER_CODE

# обработка кода доступа
async def enter_code(update: Update, context):
    entered_code = update.message.text
    user_status = context.user_data['status']

    if entered_code == '🔙Назад':
        await update.message.reply_text(
            "Выбор статуса:",
            reply_markup=ReplyKeyboardMarkup(
                [['🎓 Студент', '👨‍🎓 Староста'], ['👩‍🏫 Преподаватель', '👨‍💻 Администратор']],
                resize_keyboard=True
            )
        )
        return CHOOSE_STATUS

    correct_code = codes.get(user_status)

    if correct_code and entered_code == correct_code:
        await update.message.reply_text(f"✅ Вы успешно вошли как {user_status}. Ваше ФИО: {context.user_data['full_name']}")

        # Специальное меню для старосты
        if user_status == '👨‍🎓 Староста':
            message = "Выберите действие:"
            reply_keyboard = [['➕ Добавить группу'], ['🔙 Назад']]  # Кнопка "Назад" добавлена
            await update.message.reply_text(
                message,
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            )
            return ADD_GROUP

        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Неверный код! Попробуйте снова или вернитесь назад к выбору статуса:",
            reply_markup=ReplyKeyboardMarkup([['🔙Назад']], resize_keyboard=True)
        )
        return ENTER_CODE

# обработка добавления группы
async def add_group(update: Update, context):
    user_action = update.message.text

    if user_action == '🔙 Назад':
        return await choose_status(update, context)

    if user_action == '➕ Добавить группу':
        await update.message.reply_text("Введите номер группы:")
        return ENTER_GROUP

async def enter_group(update: Update, context):
    group_number = update.message.text
    context.user_data['group_number'] = group_number

    # Создаем группу в базе данных
    db_functions.create_group(group_number, context.user_data['full_name'])

    await update.message.reply_text(f"Группа {group_number} добавлена. Введите ФИО участника группы:")
    context.user_data['members'] = []  # Инициализация списка участников
    return ENTER_ANOTHER_MEMBER




# обработка ввода участников по одному
async def enter_another_member(update: Update, context):
    member_name = update.message.text

    # Обработка нажатия кнопки "Завершить"
    if member_name == '✅ Завершить':
        # Собираем информацию о группе
        group_number = context.user_data['group_number']
        members = context.user_data['members']  # Список участников без старосты
        leader = context.user_data['full_name']  # Староста
        number_of_members = len(members) + 1  # Учитываем старосту как участника

        # Формируем сообщение с номером группы и списком участников
        group_info = f"     <u>{group_number}</u>     \n"  # Номер группы подчёркнутый
        group_info += "\n"  # Вторая строка: пустая
        group_info += f"<i>Список группы ({number_of_members})</i>\n"  # Курсив с количеством участников
        group_info += "\n"  # Четвертая строка: пустая

        # Включаем старосту в общий список участников и сортируем его
        sorted_members = sorted([leader] + members)  # Староста вначале и сортировка всех участников

        # Добавляем участников в сообщение, выделяя старосту жирным шрифтом
        for member in sorted_members:
            if member == leader:
                group_info += f"<b>{member}</b>  👨‍🎓\n"  # Староста выделяется жирным и смайлик
            else:
                group_info += f"{member}\n"

        # Создаём inline кнопки
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data='confirm_group')],
            [InlineKeyboardButton("❌ Отменить", callback_data='cancel_group')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с информацией о группе
        await update.message.reply_text(group_info, parse_mode="HTML", reply_markup=reply_markup)
        return ConversationHandler.END

    # Добавляем участника в список
    context.user_data['members'].append(member_name.strip())  # Сохранение ФИО участника

    # Добавляем участника в базу данных
    db_functions.add_member(member_name.strip(), context.user_data['group_number'])

    await update.message.reply_text(f"✅ Участник '{member_name.strip()}' добавлен. Введите ФИО следующего участника или нажмите '✅ Завершить' для завершения ввода:",
                                     reply_markup=ReplyKeyboardMarkup([['✅ Завершить']], resize_keyboard=True))

    return ENTER_ANOTHER_MEMBER


# обработка действий по кнопкам
async def button(update: Update, context):
    query = update.callback_query
    await query.answer()  # Это нужно для обработки нажатия кнопки

    # Если нажата кнопка "Подтвердить"
    if query.data == 'confirm_group':
        # Добавляем старосте кнопку "Просмотреть дисциплины"
        reply_keyboard = [['👨‍🎓 Просмотреть дисциплины']]
        await query.edit_message_text("✅ Информация о группе подтверждена!", reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))

    # Если нажата кнопка "Отменить"
    elif query.data == 'cancel_group':
        # Стираем все данные о группе и возвращаем старосту к вводу номера группы
        context.user_data['group_number'] = ''
        context.user_data['members'] = []
        await query.edit_message_text("❌ Информация о группе отменена. Введите номер группы заново.")








# основной код для запуска бота
def main():
    TOKEN = "7500268240:AAEtuPOniFFCnaHSW55eUfe392egvxDONWU"  # Ваш токен
    application = ApplicationBuilder().token(TOKEN).build()

    # создаём таблицы при запуске бота
    db_functions.create_tables()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            CHOOSE_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_status)],
            ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_code)],
            ADD_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_group)],
            ENTER_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_group)],
            ENTER_ANOTHER_MEMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_another_member)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, enter_another_member)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
