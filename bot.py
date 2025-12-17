import os
import pandas as pd
from analyzer import FinanceAnalyzer
from telegram import Update, ReplyKeyboardMarkup
from db import init_db, import_stock_csv, get_user_data, import_user_csv
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8319847829:AAFrL_cQ0qf9tRokwmLFutLaOCdArKVKD7c"
main_menu = ReplyKeyboardMarkup([["📊 Анализ", "📈 Графики"],["📄 Полный отчёт", "💡 Рекомендация"], ["🔁 Сменить источник данных"]], resize_keyboard=True)
analitics_menu = ReplyKeyboardMarkup([["₽ Топ расходов", "💰 Топ доходов"],["📉 Средняя трата", "🏢 Компании"],["⬅ Назад"]],resize_keyboard=True)
graphs_menu = ReplyKeyboardMarkup([["📊 Доходы/Расходы", "📈 Доходы/Расходы c балансом"],["🥧 Категории", "🏢 Компании"],["⬅ Назад"]],resize_keyboard=True)
data_menu = ReplyKeyboardMarkup([["📂 Использовать демонстрационные данные"],["📎 Загрузить свои данные"],],resize_keyboard=True)

init_db()
import_stock_csv("finance_data_finished.csv")

def get_analyzer(user_id, source):
    if source == "stock":
        rows = get_user_data(None)
    else:
        rows = get_user_data(user_id)
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["date", "type", "category", "company", "amount"])
    return FinanceAnalyzer(df)

async def start_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):       #1 Стартовая команда
    welcome = '''
Привет! Я твой персональный финансовый помощник!

Здесь ты можешь:

• 📊 Анализировать доходы и расходы
• 📈 Строить графики финансовой активности
• 🏆 Видеть топ категорий трат
• 💡 Получать рекомендации по оптимизации бюджета

!Доступные команды!:

/start — Начать
📂 Использовать демонстрационные данные
📎 Загрузить свои данные

Управляйте финансами с умом! 💰'''
    context.user_data["choosing_data"] = True
    await upd.message.reply_text(welcome, reply_markup=data_menu)
    return

async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):        #2 Обработчик ошибок
    print("Ошибка:", context.error)

async def top_income_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):         #3 Топ доходов
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    text = "💰 Топ доходов:\n"
    for company, value in fin_anlz.top_categories_income().items():
        text += f"{company}: {value:.2f}\n"

    await upd.message.reply_text(text)
    return

async def top_waste_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):          #4 Топ расходов
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    text = "💰 Топ трат:\n"
    for company, value in fin_anlz.top_categories_waste().items():
        text += f"{company}: {value:.2f}\n"

    await upd.message.reply_text(text)
    return

async def avg_waste_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):          #5 Средняя трата
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    await upd.message.reply_text(f"📉 Средняя трата: {fin_anlz.avg_waste():.2f}")
    return

async def top_companies_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):          #6 Топ компаний по доходам/тратам
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    waste, income = fin_anlz.top_companies()

    text = "🏢 Компании (расходы):\n"
    for company, value in waste.items():
        text += f"{company}: {value:.2f}\n"

    text += "\n🏢 Компании (доходы):\n"
    for company, value in income.items():
        text += f"{company}: {value:.2f}\n"

    await upd.message.reply_text(text)
    return

async def plot_standart_graph_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):       #7 Стандартный график доход/расход
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    os.makedirs("Graphs", exist_ok=True)
    path = f"Graphs/standart_{upd.effective_user.id}.png"
    fin_anlz.plot_statistics(path)

    await upd.message.reply_photo(photo=open(path, "rb"))
    return

async def plot_balance_graph_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):        #8 График доход/расход + баланс пользователя
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    os.makedirs("Graphs", exist_ok=True)
    path = f"Graphs/balance_{upd.effective_user.id}.png"
    fin_anlz.plot_statistics_with_balance(path)

    await upd.message.reply_photo(photo=open(path, "rb"))
    return

async def plot_categories_pie_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):         #9 Круговая диаграмма по тратам в категориях
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    os.makedirs("Graphs", exist_ok=True)
    path = f"Graphs/pie_{upd.effective_user.id}.png"

    fin_anlz.plot_pie_categories(path)
    await upd.message.reply_photo(photo=open(path, "rb"))
    return

async def plot_companies_bar_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):       #10 Гистограмма по тратам в компаниях
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    os.makedirs("Graphs", exist_ok=True)
    path = f"Graphs/companies_{upd.effective_user.id}.png"

    fin_anlz.plot_bar_companies(output=path)
    await upd.message.reply_photo(photo=open(path, "rb"))
    return

async def recommendation_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):       #11 Рекомендация к ведению финансов
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    await upd.message.reply_text(fin_anlz.recommendation())
    return

async def report_command(upd: Update, context: ContextTypes.DEFAULT_TYPE):         #12 Полный отчет по финансам
    source = context.user_data.get("data_source", "stock")
    fin_anlz = get_analyzer(upd.effective_user.id, source)
    if not fin_anlz:
        await upd.message.reply_text("Нет данных")
        return

    await upd.message.reply_text(fin_anlz.full_report())
    return

