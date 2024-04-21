from workalendar.europe import Slovakia
import cpmpy as cp
import datetime
import calendar
from app import *
import random

# employees = ["Nurse1", "Nurse2", "Nurse3", "Nurse4", "Nurse5", "Nurse6", "Nurse7", "Nurse8", "Nurse9", "Nurse10", "Nurse11", "Nurse12", "Nurse13"]
# max_num_shifts = [10,10,10,10,10,10,10,10,10,10,10,10,10]

penalty_weight = {
    "preference_strength": {"Slabý": 1, "Stredný": 3, "Silný": 5},  # Penalizácia podľa preferencie
    "not_accepted_preference" : 3
}


# employee_preferences = {
#     "Nurse1": {5: "N"},
#     "Nurse6": {4: "D", 9: "N"},
#     "Nurse3": {7: "D", 5: "N"}
# }


# employee_nonpreferences = {
#     "Nurse1": {
#         8: {"strength": "weak", "shift": "B"},
#         1: {"strength": "medium", "shift": "N"}
#     },
#     "Nurse2": {
#         9: {"strength": "strong", "shift": "N"},
#         4: {"strength": "strong", "shift": "D"},
#         1: {"strength": "medium", "shift": "N"}
#     }


calendar_slovakia = Slovakia()


def is_holiday_or_weekend(day):
    if calendar_slovakia.is_working_day(day):
        return "Pracovný deň"
    elif calendar_slovakia.is_holiday(day):
        return "Sviatok"
    else:
        return "Víkend"


