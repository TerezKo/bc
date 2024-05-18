import numpy as np

# Prvé vygenerovanie rozvrhu
first_schedule = {
    "Lekar": {
        "day": [1, 6, 6, 5, 6, 4, 5, 4, 3, 5, 3, 5, 1, 1, 1, 4],
        "night": [6, 6, 3, 7, 6, 6, 4, 3, 5, 1, 5, 1, 2, 3, 2, 0]
    },
    "Sestra": {
        "day": [10, 10, 8, 10, 8, 8, 5, 1, 4, 4, 2, 13, 10, 6, 7, 7, 7, 8, 7, 6, 10, 2, 0, 3, 0, 3, 4, 8, 12, 1, 3, 4],
        "night": [6, 6, 6, 7, 7, 8, 1, 3, 1, 4, 13, 4, 8, 3, 3, 6, 4, 6, 8, 8, 3, 7, 3, 3, 3, 0, 8, 0, 0, 6, 0, 1]
    },
    "PraSestra": {
        "day": [11, 12, 9, 12, 12, 4, 9, 14, 15, 9, 7, 13, 3, 10],
        "night": [7, 3, 6, 5, 3, 6, 7, 3, 2, 6, 5, 3, 3, 1]
    },
    "Osetrovatel": {
        "day": [3, 15, 13, 11, 2, 6, 6, 6, 11, 13, 11, 0, 3],
        "night": [12, 1, 2, 4, 5, 6, 10, 7, 5, 2, 2, 3, 1]
    }
}

# Druhé vygenerovanie rozvrhu
second_schedule = {
    "Lekar": {
        "day": [3, 3, 8, 8, 6, 0, 4, 4, 4, 2, 0, 0, 4, 5, 5, 4],
        "night": [11, 12, 10, 7, 10, 2, 0, 0, 1, 3, 0, 0, 1, 1, 1, 1]
    },
    "Sestra": {
        "day": [0, 30, 30, 0, 30, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 30, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 30],
        "night": [30, 0, 0, 30, 0, 30, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24, 0, 30, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    },
    "PraSestra": {
        "day": [1, 27, 24, 4, 4, 0, 2, 25, 23, 19, 4, 4, 3, 0],
        "night": [24, 0, 1, 0, 0, 5, 25, 1, 0, 0, 1, 0, 0, 3]
    },
    "Osetrovatel": {
        "day": [3, 27, 18, 1, 1, 0, 3, 23, 18, 2, 2, 2, 0],
        "night": [26, 1, 1, 1, 0, 1, 24, 2, 0, 0, 0, 0, 4]
    }
}

def calculate_statistics(schedule):
    statistics = {}
    for occupation, shifts in schedule.items():
        day_shifts = shifts["day"]
        night_shifts = shifts["night"]

        day_shifts_std = round(np.std(day_shifts), 2)
        night_shifts_std = round(np.std(night_shifts), 2)

        # Gini coefficient calculation
        def gini_coefficient(data):
            data = sorted(data)
            height, area = 0, 0
            for value in data:
                height += value
                area += height - value / 2
            fair_area = height * len(data) / 2
            return round((fair_area - area) / fair_area, 2)

        gini_day = gini_coefficient(day_shifts)
        gini_night = gini_coefficient(night_shifts)

        statistics[occupation] = {
            "day_shifts_std": day_shifts_std,
            "night_shifts_std": night_shifts_std,
            "gini_day": gini_day,
            "gini_night": gini_night
        }

    return statistics

# Funkcia na vypis statistik
def print_statistics(statistics):
    for occupation, stats in statistics.items():
        print(f"{occupation}:")
        print(f"\tStandard deviation of day shifts: {stats['day_shifts_std']}")
        print(f"\tStandard deviation of night shifts: {stats['night_shifts_std']}")
        print(f"\tGini coefficient of day shifts: {stats['gini_day']}")
        print(f"\tGini coefficient of night shifts: {stats['gini_night']}")
        print()

# Vypočítať štatistiky pre oba rozvrhy
first_schedule_stats = calculate_statistics(first_schedule)
second_schedule_stats = calculate_statistics(second_schedule)

# Vypísať štatistiky pre prvé a druhé rozvrhy
print("Statistics for the first schedule:")
print_statistics(first_schedule_stats)
print("\nStatistics for the second schedule:")
print_statistics(second_schedule_stats)
