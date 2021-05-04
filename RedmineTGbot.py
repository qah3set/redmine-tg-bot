from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from redminelib import Redmine

token = "<token>"
redmine_url = "<url>"

def start(update: Update, context: CallbackContext) -> None:

    chat_id = update.message.chat_id

    if "api" in context.user_data:

        remove_job_if_exists(str(chat_id), context)

        context.job_queue.run_repeating(
            alarm, 10, 1, context=context, name=str(chat_id))
        update.message.reply_text('Бот запущен!')
    else:

        update.message.reply_text(
            'Привет! Используйте команду /api <свой ключ api> чтобы запустить бота')


def alarm(context: CallbackContext) -> None:

    user_data = context.job.context.user_data
    api = user_data["api"]
    chat_id = user_data["chat_id"]
    issues_new = []
    issues_old = []
    if "issues_old" in user_data:
        issues_old = user_data["issues_old"]

    redmine = Redmine(redmine_url, key=api)
    issues = redmine.issue.filter(status_id="open", assigned_to_id="me")

    for issue in issues:
        issues_new.append(issue.id)

        if issue.id not in issues_old:
            txt = "Номер задачи: <a href='{0}/issues/{1}'>{1}</a>\nТема задачи: {2}\nНазначена: {3}\nТрекер: {4}\nСтатус: {5}\nПриоритет: {6}".format(
                redmine_url, issue.id, issue.subject, issue.assigned_to, issue.tracker, issue.status, issue.priority)
            context.bot.send_message(
                chat_id, text=txt, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    issues_old = issues_new.copy()

    user_data["issues_old"] = issues_old


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def api(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    api = str(context.args[0])

    if len(api) != 40:
        update.message.reply_text(
            'Введен некорректный ключ API, используйте команду: /api <ключ api>')
        return

    context.user_data["api"] = api
    context.user_data["chat_id"] = chat_id
    remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(
        alarm, 10, 1, context=context, name=str(chat_id))
    update.message.reply_text('Бот запущен!')


def stop(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Обновление задач отменено' if job_removed else 'У Вас нет активных обновлений задач'

    update.message.reply_text(text)


def main() -> None:

    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("api", api))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("stop", stop))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
