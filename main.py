import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv

load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SMTP_EMAIL = os.getenv('SMTP_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

EMAIL, MESSAGE = range(2)

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.yandex.ru', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")
        return False

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Пожалуйста, введи email, на который будет отправлено сообщение:")
    return EMAIL

async def handle_email(update: Update, context: CallbackContext):
    email = update.message.text

    if is_valid_email(email):
        context.user_data['email'] = email
        await update.message.reply_text("Email принят! Теперь введите текст сообщения:")
        return MESSAGE
    else:
        await update.message.reply_text("Неверный email, пожалуйста, введите корректный email:")
        return EMAIL

async def handle_message(update: Update, context: CallbackContext):
    message_text = update.message.text
    email = context.user_data.get('email')

    if email:
        if send_email(email, "Сообщение от Telegram бота", message_text):
            await update.message.reply_text(f"Сообщение отправлено на {email}!")
        else:
            await update.message.reply_text("Произошла ошибка при отправке сообщения.")
    else:
        await update.message.reply_text("Произошла ошибка. Сначала введите email.")
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Обработка прервана.")
    return ConversationHandler.END


application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
        MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
application.add_handler(conversation_handler)
application.run_polling()
