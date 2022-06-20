from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from redminelib import Redmine

TOKEN = "<token>"
REDMINE_URL = "<url>"


def start(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    if "api" not in context.user_data:
        update.message.reply_text(
            'Привет! Используйте команду /api <свой ключ api> чтобы запустить бота')
        return

    remove_jobs_if_exist(chat_id, context)
    context.job_queue.run_repeating(
        alarm, 10, 1, context=context, name=chat_id)
    update.message.reply_text('Бот запущен!')


def alarm(context: CallbackContext) -> None:
    user_data = context.job.context.user_data
    new_issues_id = []
    old_issues_id = user_data["issues_old"] if "issues_old" in user_data else []

    redmine = Redmine(REDMINE_URL, key=user_data["api"])
    issues = redmine.issue.filter(status_id="open", assigned_to_id="me")

    for issue in issues:
        new_issues_id.append(issue.id)

        if issue.id not in old_issues_id:
            txt = "Номер задачи: <a href='{0}/issues/{1}'>{1}</a>\nТема задачи: {2}\nНазначена: {3}\nТрекер: {4}\nСтатус: {5}\nПриоритет: {6}".format(
                REDMINE_URL, issue.id, issue.subject, issue.assigned_to, issue.tracker, issue.status, issue.priority)
            context.bot.send_message(
                user_data["chat_id"], text=txt, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    user_data["issues_old"] = new_issues_id.copy()


def jobs_exist(name: str, context: CallbackContext) -> bool:
    return bool(context.job_queue.get_jobs_by_name(name))


def remove_jobs_if_exist(name: str, context: CallbackContext) -> None:
    if jobs_exist(name, CallbackContext):
        current_jobs = context.job_queue.get_jobs_by_name(name)
        for job in current_jobs:
            job.schedule_removal()


def api(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    api_key = str(context.args[0])

    if len(api_key) != 40:
        update.message.reply_text(
            'Введен некорректный ключ API, используйте команду: /api <ключ api>')
        return

    context.user_data["api"] = api_key
    context.user_data["chat_id"] = update.message.chat_id
    remove_jobs_if_exist(chat_id, context)
    context.job_queue.run_repeating(
        alarm, 10, 1, context=context, name=chat_id)
    update.message.reply_text('Бот запущен!')


def stop(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    jobs_removed = jobs_exist(chat_id, context)
    remove_jobs_if_exist(chat_id, context)

    update.message.reply_text('Обновление задач отменено' if jobs_removed else 'У Вас нет активных обновлений задач')


def main() -> None:
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("api", api))
    updater.dispatcher.add_handler(CommandHandler("help", start))
    updater.dispatcher.add_handler(CommandHandler("stop", stop))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