def vypis_rozvrhu(position, employees, max_num_shifts, min_num_shifts, last_month, employee_preferences, employee_nonpreferences, count, not_workatnight, uncertified_doctors=[]):
    vysledok = ""
    print(position)
    # random.shuffle(employees)

    denna_pracovny, nocna_pracovny, denna_volno, nocna_volno = count

    aktualny_datum = datetime.now()
    prvy_den_buduceho_mes = datetime(aktualny_datum.year, aktualny_datum.month + 1, 1)
    pocet_dni = calendar.monthrange(prvy_den_buduceho_mes.year, prvy_den_buduceho_mes.month)[1]

    # Definuje zoznam dní a typov služieb pre každý deň
    days = [datetime(aktualny_datum.year, aktualny_datum.month + 1, day) for day in range(1, pocet_dni + 1)]  # 1-31 dni v mesiaci
    shift_types = ["Denná", "Nočná"]

    # Vytvorte premenné pre každého zamestnanca, deň a typ služby na celý mesiac
    # schedule[i, j, k] bude True, ak zamestnanec i pracuje v deň j so službou k
    schedule = cp.boolvar(shape=(len(employees), len(days), len(shift_types)), name="schedule")

    # Pridanie penalizácií do modelu
    penalties = []

    penalty_reasons = []

    for i in range(len(employees)):
        for j in range(len(days)):
            # Penalizácia za neakceptovanie preferencie
            if employees[i] in employee_preferences and j+1 in employee_preferences[employees[i]]:
                if employee_preferences[employees[i]][j+1] == "Obe":
                    penalties.append(min((1 - schedule[i, j, 0]),(1 - schedule[i, j, 1])) * penalty_weight["not_accepted_preference"])
                    # penalties.append((1 - schedule[i, j, 1]) * penalty_weight["not_accepted_preference"])
                    penalty_reasons.append(f"Zamestnanec {employees[i]} preferoval obe zmeny dňa {j+1}, ale nebol naplánovaný na smenu.")
                    # penalty_reasons.append(f"Zamestnanec {employees[i]} preferoval obe zmeny dňa {j+1}, ale nebol naplánovaný na nočnú smenu.")
                else:
                    preferred_shift = shift_types.index(employee_preferences[employees[i]][j+1])
                    penalties.append((1 - schedule[i, j, preferred_shift]) * penalty_weight["not_accepted_preference"])
                    penalty_reasons.append(f"Zamestnanec {employees[i]} preferoval {employee_preferences[employees[i]][j+1]} smenu dňa {j+1}, ale nebol na ňu naplánovaný.")
            if employees[i] in employee_nonpreferences and j + 1 in employee_nonpreferences[employees[i]]:
                nonpreferred_strength = employee_nonpreferences[employees[i]][j+1]["strength"]
                nonpreferred_shift = employee_nonpreferences[employees[i]][j+1].get("shift", "Obe")
                if nonpreferred_shift == "Obe":
                    penalties.append(schedule[i, j, 0] * penalty_weight["preference_strength"][nonpreferred_strength])
                    penalties.append(schedule[i, j, 1] * penalty_weight["preference_strength"][nonpreferred_strength])
                    penalty_reasons.append(f"Zamestnanec {employees[i]} nenpreferoval ani jednu smenu dňa {j+1}, ale bol naplánovaný na dennú smenu.")
                    penalty_reasons.append(f"Zamestnanec {employees[i]} nenpreferoval ani jednu smenu dňa {j+1}, ale bol naplánovaný na nočnú smenu.")
                else:
                    nonpreferred_shift_index = shift_types.index(nonpreferred_shift)
                    penalties.append(schedule[i, j, nonpreferred_shift_index] * penalty_weight["preference_strength"][nonpreferred_strength])
                    penalty_reasons.append(f"Zamestnanec {employees[i]} nenpreferoval {employee_nonpreferences[employees[i]][j+1]['shift']} smenu dňa {j+1}, ale bol na ňu naplánovaný.")

    # for i in range(len(employees)):
    #     # Počet zmien, ktorý v skutočnosti tento zamestnanec pracuje
    #     actual_shifts = sum(schedule[i, :, :])

    #     # Očakávaný počet zmien pre tohto zamestnanca
    #     expected_shifts = max_num_shifts[i]

    #     # Absolútna hodnota rozdielu medzi očakávanými a skutočnými zmenami
    #     shift_diff = abs(actual_shifts - expected_shifts)

    #     # Pridať do penalizácií
    #     penalties.append(shift_diff)

    if position == "lekar":
        for j in range(len(days)):
            for k in range(len(shift_types)):
                # je viac ako 1 neatestovany lekar
                uncertified_doctors_on_shift = sum(schedule[employees.index(doctor), j, k] for doctor in uncertified_doctors)
                penalty = cp.max([0, uncertified_doctors_on_shift - 1]) * 3
                penalties.append(penalty)
                shift_type = "Denná" if k == 0 else "Nočná"
                penalty_reasons.append(f"Na {shift_type.lower()} smenu dňa {j+1} je viacero neatestovaných lekárov.")

    model = cp.Model()

    model.minimize(sum(penalties))

    weeks = [days[n:n+7] for n in range(0, len(days), 7)]
    for i in range(len(employees)):  # Pre každého zamestnanca
        for w in range(len(weeks)):  # Pre každý týždeň
            # vytvoríme obmedzenie, že súčet zmien za týždeň musí byť <= 4
            model += sum(sum(schedule[i, days.index(day), k] for k in range(len(shift_types))) for day in weeks[w]) <= 4

    # Obmedzenie: Každý zamestnanec môže mať nanajvýše x zmien po sebe
    x = 3
    for i in range(len(employees)):
        for j in range(len(days) - x):
            model += sum(sum(schedule[i, j+k, :] for k in range(x + 1))) <= x

    # ti co pracovali poslednu sluzbu minuly mesiac nemozu pracovat prvu
    for i in last_month:
        model += ~schedule[employees.index(i), 0, 0]

    if position == "lekar":
        # Obmedzenie: Na nepracovné dni musí byť ten istý lekár na dennú a nočnú službu
        # Inak: Každý zamestnanec môže pracovať iba v jednom type služby v daný deň
        for i in range(len(employees)):
            for j in range(len(days)):
                if is_holiday_or_weekend(days[j]) != "Pracovný deň":
                    model += schedule[i, j, 0] == schedule[i, j, 1]
                else:
                    model += sum(schedule[i, j, :]) <= 1
    else:
        # Obmedzenie: Každý zamestnanec môže pracovať iba v jednom type služby v daný deň
        for i in range(len(employees)):
            for j in range(len(days)):
                model += sum(schedule[i, j, :]) <= 1

    # Obmedzenie: Jeden zamestnanec nemôže robiť v jeden deň nočnú a na ďalší deň dennú službu
    for i in range(len(employees)):
        for j in range(len(days) - 1):  # Posledný deň nemá "druhý deň"
            model += ~((schedule[i, j, 1] == 1) & (schedule[i, j + 1, 0] == 1))

    # Obmedzenie: Zamestnanci v poli not_workatnight nemôžu mať nočnú službu
    for employee in not_workatnight:
        for j in range(len(days)):
            model += ~schedule[employees.index(employee), j, 1]

    # Obmedzenie: Musí byť istý počet zamestnancov na dennú a nočnú a tiež podľa pracovného dňa alebo iného
    for j in range(len(days)):
        if is_holiday_or_weekend(days[j]) == "Pracovný deň":
            model += sum(schedule[:, j, 0]) == denna_pracovny
            model += sum(schedule[:, j, 1]) == nocna_pracovny
        else:
            model += sum(schedule[:, j, 0]) == denna_volno
            model += sum(schedule[:, j, 1]) == nocna_volno


    # Obmedzenie: Každý zamestnanec má stanovený maximálny počet hodín, ktoré môže za mesiac odpracovať
    for i in range(len(employees)):
        model += sum(schedule[i, :, :]) <= max_num_shifts[i]

    # Obmedzenie: Každý zamestnanec má stanovený minimálny počet hodín, ktoré má za mesiac odpracovať
    for employee in not_workatnight:
        emp = employees.index(employee)

    for i in range(len(employees)):
        model += (sum(schedule[i, :, 0]) + sum(schedule[i, :, 1])) >= min_num_shifts[i]

    # Riešenie modelu
    solver = model.solve()

    # Výpis riešenia ako HTML tabuľka
    vysledok_tabulka = "<table id='Shifts' border='1' cellpadding='5'>"
    vysledok_tabulka += "<tr><th>Dátum</th><th>Denná služba</th><th>Nočná služba</th></tr>"

    # Výpis riešenia ako čistý text
    vysledok_text = ""

    for j in range(len(days)):
        day_shift_nurses = [employees[i] for i in range(len(employees)) if schedule[i, j, 0].value() == 1]
        night_shift_nurses = [employees[i] for i in range(len(employees)) if schedule[i, j, 1].value() == 1]

        vysledok_tabulka += f"<tr><td>{days[j].strftime('%d.%m.%Y')}</td><td>{', '.join(day_shift_nurses)}</td><td>{', '.join(night_shift_nurses)}</td></tr>"

        vysledok_text += f"Deň {days[j].strftime('%d.%m.%Y')}:\n"
        vysledok_text += f"  Denná služba: {', '.join(day_shift_nurses)}\n"
        vysledok_text += f"  Nočná služba: {', '.join(night_shift_nurses)}\n\n"

    vysledok_tabulka += "</table>"

    # print("Výsledok ako HTML tabuľka:")
    # print(vysledok_tabulka)

    # print("\nVýsledok ako čistý text:")
    # print(vysledok_text)

    # print(vysledok)

    # for penalty, reason in zip(penalties, penalty_reasons):
    #     if penalty.value() > 0:
    #         print(f"Sankcia: {penalty.value()}, Dôvod: {reason}")

    tot_penalty = sum(penalty.value() for penalty in penalties)
    print(tot_penalty)

    # print(employees)
    total_shifts_per_employee = [sum(schedule[i, :, :].value()) for i in range(len(employees))]
    for employee, total_shifts in zip(employees, total_shifts_per_employee):
        print(f"{employee} má celkovo {total_shifts} zmien.")

    return vysledok_tabulka

