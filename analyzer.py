import pandas as pd
import matplotlib.pyplot as plt

class FinanceAnalyzer:
    def __init__(self, data):   #Загрузка и первичная обработка данных
        if isinstance(data, str):
            self.data = pd.read_csv(data)
        else:
            self.data = data.copy()

        self.data["date"] = pd.to_datetime(self.data["date"])   # Приводим дату
        self.data.sort_values("date", inplace=True)
   
    # 1. Сумма доходов и расходов по дням
    def daily_stats(self):
        return (self.data.groupby(["date", "type"])["amount"].sum().unstack().fillna(0))  # Таблица доходов / расходов 
   
    # 2. Топ-n категорий расходов (по умолчанию 3)
    def top_categories_waste(self, n=3):
        df_waste = self.data[self.data["type"] == "расход"]
        return (df_waste.groupby("category")["amount"].sum().sort_values(ascending=False).head(n).to_dict())  # Словарь первых n значений расходов
    
    # 3. Топ-n категорий доходов (по умолчанию 3)
    def top_categories_income(self, n=3):
        df_inc = self.data[self.data["type"] == "доход"]
        return (df_inc.groupby("category")["amount"].sum().sort_values(ascending=False).head(n).to_dict())    # Словарь первых n значений доходов

    # 4. Средняя трата за весь период
    def avg_waste(self):
        df_waste = self.data[self.data["type"] == "расход"]
        return round(df_waste["amount"].mean(), 2)

    # 5. Топ n компаний по доходам и расходам
    def top_companies(self, n=5):
        df = self.data
        waste = (df[df["type"] == "расход"].groupby("company")["amount"].sum().sort_values(ascending=False).head(n).to_dict())   # Словарь n компаний по расходам
        incomes = (df[df["type"] == "доход"].groupby("company")["amount"].sum().sort_values(ascending=False).head(n).to_dict())  # Словарь n компаний по доходам
        return (waste, incomes)

    # 6. График доходов/расходов по времени
    def plot_statistics(self, output="finance_plot.png"):
        daily = self.daily_stats()

        plt.figure(figsize=(10, 5))
        plt.plot(daily.index, daily["доход"], label="Доходы", color="green")
        plt.plot(daily.index, daily["расход"], label="Расходы",  color="red")
        plt.title("Доходы и расходы по дням")
        plt.xlabel("Дата")
        plt.ylabel("Сумма")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig(output)
        plt.close()

        return output
    
    # График доходов/расходов по времени с балансом
    def plot_statistics_with_balance(self, output="finance_plot_balance.png"):
        daily = self.daily_stats()
        daily["баланс"] = (daily["доход"] - daily["расход"]).cumsum()

        plt.figure(figsize=(10, 5))
        plt.plot(daily.index, daily["доход"], label="Доходы", color="green")
        plt.plot(daily.index, daily["расход"], label="Расходы",  color="red")
        plt.plot(daily.index, daily["баланс"], label="Баланс", color="purple")
        plt.title("Доходы и расходы по дням")
        plt.xlabel("Дата")
        plt.ylabel("Сумма")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig(output)
        plt.close()

        return output
    
    # Круговая диаграмма по категориям расходов
    def plot_pie_categories(self, output="categories_pie.png"):
        df_waste = self.data[self.data["type"] == "расход"]
        cat_sum = df_waste.groupby("category")["amount"].sum()

        plt.figure(figsize=(10, 10))
        plt.pie(cat_sum, labels=cat_sum.index, autopct="%1.1f%%", startangle=90)
        plt.title("Распределение расходов по категориям")
        plt.tight_layout()
        plt.savefig(output)
        plt.close()

        return output

    # Гистограмма расходов по компаниям
    def plot_bar_companies(self, n=10, output="companies_bar.png"):
        df_waste = self.data[self.data["type"] == "расход"]
        comp_sum = df_waste.groupby("company")["amount"].sum().sort_values(ascending=False).head(n)

        plt.figure(figsize=(12, 6))
        plt.bar(comp_sum.index, comp_sum.values)
        plt.xticks(rotation=45)
        plt.title(f"Топ-{n} компаний по расходам")
        plt.xlabel("Компания")
        plt.ylabel("Сумма расходов")
        plt.tight_layout()
        plt.savefig(output)
        plt.close()

        return output

    # 7. Рекомендация на основе данных
    def recommendation(self):
        income = self.data[self.data["type"] == "доход"]["amount"].sum()
        waste = self.data[self.data["type"] == "расход"]["amount"].sum()
        top_cat = list(self.top_categories_waste(3).keys())
        key = 1

        if waste > income:
            key = -1
            return (
                "Вы тратите больше, чем зарабатываете.\n"
                f"Самая затратная категория — {top_cat}. Попробуйте сократить расходы в этой области.", key)
        if self.avg_waste() > round(income*0.7, 2):
            key = 0
            return (
                "  Средняя трата за раз довольно высокая.\n"
                "  Попробуйте ставить лимиты на отдельные категории.", key)
        return ("Финансовое состояние стабильное. Продолжайте в том же духе!", key)

    # 8 Тотальный отчет по всем параметрам
    def full_report(self, days=30, top_comp=3):
        end = self.data["date"].max()
        start = end - pd.Timedelta(days=days)
        df = self.data[(self.data["date"] >= start)]

        income = df[df["type"] == "доход"]["amount"].sum()
        waste = df[df["type"] == "расход"]["amount"].sum()
        balance = income - waste

        waste_comp, inc_comp = self.top_companies(top_comp)

        report = (
            f"Финансовый отчёт за период {start.date()} — {end.date()}\n\n"
            f"Доходы: {income:.2f} ₽\n"
            f"Расходы: {waste:.2f} ₽\n"
            f"Баланс: {balance:.2f} ₽\n\n"
            f"Средняя трата: {self.avg_waste():.2f} ₽\n\n"
        )

        report += "Топ-3 категорий расходов:\n"
        for category, value in self.top_categories_waste().items():
            report += (f"  {category}: {value:.2f} ₽\n")
        
        report += "\nТоп-3 категорий доходов:\n"
        for category, value in self.top_categories_income().items():
            report += (f"  {category}: {value:.2f} ₽\n")

        report += "\nТоп компаний по расходам:\n"
        for comp, value in waste_comp.items():
            report += (f"  {comp}: {value:.2f} ₽\n")

        report += "\nТоп компаний по доходам:\n"
        for comp, value in inc_comp.items():
            report += (f"  {comp}: {value:.2f} ₽\n")

        report += (f"\nРекомендация: {self.recommendation()}\n")
        return report