async def logic_handler(upd: Update, context: ContextTypes.DEFAULT_TYPE):        #13 - вывод в чате куда мы идем
    text = upd.message.text
    mode = context.user_data.get("mode")

    is_choosing_data_source = context.user_data.get("choosing_data", False)
    
    if text == "🔁 Сменить источник данных":
        context.user_data["choosing_data"] = True
        await upd.message.reply_text('''
Выбери источник данных:
 📂 Использовать демонстрационные данные
 📎 Загрузить свои данные''', reply_markup=data_menu)
        return

    if text == "📂 Использовать демонстрационные данные":
        context.user_data["data_source"] = "stock"
        context.user_data["choosing_data"] = False
        await upd.message.reply_text("✔ Используются демонстрационные данные", reply_markup=main_menu)
        await upd.message.reply_text('''
📊 Анализ — Быстрый анализ доходов и расходов
📈 Графики — График финансов с балансом
📄 Полный отчёт — Полный финансовый отчет
💡 Рекомендация — Советы по улучшению финансов''', reply_markup=main_menu)
        return

    if text == "📎 Загрузить свои данные":
        context.user_data["data_source"] = "user"
        context.user_data["choosing_data"] = True
        await upd.message.reply_text('''📎 Загрузи в чат свой CSV-файл в формате:
 id,date,category,amount,type,company
 Пример:
 1,2024-01-01,Зарплата,50000,доход,Компания''', reply_markup=ReplyKeyboardMarkup([["⬅ Назад"]], resize_keyboard=True))
        return

    if text == "📊 Анализ":
        context.user_data["mode"] = "analyze"
        await upd.message.reply_text('''
📊 Анализ: выбери что именно хочешь посмотреть:
 Топ доходов
 Топ расходов
 Средняя трата за период
 Топ компаний по тратам''', reply_markup=analitics_menu)
        return
    
    if text == "📈 Графики":
        context.user_data["mode"] = "graphs"
        await upd.message.reply_text('''
📈 Графики: выбери тип интересующего графика:
 Доходы/Расходы
 Доходы/Расходы с балансом
 Категории
 Топ компаний по тратам''', reply_markup=graphs_menu)
        return
    
    if text == "📄 Полный отчёт":
        context.user_data["mode"] = "report"
        await report_command(upd, context)
        return
    
    if text == "💡 Рекомендация":
        context.user_data["mode"] = "rec"
        await recommendation_command(upd, context)
        return
    
    if text == "⬅ Назад":
        if is_choosing_data_source:
            await upd.message.reply_text('''
Выбери источник данных:
 📂 Использовать демонстрационные данные
 📎 Загрузить свои данные''', reply_markup=data_menu)
        else:
            context.user_data["mode"] = None
            await upd.message.reply_text("Вы в главном меню, о чем хочешь узнать?\n 📊 Анализ\n 📈 Графики\n 📄 Полный отчёт\n 💡 Рекомендация", reply_markup=main_menu)
        return
    
    if mode == "analyze":
        if text == "₽ Топ расходов":
            await top_waste_command(upd, context)
            return
        elif text == "💰 Топ доходов":
            await top_income_command(upd, context)
            return
        elif text == "📉 Средняя трата":
            await avg_waste_command(upd, context)
            return
        elif text == "🏢 Компании":
            await top_companies_command(upd, context)
            return
        else:
            await upd.message.reply_text("Выбери пункт из меню")
        return
    if mode == "graphs":
        if text == "📊 Доходы/Расходы":
            await plot_standart_graph_command(upd, context)
            return
        elif text == "📈 Доходы/Расходы c балансом":
            await plot_balance_graph_command(upd, context)
            return
        elif text == "🥧 Категории":
            await plot_categories_pie_command(upd, context)
            return
        elif text == "🏢 Компании":
            await plot_companies_bar_command(upd, context)
            return
        else:
            await upd.message.reply_text("Выбери график из меню")
        return

async def document_handler(upd: Update, context: ContextTypes.DEFAULT_TYPE):        #14 Загрузка документа (CSV-файла)
    doc = upd.message.document
    if not doc:
        return

    if not doc.file_name.lower().endswith(".csv"):
        await upd.message.reply_text("❌ Нужен CSV-файл")
        return

    os.makedirs("loads_csv", exist_ok=True)
    path = f"loads_csv/{upd.effective_user.id}.csv"

    file = await doc.get_file()
    await file.download_to_drive(path)

    try:
        import_user_csv(path, upd.effective_user.id)
    except Exception as e:
        await upd.message.reply_text(f"❌ Ошибка загрузки CSV:\n{e}")
        return

    await upd.message.reply_text('''
✔️ Данные успешно загружены!
Теперь можешь пользоваться анализом 📊''', reply_markup=main_menu)
    context.user_data["data_source"] = "user"
    context.user_data["choosing_data"] = False
    await upd.message.reply_text('''
📊 Анализ — Быстрый анализ доходов и расходов
📈 Графики — График финансов с балансом
📄 Полный отчёт — Полный финансовый отчет
💡 Рекомендация — Советы по улучшению финансов''', reply_markup=main_menu)
    return


def main():
    app = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, logic_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == "__main__":
    main()