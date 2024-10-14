from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

# этапы бота
ASK_NAME, CHOOSE_STATUS, ENTER_CODE = range(3)

codes = {
    "👨‍💻 Администратор": "SUAI6666ZXC_Admin_6699",
    "👨‍🎓 Староста": "SUAI1234ZXC_Elder_5775",
    "👩‍🏫 Преподаватель": "SUAI5678ASD_Teacher_2332",
}

# функция при старте бота, ввод фио
async def start(update: Update, context):
    message = "👋 Пожалуйста, введите ваше ФИО в формате: Иванов Иван Иванович"
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
    return ASK_NAME

async def ask_name(update: Update, context):
    full_name = update.message.text
    context.user_data['full_name'] = full_name

    # if len(full_name.split()) != 3:
        # await update.message.reply_text("❌ Неверный формат ФИО. Пожалуйста, введите ФИО в формате: Иванов Иван Иванович")
        # return ASK_NAME

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

    if user_status == '🎓 Студент':
        await update.message.reply_text(f"✅ Вы успешно выбрали статус: {user_status}. Ваше ФИО: {context.user_data['full_name']}")
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

    # кнопка назад
    if entered_code == '🔙Назад':
        await update.message.reply_text(
            "Выбор статуса:",
            reply_markup=ReplyKeyboardMarkup(
                [['🎓 Студент', '👨‍🎓 Староста'], ['👩‍🏫 Преподаватель', '👨‍💻 Администратор']],
                resize_keyboard=True
            )
        )
        return CHOOSE_STATUS

    # проверка ввода самого кода
    correct_code = codes.get(user_status)

    if correct_code and entered_code == correct_code:
        await update.message.reply_text(f"✅ Вы успешно вошли как {user_status}. Ваше ФИО: {context.user_data['full_name']}")
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Неверный код! Попробуйте снова или вернитесь назад к выбору статуса:",
            reply_markup=ReplyKeyboardMarkup([['🔙Назад']], resize_keyboard=True)
        )
        return ENTER_CODE

# основной код для запуска бота
def main():
    TOKEN = "7500268240:AAEtuPOniFFCnaHSW55eUfe392egvxDONWU"
    application = ApplicationBuilder().token(TOKEN).build()

    # этапы бота
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            CHOOSE_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_status)],
            ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_code)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # запуск бота
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
