import json
import os
import flet as ft

# ==============================================================================
# 1. ЛОГИКА РАСЧЕТА ЗАРАБОТНОЙ ПЛАТЫ
# ==============================================================================

def calculate_salary(
    hourly_rate: float,
    days_worked_normal: float,
    days_pre_holiday_reduced: float = 0,
    days_pre_holiday_reduced_evening: float = 0,
    evening_shifts: float = 0,
    hours_overtime_first_two: float = 0,
    hours_overtime_after_two: float = 0,
    hours_weekend_holiday: float = 0,
    days_non_working_holiday: float = 0,
    hours_night: float = 0,
    overtime_multiplier_first_two_hours: float = 1.5,
    overtime_multiplier_after_two_hours: float = 2.0,
    weekend_holiday_multiplier: float = 2.0,
    non_working_holiday_multiplier: float = 1.0,
    night_surcharge_percent: float = 0.20,
    evening_surcharge_percent: float = 0.20,
    hazard_surcharge_percent: float = 0.12,
    difficulty_surcharge_percent: float = 0.10,
    ndfl_rate: float = 0.13,
    bonus_percent_of_base_hours: float = 0.0
) -> dict:
    
    hours_worked_scheduled_full = days_worked_normal * 8
    hours_reduction_total = days_pre_holiday_reduced * 1.0
    hours_worked_normal = hours_worked_scheduled_full - hours_reduction_total

    hours_evening_scheduled_full = evening_shifts * 8
    hours_evening_reduction = days_pre_holiday_reduced_evening * 1.0
    hours_evening = hours_evening_scheduled_full - hours_evening_reduction

    hourly_pay_base = hourly_rate * hours_worked_normal
    evening_surcharge_amount = hourly_rate * hours_evening * evening_surcharge_percent
    hazard_surcharge_amount = hourly_rate * hours_worked_normal * hazard_surcharge_percent
    difficulty_surcharge_amount = hourly_rate * hours_worked_normal * difficulty_surcharge_percent
    night_surcharge_amount = hourly_rate * hours_night * night_surcharge_percent

    rate_with_hazard_surcharge = hourly_rate * (1 + hazard_surcharge_percent)

    overtime_payment_first_two = (hours_overtime_first_two * rate_with_hazard_surcharge * overtime_multiplier_first_two_hours)
    overtime_payment_after_two = (hours_overtime_after_two * rate_with_hazard_surcharge * overtime_multiplier_after_two_hours)
    total_overtime_payment = overtime_payment_first_two + overtime_payment_after_two

    weekend_holiday_pay = hours_weekend_holiday * rate_with_hazard_surcharge * weekend_holiday_multiplier
    non_working_holiday_pay = (days_non_working_holiday * 8) * hourly_rate * non_working_holiday_multiplier

    base_for_bonus_calculation = (hourly_pay_base + (hourly_rate * hours_evening * evening_surcharge_percent) + 
                                 (hourly_pay_base * hazard_surcharge_percent) + 
                                 overtime_payment_first_two + overtime_payment_after_two + weekend_holiday_pay)
    
    bonus_amount = base_for_bonus_calculation * bonus_percent_of_base_hours

    gross_salary = (hourly_pay_base + bonus_amount + evening_surcharge_amount + hazard_surcharge_amount + 
                   difficulty_surcharge_amount + total_overtime_payment + weekend_holiday_pay + 
                   non_working_holiday_pay + night_surcharge_amount)

    ndfl_amount = gross_salary * ndfl_rate
    net_salary = gross_salary - ndfl_amount

    breakdown = {
        "Базовые часы": hourly_pay_base,
        "Премия": bonus_amount,
        "Вечерние часы": evening_surcharge_amount,
        "Вредность": hazard_surcharge_amount,
        "Сложность": difficulty_surcharge_amount,
        "Сверхурочные": total_overtime_payment,
        "Выходные/праздники": weekend_holiday_pay,
        "Ночные часы": night_surcharge_amount,
        "Итого до вычета": gross_salary,
        "НДФЛ": -ndfl_amount,
        "ИТОГО К ВЫПЛАТЕ": net_salary
    }

    return {
        "gross_salary": round(gross_salary, 2),
        "ndfl_amount": round(ndfl_amount, 2),
        "net_salary": round(net_salary, 2),
        "breakdown": breakdown
    }

# ==============================================================================
# 2. ИНТЕРФЕЙС FLET
# ==============================================================================

def main(page: ft.Page):
    page.title = "ЗП Калькулятор"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.SYSTEM

    inputs = {
        "days_worked_normal": ft.TextField(label="Отработано смен", value="0"),
        "evening_shifts": ft.TextField(label="Вечерних смен", value="0"),
        "hours_overtime_first_two": ft.TextField(label="Переработка (первые 2ч)", value="0"),
        "hours_overtime_after_two": ft.TextField(label="Переработка (остальные)", value="0"),
    }

    net_output = ft.Text("0.00 руб.", size=30, weight=ft.FontWeight.BOLD)
    details_column = ft.Column()

    def calculate_click(e):
        try:
            params = {k: float(v.value.replace(",", ".")) for k, v in inputs.items()}
            # Добавим дефолтные коэффициенты для простоты
            params.update({"hourly_rate": 344.81, "bonus_percent_of_base_hours": 0.95})
            
            result = calculate_salary(**params)
            net_output.value = f"{result['net_salary']:,.2f} руб."
            details_column.controls.clear()
            for k, v in result["breakdown"].items():
                details_column.controls.append(ft.Text(f"{k}: {v:,.2f}"))
            page.update()
        except:
            page.snack_bar = ft.SnackBar(ft.Text("Ошибка в данных!"))
            page.snack_bar.open = True
            page.update()

    # Кастомная навигация (вкладки без использования проблемных компонентов)
    shifts_view = ft.Column([inputs["days_worked_normal"], inputs["evening_shifts"]], visible=True)
    hours_view = ft.Column([inputs["hours_overtime_first_two"], inputs["hours_overtime_after_two"]], visible=False)

    def switch_tab(e):
        shifts_view.visible = (e.control.text == "Смены")
        hours_view.visible = (e.control.text == "Часы")
        page.update()

    page.add(
        ft.Row([ft.TextButton("Смены", on_click=switch_tab), ft.TextButton("Часы", on_click=switch_tab)]),
        ft.Container(content=shifts_view, padding=10),
        ft.Container(content=hours_view, padding=10),
        ft.ElevatedButton("Рассчитать", on_click=calculate_click),
        net_output,
        details_column
    )

if __name__ == "__main__":
    ft.app(target=main)
