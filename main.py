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
    if any(arg < 0 for arg in [
        hourly_rate, days_worked_normal, days_pre_holiday_reduced, days_pre_holiday_reduced_evening, evening_shifts, hours_overtime_first_two, hours_overtime_after_two,
        hours_weekend_holiday, days_non_working_holiday,
        hours_night, overtime_multiplier_first_two_hours, overtime_multiplier_after_two_hours,
        weekend_holiday_multiplier, non_working_holiday_multiplier,
        night_surcharge_percent, evening_surcharge_percent, hazard_surcharge_percent,
        difficulty_surcharge_percent,
        ndfl_rate, bonus_percent_of_base_hours
    ]):
        raise ValueError("Все входные параметры должны быть неотрицательными.")

    hours_worked_scheduled_full = days_worked_normal * 8
    hours_reduction_total = days_pre_holiday_reduced * 1.0
    hours_worked_normal = hours_worked_scheduled_full - hours_reduction_total

    if hours_worked_normal < 0:
        raise ValueError("Общее количество рабочих часов не может быть отрицательным после учета сокращенных дней.")

    hours_evening_scheduled_full = evening_shifts * 8
    hours_evening_reduction = days_pre_holiday_reduced_evening * 1.0
    hours_evening = hours_evening_scheduled_full - hours_evening_reduction

    if hours_evening < 0:
        raise ValueError("Количество вечерних часов не может быть отрицательным после учета сокращения.")
    if days_pre_holiday_reduced_evening > days_pre_holiday_reduced:
        raise ValueError("Количество сокращенных вечерних дней не может превышать общее количество сокращенных дней.")
    if days_pre_holiday_reduced_evening > evening_shifts:
        raise ValueError("Количество сокращенных вечерних дней не может превышать общее количество вечерних смен.")

    hourly_pay_base = hourly_rate * hours_worked_normal
    evening_surcharge_amount = hourly_rate * hours_evening * evening_surcharge_percent
    hazard_surcharge_amount = hourly_rate * hours_worked_normal * hazard_surcharge_percent
    difficulty_surcharge_amount = hourly_rate * hours_worked_normal * difficulty_surcharge_percent
    night_surcharge_amount = hourly_rate * hours_night * night_surcharge_percent

    rate_with_hazard_surcharge = hourly_rate * (1 + hazard_surcharge_percent)

    overtime_payment_first_two = 0
    overtime_payment_after_two = 0
    total_overtime_surcharge = 0

    if hours_overtime_first_two > 0:
        overtime_base_pay_first_two = hours_overtime_first_two * rate_with_hazard_surcharge
        overtime_payment_first_two = overtime_base_pay_first_two * overtime_multiplier_first_two_hours
        total_overtime_surcharge += overtime_base_pay_first_two * (overtime_multiplier_first_two_hours - 1)

    if hours_overtime_after_two > 0:
        overtime_base_pay_after_two = hours_overtime_after_two * rate_with_hazard_surcharge
        overtime_payment_after_two = overtime_base_pay_after_two * overtime_multiplier_after_two_hours
        total_overtime_surcharge += overtime_base_pay_after_two * (overtime_multiplier_after_two_hours - 1)

    total_overtime_payment = overtime_payment_first_two + overtime_payment_after_two

    weekend_holiday_pay = 0
    if hours_weekend_holiday > 0:
        weekend_holiday_pay = hours_weekend_holiday * rate_with_hazard_surcharge * weekend_holiday_multiplier

    hours_non_working_holiday = days_non_working_holiday * 8
    non_working_holiday_pay = 0
    if hours_non_working_holiday > 0:
        non_working_holiday_pay = hours_non_working_holiday * hourly_rate * non_working_holiday_multiplier

    base_for_bonus_calculation = (hourly_rate * hours_worked_normal) + \
                                 (hourly_rate * hours_evening * evening_surcharge_percent) + \
                                 (hourly_rate * hours_worked_normal * hazard_surcharge_percent) + \
                                 (hourly_rate * hours_overtime_first_two * (1 + hazard_surcharge_percent)) + \
                                 (hourly_rate * hours_overtime_after_two * (1 + hazard_surcharge_percent)) + \
                                 (hourly_rate * hours_weekend_holiday * (1 + hazard_surcharge_percent))

    bonus_amount = 0
    if bonus_percent_of_base_hours > 0 and base_for_bonus_calculation > 0:
        bonus_amount = base_for_bonus_calculation * bonus_percent_of_base_hours

    gross_salary = hourly_pay_base + \
                   bonus_amount + \
                   evening_surcharge_amount + \
                   hazard_surcharge_amount + \
                   difficulty_surcharge_amount + \
                   total_overtime_payment + \
                   weekend_holiday_pay + \
                   non_working_holiday_pay + \
                   night_surcharge_amount

    ndfl_amount = gross_salary * ndfl_rate
    net_salary = gross_salary - ndfl_amount

    breakdown = {}
    if hourly_pay_base > 0:
        breakdown[f"Базовые часы ({hours_worked_normal:.1f} ч)"] = hourly_pay_base
    if hours_reduction_total > 0:
        breakdown[f"Сокращение часов (-{hours_reduction_total:.1f} ч)"] = 0.00
    if bonus_amount > 0:
        breakdown["Премия"] = bonus_amount
    if hours_evening_scheduled_full > 0:
        breakdown[f"Вечерние часы ({hours_evening:.1f} ч)"] = evening_surcharge_amount
    if hazard_surcharge_amount > 0:
        breakdown["Доплата за вредность"] = hazard_surcharge_amount
    if difficulty_surcharge_amount > 0:
        breakdown["Доплата за сложность"] = difficulty_surcharge_amount
    if (hours_overtime_first_two + hours_overtime_after_two) > 0:
        breakdown["Сверхурочные"] = total_overtime_payment
    if hours_weekend_holiday > 0:
        breakdown["Выходные/праздники (часы)"] = weekend_holiday_pay
    if days_non_working_holiday > 0:
        breakdown["Праздничные дни"] = non_working_holiday_pay
    if hours_night > 0:
        breakdown["Ночные часы"] = night_surcharge_amount

    breakdown["**Сумма до вычета (гросс)**"] = gross_salary
    breakdown[f"**НДФЛ ({ndfl_rate*100:.0f}%)**"] = -ndfl_amount
    breakdown["**Итого к выплате (нетто)**"] = net_salary

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
    page.title = "Калькулятор зарплаты"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 15

    settings_file = "app_settings.json"
    last_input_file = "last_input.json"

    default_coefficients = {
        "hourly_rate": 344.81,
        "overtime_multiplier_first_two_hours": 1.5,
        "overtime_multiplier_after_two_hours": 2.0,
        "weekend_holiday_multiplier": 2.0,
        "non_working_holiday_multiplier": 1.0,
        "night_surcharge_percent": 0.20,
        "evening_surcharge_percent": 0.20,
        "hazard_surcharge_percent": 0.12,
        "difficulty_surcharge_percent": 0.10,
        "ndfl_rate": 0.13,
        "bonus_percent_of_base_hours": 0.95,
    }
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                coefficients = json.load(f).get("coefficients", default_coefficients)
        except:
            coefficients = default_coefficients
    else:
        coefficients = default_coefficients

    inputs = {}
    
    fields_config = [
        ("days_worked_normal", "Всего отработано смен", "0"),
        ("evening_shifts", "Количество вечерних смен", "0"),
        ("days_pre_holiday_reduced", "Сокращенные дни (общее)", "0"),
        ("days_pre_holiday_reduced_evening", "Сокращенные вечерние смены", "0"),
        ("hours_overtime_first_two", "Переработка (первые 2ч)", "0"),
        ("hours_overtime_after_two", "Переработка (последующие)", "0"),
        ("hours_weekend_holiday", "Часы в выходные/праздники", "0"),
        ("days_non_working_holiday", "Нерабочие праздничные дни", "0"),
        ("hours_night", "Ночные часы", "0"),
    ]

    saved_inputs = {}
    if os.path.exists(last_input_file):
        try:
            with open(last_input_file, "r", encoding="utf-8") as f:
                saved_inputs = json.load(f)
        except:
            pass

    for key, label, default_val in fields_config:
        val = saved_inputs.get(key, default_val)
        inputs[key] = ft.TextField(
            label=label,
            value=str(val),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=18,
            height=55,
            border_radius=10,
        )

    net_output = ft.Text("0.00 руб.", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    details_column = ft.Column()

    def save_state():
        data = {k: v.value for k, v in inputs.items()}
        try:
            with open(last_input_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except:
            pass

    def calculate_click(e):
        try:
            params = {}
            for k, field in inputs.items():
                val_str = field.value.strip().replace(",", ".")
                params[k] = float(val_str) if val_str else 0.0
            
            params.update(coefficients)
            result = calculate_salary(**params)

            net_output.value = f"{result['net_salary']:,.2f} руб."
            details_column.controls.clear()

            for name, val in result["breakdown"].items():
                details_column.controls.append(
                    ft.Row(
                        [
                            ft.Text(name, size=14, expand=True),
                            ft.Text(f"{val:,.2f}", size=14, weight=ft.FontWeight.BOLD)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                )
            save_state()
            page.update()
        except ValueError as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка в данных: {err}"), bgcolor=ft.Colors.RED_400)
            page.snack_bar.open = True
            page.update()

    def clear_click(e):
        for field in inputs.values():
            field.value = "0"
        net_output.value = "0.00 руб."
        details_column.controls.clear()
        save_state()
        page.update()

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Смены",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        inputs["days_worked_normal"],
                        inputs["evening_shifts"],
                        inputs["days_pre_holiday_reduced"],
                        inputs["days_pre_holiday_reduced_evening"],
                    ], spacing=15)
                ),
            ),
            ft.Tab(
                text="Часы / Переработки",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        inputs["hours_overtime_first_two"],
                        inputs["hours_overtime_after_two"],
                        inputs["hours_weekend_holiday"],
                        inputs["days_non_working_holiday"],
                        inputs["hours_night"],
                    ], spacing=15)
                ),
            ),
        ],
        expand=1
    )

    page.add(
        ft.Text("Калькулятор ЗП", size=24, weight=ft.FontWeight.BOLD),
        ft.Container(content=tabs, height=380),
        ft.Row([
            ft.ElevatedButton("Рассчитать", on_click=calculate_click, expand=True, height=50, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
            ft.OutlinedButton("Очистить", on_click=clear_click, height=50),
        ], spacing=10),
        ft.Divider(),
        ft.Text("Результат:", size=16, weight=ft.FontWeight.BOLD),
        net_output,
        ft.Divider(),
        ft.Text("Детализация:", size=16, weight=ft.FontWeight.BOLD),
        details_column
    )

if __name__ == "__main__":
    ft.app(main)
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
    if any(arg < 0 for arg in [
        hourly_rate, days_worked_normal, days_pre_holiday_reduced, days_pre_holiday_reduced_evening, evening_shifts, hours_overtime_first_two, hours_overtime_after_two,
        hours_weekend_holiday, days_non_working_holiday,
        hours_night, overtime_multiplier_first_two_hours, overtime_multiplier_after_two_hours,
        weekend_holiday_multiplier, non_working_holiday_multiplier,
        night_surcharge_percent, evening_surcharge_percent, hazard_surcharge_percent,
        difficulty_surcharge_percent,
        ndfl_rate, bonus_percent_of_base_hours
    ]):
        raise ValueError("Все входные параметры должны быть неотрицательными.")

    hours_worked_scheduled_full = days_worked_normal * 8
    hours_reduction_total = days_pre_holiday_reduced * 1.0
    hours_worked_normal = hours_worked_scheduled_full - hours_reduction_total

    if hours_worked_normal < 0:
        raise ValueError("Общее количество рабочих часов не может быть отрицательным после учета сокращенных дней.")

    hours_evening_scheduled_full = evening_shifts * 8
    hours_evening_reduction = days_pre_holiday_reduced_evening * 1.0
    hours_evening = hours_evening_scheduled_full - hours_evening_reduction

    if hours_evening < 0:
        raise ValueError("Количество вечерних часов не может быть отрицательным после учета сокращения.")
    if days_pre_holiday_reduced_evening > days_pre_holiday_reduced:
        raise ValueError("Количество сокращенных вечерних дней не может превышать общее количество сокращенных дней.")
    if days_pre_holiday_reduced_evening > evening_shifts:
        raise ValueError("Количество сокращенных вечерних дней не может превышать общее количество вечерних смен.")

    hourly_pay_base = hourly_rate * hours_worked_normal
    evening_surcharge_amount = hourly_rate * hours_evening * evening_surcharge_percent
    hazard_surcharge_amount = hourly_rate * hours_worked_normal * hazard_surcharge_percent
    difficulty_surcharge_amount = hourly_rate * hours_worked_normal * difficulty_surcharge_percent
    night_surcharge_amount = hourly_rate * hours_night * night_surcharge_percent

    rate_with_hazard_surcharge = hourly_rate * (1 + hazard_surcharge_percent)

    overtime_payment_first_two = 0
    overtime_payment_after_two = 0
    total_overtime_surcharge = 0

    if hours_overtime_first_two > 0:
        overtime_base_pay_first_two = hours_overtime_first_two * rate_with_hazard_surcharge
        overtime_payment_first_two = overtime_base_pay_first_two * overtime_multiplier_first_two_hours
        total_overtime_surcharge += overtime_base_pay_first_two * (overtime_multiplier_first_two_hours - 1)

    if hours_overtime_after_two > 0:
        overtime_base_pay_after_two = hours_overtime_after_two * rate_with_hazard_surcharge
        overtime_payment_after_two = overtime_base_pay_after_two * overtime_multiplier_after_two_hours
        total_overtime_surcharge += overtime_base_pay_after_two * (overtime_multiplier_after_two_hours - 1)

    total_overtime_payment = overtime_payment_first_two + overtime_payment_after_two

    weekend_holiday_pay = 0
    if hours_weekend_holiday > 0:
        weekend_holiday_pay = hours_weekend_holiday * rate_with_hazard_surcharge * weekend_holiday_multiplier

    hours_non_working_holiday = days_non_working_holiday * 8
    non_working_holiday_pay = 0
    if hours_non_working_holiday > 0:
        non_working_holiday_pay = hours_non_working_holiday * hourly_rate * non_working_holiday_multiplier

    base_for_bonus_calculation = (hourly_rate * hours_worked_normal) + \
                                 (hourly_rate * hours_evening * evening_surcharge_percent) + \
                                 (hourly_rate * hours_worked_normal * hazard_surcharge_percent) + \
                                 (hourly_rate * hours_overtime_first_two * (1 + hazard_surcharge_percent)) + \
                                 (hourly_rate * hours_overtime_after_two * (1 + hazard_surcharge_percent)) + \
                                 (hourly_rate * hours_weekend_holiday * (1 + hazard_surcharge_percent))

    bonus_amount = 0
    if bonus_percent_of_base_hours > 0 and base_for_bonus_calculation > 0:
        bonus_amount = base_for_bonus_calculation * bonus_percent_of_base_hours

    gross_salary = hourly_pay_base + \
                   bonus_amount + \
                   evening_surcharge_amount + \
                   hazard_surcharge_amount + \
                   difficulty_surcharge_amount + \
                   total_overtime_payment + \
                   weekend_holiday_pay + \
                   non_working_holiday_pay + \
                   night_surcharge_amount

    ndfl_amount = gross_salary * ndfl_rate
    net_salary = gross_salary - ndfl_amount

    breakdown = {}
    if hourly_pay_base > 0:
        breakdown[f"Базовые часы ({hours_worked_normal:.1f} ч)"] = hourly_pay_base
    if hours_reduction_total > 0:
        breakdown[f"Сокращение часов (-{hours_reduction_total:.1f} ч)"] = 0.00
    if bonus_amount > 0:
        breakdown["Премия"] = bonus_amount
    if hours_evening_scheduled_full > 0:
        breakdown[f"Вечерние часы ({hours_evening:.1f} ч)"] = evening_surcharge_amount
    if hazard_surcharge_amount > 0:
        breakdown["Доплата за вредность"] = hazard_surcharge_amount
    if difficulty_surcharge_amount > 0:
        breakdown["Доплата за сложность"] = difficulty_surcharge_amount
    if (hours_overtime_first_two + hours_overtime_after_two) > 0:
        breakdown["Сверхурочные"] = total_overtime_payment
    if hours_weekend_holiday > 0:
        breakdown["Выходные/праздники (часы)"] = weekend_holiday_pay
    if days_non_working_holiday > 0:
        breakdown["Праздничные дни"] = non_working_holiday_pay
    if hours_night > 0:
        breakdown["Ночные часы"] = night_surcharge_amount

    breakdown["**Сумма до вычета (гросс)**"] = gross_salary
    breakdown[f"**НДФЛ ({ndfl_rate*100:.0f}%)**"] = -ndfl_amount
    breakdown["**Итого к выплате (нетто)**"] = net_salary

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
    page.title = "Калькулятор зарплаты"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 15

    settings_file = "app_settings.json"
    last_input_file = "last_input.json"

    default_coefficients = {
        "hourly_rate": 344.81,
        "overtime_multiplier_first_two_hours": 1.5,
        "overtime_multiplier_after_two_hours": 2.0,
        "weekend_holiday_multiplier": 2.0,
        "non_working_holiday_multiplier": 1.0,
        "night_surcharge_percent": 0.20,
        "evening_surcharge_percent": 0.20,
        "hazard_surcharge_percent": 0.12,
        "difficulty_surcharge_percent": 0.10,
        "ndfl_rate": 0.13,
        "bonus_percent_of_base_hours": 0.95,
    }
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                coefficients = json.load(f).get("coefficients", default_coefficients)
        except:
            coefficients = default_coefficients
    else:
        coefficients = default_coefficients

    inputs = {}
    
    fields_config = [
        ("days_worked_normal", "Всего отработано смен", "0"),
        ("evening_shifts", "Количество вечерних смен", "0"),
        ("days_pre_holiday_reduced", "Сокращенные дни (общее)", "0"),
        ("days_pre_holiday_reduced_evening", "Сокращенные вечерние смены", "0"),
        ("hours_overtime_first_two", "Переработка (первые 2ч)", "0"),
        ("hours_overtime_after_two", "Переработка (последующие)", "0"),
        ("hours_weekend_holiday", "Часы в выходные/праздники", "0"),
        ("days_non_working_holiday", "Нерабочие праздничные дни", "0"),
        ("hours_night", "Ночные часы", "0"),
    ]

    saved_inputs = {}
    if os.path.exists(last_input_file):
        try:
            with open(last_input_file, "r", encoding="utf-8") as f:
                saved_inputs = json.load(f)
        except:
            pass

    for key, label, default_val in fields_config:
        val = saved_inputs.get(key, default_val)
        inputs[key] = ft.TextField(
            label=label,
            value=str(val),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=18,
            height=55,
            border_radius=10,
        )

    net_output = ft.Text("0.00 руб.", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    details_column = ft.Column()

    def save_state():
        data = {k: v.value for k, v in inputs.items()}
        try:
            with open(last_input_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except:
            pass

    def calculate_click(e):
        try:
            params = {}
            for k, field in inputs.items():
                val_str = field.value.strip().replace(",", ".")
                params[k] = float(val_str) if val_str else 0.0
            
            params.update(coefficients)
            result = calculate_salary(**params)

            net_output.value = f"{result['net_salary']:,.2f} руб."
            details_column.controls.clear()

            for name, val in result["breakdown"].items():
                details_column.controls.append(
                    ft.Row(
                        [
                            ft.Text(name, size=14, expand=True),
                            ft.Text(f"{val:,.2f}", size=14, weight=ft.FontWeight.BOLD)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                )
            save_state()
            page.update()
        except ValueError as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка в данных: {err}"), bgcolor=ft.Colors.RED_400)
            page.snack_bar.open = True
            page.update()

    def clear_click(e):
        for field in inputs.values():
            field.value = "0"
        net_output.value = "0.00 руб."
        details_column.controls.clear()
        save_state()
        page.update()

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Смены",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        inputs["days_worked_normal"],
                        inputs["evening_shifts"],
                        inputs["days_pre_holiday_reduced"],
                        inputs["days_pre_holiday_reduced_evening"],
                    ], spacing=15)
                ),
            ),
            ft.Tab(
                text="Часы / Переработки",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        inputs["hours_overtime_first_two"],
                        inputs["hours_overtime_after_two"],
                        inputs["hours_weekend_holiday"],
                        inputs["days_non_working_holiday"],
                        inputs["hours_night"],
                    ], spacing=15)
                ),
            ),
        ],
        expand=1
    )

    page.add(
        ft.Text("Калькулятор ЗП", size=24, weight=ft.FontWeight.BOLD),
        ft.Container(content=tabs, height=380),
        ft.Row([
            ft.ElevatedButton("Рассчитать", on_click=calculate_click, expand=True, height=50, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
            ft.OutlinedButton("Очистить", on_click=clear_click, height=50),
        ], spacing=10),
        ft.Divider(),
        ft.Text("Результат:", size=16, weight=ft.FontWeight.BOLD),
        net_output,
        ft.Divider(),
        ft.Text("Детализация:", size=16, weight=ft.FontWeight.BOLD),
        details_column
    )

if __name__ == "__main__":
    ft.app(main)


