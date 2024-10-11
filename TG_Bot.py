from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

# определяем этапы бота
CHOOSE_STATUS, ENTER_CODE = range(2)

codes = {
    "Администратор": "SUAI1234ZXC",
    "Староста": "SUAI1234QWE",
}

# функция при старте бота, предлагает выбрать статус
async def start(update: Update, context):
    message = "Я - шухер для отслежки посещений. Выбери свой статус :"

    #  кнопки для статусов
    reply_keyboard = [['Студент', 'Староста', 'Администратор']]

    # сообщение с кнопками выбора статуса
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    # возвращаемся на этап выбора статуса
    return CHOOSE_STATUS


# обрабатываем выбор статуса
async def choose_status(update: Update, context):
    user_status = update.message.text
    context.user_data['status'] = user_status
    
    if user_status == 'Студент':
        await update.message.reply_text(f"Вы выбрали: {user_status}")
        return ConversationHandler.END
    
    #запрашиваем код
    await update.message.reply_text(f"Вы выбрали: {user_status}. Введите код доступа:", 
                                    reply_markup=ReplyKeyboardMarkup([['Назад']], one_time_keyboard=True))
    return ENTER_CODE



# проверяем введённый код
async def enter_code(update: Update, context):
    entered_code = update.message.text
    
    # возвращаемся к выбору статуса
    if entered_code == 'Назад':
        await update.message.reply_text("Выбор статуса:",
                                        reply_markup=ReplyKeyboardMarkup([['Студент', 'Староста', 'Администратор']], one_time_keyboard=True))
        return CHOOSE_STATUS
    
    user_status = context.user_data['status']
    
    # правильность кода
    if user_status in codes and entered_code == codes[user_status]:
        await update.message.reply_text(f"Вы успешно вошли как {user_status}.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Неверный код! Попробуйте снова или вернитесь назад к выбору статуса:",
                                        reply_markup=ReplyKeyboardMarkup([['Назад']], one_time_keyboard=True))
        return ENTER_CODE


def main():
    TOKEN = "7500268240:AAEtuPOniFFCnaHSW55eUfe392egvxDONWU"
    application = ApplicationBuilder().token(TOKEN).build()
    
    #  последовательность шагов в боте
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_status)],
            ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_code)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    # добавляем обработчики
    application.add_handler(conv_handler)
    # запускаем бот
    application.run_polling()

if __name__ == '__main__':
    main()
