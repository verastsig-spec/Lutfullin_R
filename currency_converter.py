#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Currency Converter — GUI приложение для конвертации валют
Автор: [Ваше Имя Фамилия]
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

# Константы
HISTORY_FILE = "history.json"
API_BASE = "https://open.er-api.com/v6/latest/"  # Open Access endpoint (без ключа)
# Для Pro-версии: "https://v6.exchangerate-api.com/v6/YOUR-API-KEY/latest/"

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("💱 Currency Converter")
        self.root.geometry("650x500")
        self.root.resizable(False, False)
        
        # Загрузка валют и истории
        self.currencies = []
        self.history = []
        self.load_history()
        
        self.setup_ui()
        self.load_currencies()
        
    def setup_ui(self):
        """Создание интерфейса"""
        # Заголовок
        title = tk.Label(self.root, text="💱 Конвертер валют", 
                        font=("Arial", 18, "bold"), pady=10)
        title.pack()
        
        # Фрейм ввода
        input_frame = tk.Frame(self.root, padx=20, pady=10)
        input_frame.pack(fill=tk.X)
        
        # Сумма
        tk.Label(input_frame, text="Сумма:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.amount_entry = tk.Entry(input_frame, width=20, font=("Arial", 10))
        self.amount_entry.grid(row=0, column=1, padx=10, pady=5)
        self.amount_entry.insert(0, "1.0")
        
        # Валюта "из"
        tk.Label(input_frame, text="Из:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.from_currency = ttk.Combobox(input_frame, width=17, state="readonly", font=("Arial", 10))
        self.from_currency.grid(row=1, column=1, padx=10, pady=5)
        self.from_currency.set("USD")
        
        # Валюта "в"
        tk.Label(input_frame, text="В:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.to_currency = ttk.Combobox(input_frame, width=17, state="readonly", font=("Arial", 10))
        self.to_currency.grid(row=2, column=1, padx=10, pady=5)
        self.to_currency.set("EUR")
        
        # Кнопка конвертации
        convert_btn = tk.Button(input_frame, text="🔄 Конвертировать", 
                             command=self.convert_currency,
                             bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                             width=20, cursor="hand2")
        convert_btn.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Результат
        self.result_label = tk.Label(self.root, text="", font=("Arial", 12, "bold"), 
                                    fg="#2196F3", pady=5)
        self.result_label.pack()
        
        # Атрибуция API (требуется для Open Access)
        attribution = tk.Label(self.root, text='Rates by <a href="https://www.exchangerate-api.com">Exchange Rate API</a>',
                              font=("Arial", 8), fg="gray", cursor="hand2", pady=5)
        attribution.pack()
        attribution.bind("<Button-1>", lambda e: self.open_url("https://www.exchangerate-api.com"))
        
        # Фрейм истории
        history_frame = tk.Frame(self.root, padx=20, pady=10)
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(history_frame, text="📋 История конвертаций", 
                font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Таблица истории (Treeview)
        columns = ("date", "from", "to", "amount", "result", "rate")
        self.history_table = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        
        self.history_table.heading("date", text="Дата")
        self.history_table.heading("from", text="Из")
        self.history_table.heading("to", text="В")
        self.history_table.heading("amount", text="Сумма")
        self.history_table.heading("result", text="Результат")
        self.history_table.heading("rate", text="Курс")
        
        self.history_table.column("date", width=100)
        self.history_table.column("from", width=50)
        self.history_table.column("to", width=50)
        self.history_table.column("amount", width=70)
        self.history_table.column("result", width=80)
        self.history_table.column("rate", width=70)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_table.yview)
        self.history_table.configure(yscroll=scrollbar.set)
        
        self.history_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки управления историей
        btn_frame = tk.Frame(self.root, pady=5)
        btn_frame.pack()
        
        tk.Button(btn_frame, text="📥 Загрузить историю", command=self.load_history, width=18).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📤 Сохранить историю", command=self.save_history, width=18).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Очистить", command=self.clear_history, width=10).pack(side=tk.LEFT, padx=5)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_currencies(self):
        """Загрузка списка валют из API"""
        self.status_var.set("Загрузка валют...")
        self.root.update()
        
        try:
            # Используем USD как базовую валюту для получения списка
            response = requests.get(f"{API_BASE}USD", timeout=10)
            data = response.json()
            
            if data.get("result") == "success":
                # Для Open Access: ключ "rates", для Pro: "conversion_rates"
                rates = data.get("rates") or data.get("conversion_rates", {})
                self.currencies = sorted(rates.keys())
                
                self.from_currency["values"] = self.currencies
                self.to_currency["values"] = self.currencies
                
                if "USD" in self.currencies:
                    self.from_currency.set("USD")
                if "EUR" in self.currencies:
                    self.to_currency.set("EUR")
                    
                self.status_var.set(f"Загружено {len(self.currencies)} валют")
            else:
                raise ValueError("API вернул ошибку")
                
        except Exception as e:
            self.status_var.set("⚠️ Ошибка загрузки валют")
            messagebox.showerror("Ошибка", f"Не удалось загрузить валюты:\n{e}")
            # Fallback: базовый список
            self.currencies = ["USD", "EUR", "RUB", "GBP", "CNY", "JPY", "CAD", "AUD", "CHF"]
            self.from_currency["values"] = self.currencies
            self.to_currency["values"] = self.currencies
            
    def validate_input(self):
        """Проверка корректности ввода"""
        try:
            amount = float(self.amount_entry.get().replace(',', '.'))
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной")
            return amount
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", f"Некорректная сумма:\n{e}")
            return None
            
    def get_exchange_rate(self, from_curr, to_curr):
        """Получение курса валют через API"""
        try:
            response = requests.get(f"{API_BASE}{from_curr}", timeout=10)
            data = response.json()
            
            if data.get("result") == "success":
                rates = data.get("rates") or data.get("conversion_rates", {})
                if to_curr in rates:
                    return rates[to_curr]
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
            
    def convert_currency(self):
        """Основная логика конвертации"""
        # Валидация
        amount = self.validate_input()
        if amount is None:
            return
            
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        
        if not from_curr or not to_curr:
            messagebox.showwarning("Предупреждение", "Выберите валюты для конвертации")
            return
            
        self.status_var.set("Конвертация...")
        self.root.update()
        
        # Получение курса
        rate = self.get_exchange_rate(from_curr, to_curr)
        
        if rate is None:
            self.status_var.set("⚠️ Ошибка получения курса")
            messagebox.showerror("Ошибка", "Не удалось получить актуальный курс валют")
            return
            
        # Расчёт
        result = amount * rate
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Отображение результата
        self.result_label.config(
            text=f"{amount:,.2f} {from_curr} = {result:,.2f} {to_curr}\n"
                 f"Курс: 1 {from_curr} = {rate:,.4f} {to_curr}"
        )
        
        # Добавление в историю
        record = {
            "date": timestamp,
            "from": from_curr,
            "to": to_curr,
            "amount": amount,
            "result": round(result, 2),
            "rate": round(rate, 6)
        }
        self.history.insert(0, record)  # Новые записи сверху
        self.update_history_table()
        self.status_var.set("✅ Конвертация выполнена")
        
    def update_history_table(self):
        """Обновление таблицы истории"""
        # Очистка
        for item in self.history_table.get_children():
            self.history_table.delete(item)
            
        # Заполнение
        for record in self.history:
            self.history_table.insert("", tk.END, values=(
                record["date"],
                record["from"],
                record["to"],
                f"{record['amount']:.2f}",
                f"{record['result']:.2f}",
                f"{record['rate']:.6f}"
            ))
            
    def save_history(self):
        """Сохранение истории в JSON"""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            self.status_var.set("✅ История сохранена")
            messagebox.showinfo("Успех", f"История сохранена в {HISTORY_FILE}")
        except Exception as e:
            self.status_var.set("⚠️ Ошибка сохранения")
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю:\n{e}")
            
    def load_history(self):
        """Загрузка истории из JSON"""
        if not os.path.exists(HISTORY_FILE):
            self.status_var.set("ℹ️ Файл истории не найден")
            return
            
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                self.history = json.load(f)
            self.update_history_table()
            self.status_var.set(f"✅ Загружено {len(self.history)} записей")
        except Exception as e:
            self.status_var.set("⚠️ Ошибка загрузки")
            messagebox.showerror("Ошибка", f"Не удалось загрузить историю:\n{e}")
            
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю конвертаций?"):
            self.history = []
            self.update_history_table()
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            self.status_var.set("🗑️ История очищена")
            
    @staticmethod
    def open_url(url):
        """Открытие ссылки в браузере"""
        import webbrowser
        webbrowser.open(url)


def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
