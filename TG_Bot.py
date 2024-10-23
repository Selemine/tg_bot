from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

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

    await update.message.reply_text(f"Группа {group_number} добавлена. Введите ФИО участника группы:")
    context.user_data['members'] = []  # Инициализация списка участников
    return ENTER_ANOTHER_MEMBER

# обработка ввода участников по одному
async def enter_another_member(update: Update, context):
    member_name = update.message.text
    context.user_data['members'].append(member_name.strip())  # Сохранение ФИО участника

    await update.message.reply_text(f"✅ Участник '{member_name.strip()}' добавлен. Введите ФИО следующего участника или нажмите '✅ Завершить' для завершения ввода:",
                                     reply_markup=ReplyKeyboardMarkup([['✅ Завершить']], resize_keyboard=True))
    
    return ENTER_ANOTHER_MEMBER

async def finish_members(update: Update, context):
    if update.message.text == '✅ Завершить':
        await update.message.reply_text(f"✅ Участники группы {context.user_data['group_number']} успешно добавлены:\n" + 
                                         "\n".join(context.user_data['members']))
        return ConversationHandler.END
    
    return await enter_another_member(update, context)

# основной код для запуска бота
def main():
    TOKEN = "7500268240:AAEtuPOniFFCnaHSW55eUfe392egvxDONWU"  # Ваш токен
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            CHOOSE_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_status)],
            ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_code)],
            ADD_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_group)],
            ENTER_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_group)],
            ENTER_ANOTHER_MEMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_members)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
