"""
تحلیل و مقایسه الگوریتم‌های TSP
===================================
این فایل تحلیل کامل عملکرد الگوریتم‌ها را ارائه می‌دهد.
"""


import time
import random
import math
import sys
from tsp_solver import (
    TSPGraph, brute_force, greedy_search,
    hill_climbing, simulated_annealing, genetic_algorithm
)

# ─────────────────────────────────────────────
# گزارش متنی
# ─────────────────────────────────────────────

def print_header(text, char="=", width=60):
    print(f"\n{char * width}")
    pad = (width - len(text) - 2) // 2
    print(f"{char}{' ' * pad}{text}{' ' * pad}{char}")
    print(f"{char * width}")

"""  
    این مهم‌ترین تابع گزارش‌گیری است.

    هدف:
    اجرای همه الگوریتم‌ها روی یک گراف یکسان و مقایسه نتایج آن‌ها.
"""
def compare_algorithms(graph: TSPGraph, verbose=True) -> dict:
    """اجرا و مقایسه همه الگوریتم‌ها"""
    results = {}
    n = len(graph.cities)

    algorithms = [
        ("Greedy Search", greedy_search),
        ("Hill Climbing", hill_climbing),
        ("Simulated Annealing", simulated_annealing),
        ("Genetic Algorithm", genetic_algorithm),
    ]
    if n <= 10:
        algorithms.insert(0, ("Brute Force", brute_force))


    if verbose:
        print(f"\n{'─'*60}")
        print(f"  تعداد شهرها: {n}")
        print(f"  شهرها: {', '.join(graph.cities)}")
        print(f"{'─'*60}")

    for name, fn in algorithms:
        
        result = fn(graph)
        results[name] = result
        if verbose:
            tour_str = " → ".join(result.best_tour)
            if result.best_tour:
                tour_str += f" → {result.best_tour[0]}"
            print(f"\n  [{name}]")
            print(f"    هزینه  : {result.best_cost:.4f}")
            print(f"    زمان   : {result.elapsed:.6f} ثانیه")
            print(f"    تکرار  : {result.iterations}")
            print(f"    مسیر   : {tour_str}")
            """
            بعد چاپ می‌کند:

                هزینه

                زمان اجرا

                تعداد تکرار

                مسیر

            """

    if verbose and results:
        best_name = min(results, key=lambda k: results[k].best_cost)
        best_cost = results[best_name].best_cost
        print(f"\n  🏆 بهترین: {best_name}  →  {best_cost:.4f}")

    return results


def benchmark_scalability(city_counts=(5, 8, 10, 15, 20), trials=3):
    """بنچمارک مقیاس‌پذیری الگوریتم‌ها با تعداد شهرهای مختلف"""
    print_header("بنچمارک مقیاس‌پذیری")

    algo_names = ["Greedy Search", "Hill Climbing",
                  "Simulated Annealing", "Genetic Algorithm"]

    # هدر جدول
    header = f"{'n':>4} | " + " | ".join(f"{a[:10]:>12}" for a in algo_names)
    print(f"\n  زمان اجرا (ثانیه):")
    print(f"  {header}")
    print(f"  {'─'*80}")

    data = {}
    for n in city_counts:
        "یک گراف تصادفی می‌سازد."
        row_times = []
        for algo_name in algo_names:
            algo_fn = {
                "Greedy Search":        greedy_search,
                "Hill Climbing":        hill_climbing,
                "Simulated Annealing":  simulated_annealing,
                "Genetic Algorithm":    genetic_algorithm,
            }[algo_name]

            times = []
            "برای هر الگوریتم چند بار اجرا می‌شود:"
            for seed in range(trials):
                g = TSPGraph()
                g.generate_random(n, seed=seed * 100)
                r = algo_fn(g)
                times.append(r.elapsed)
            avg_t = sum(times) / len(times)
            row_times.append(avg_t)

        data[n] = row_times
        row_str = f"  {n:>4} | " + " | ".join(f"{t:>12.6f}" for t in row_times)
        print(row_str)

    return data


def quality_analysis(n_cities=10, trials=5):
    """تحلیل کیفیت جواب‌ها"""
    print_header(f"تحلیل کیفیت جواب‌ها ({n_cities} شهر)")

    algo_fns = {
        "Greedy":     greedy_search,
        "Hill Climb": hill_climbing,
        "Sim. Anneal": simulated_annealing,
        "Genetic":    genetic_algorithm,
    }

    print(f"\n  {'الگوریتم':>14} | {'بهترین':>10} | {'بدترین':>10} | {'میانگین':>10} | {'انحراف':>10}")
    print(f"  {'─'*70}")

    for name, fn in algo_fns.items():
        costs = []
        for seed in range(trials):
            g = TSPGraph()
            g.generate_random(n_cities, seed=seed * 7 + 3)
            r = fn(g)
            costs.append(r.best_cost)

        best_c = min(costs)
        worst_c = max(costs)
        avg_c = sum(costs) / len(costs)
        std_c = math.sqrt(sum((c - avg_c)**2 for c in costs) / len(costs))

        print(f"  {name:>14} | {best_c:>10.2f} | {worst_c:>10.2f} | {avg_c:>10.2f} | {std_c:>10.2f}")


def complexity_info():
    """نمایش اطلاعات پیچیدگی"""
    print_header("پیچیدگی الگوریتم‌ها")
    info = [
        ("Brute Force",         "O(n!)",       "O(n)",      "دقیق",       "n > 12 ناممکن"),
        ("Greedy Search",       "O(n²)",       "O(n)",      "تقریبی",     "سریع اما ضعیف"),
        ("Hill Climbing",       "O(k·n²)",     "O(n)",      "تقریبی",     "بهینه محلی"),
        ("Simulated Annealing", "O(iter·n)",   "O(n)",      "تقریبی",     "پارامتر حساس"),
        ("Genetic Algorithm",   "O(g·p·n)",    "O(p·n)",    "تقریبی",     "قوی و انعطاف‌پذیر"),
    ]
    fmt = "  {:<25} {:<12} {:<10} {:<12} {}"
    print()
    print(fmt.format("الگوریتم", "زمانی", "فضایی", "نوع", "توضیح"))
    print(f"  {'─'*80}")
    for row in info:
        print(fmt.format(*row))


# ─────────────────────────────────────────────
# اجرای اصلی
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print_header("تحلیل TSP — فروشنده دوره‌گرد")

    # ─── مثال ۱: داده نمونه پروژه ───
    print_header("مثال ۱: داده نمونه پروژه", char="─")
    g1 = TSPGraph()
    g1.load_from_text("A B 10\nA C 15\nB C 20\nB D 25\nC D 30")
    compare_algorithms(g1)

    # ─── مثال ۲: شهرهای تصادفی ───
    print_header("مثال ۲: ۸ شهر تصادفی", char="─")
    g2 = TSPGraph()
    """
    seed=42

        باعث می‌شود که اعداد تصادفی همیشه یکسان باشند.

        یعنی هر بار برنامه اجرا شود، دقیقاً همان ۸ شهر تولید می‌شوند.

        این موضوع برای آزمایش و مقایسه الگوریتم‌ها اهمیت زیادی دارد.
    """
    g2.generate_random(8, seed=42)
    compare_algorithms(g2)

    # ─── پیچیدگی ───
    complexity_info()

    # ─── بنچمارک ───
    benchmark_scalability(city_counts=[5, 8, 10, 12, 15])

    # ─── کیفیت ───
    quality_analysis(n_cities=10, trials=5)

    print("\n\n" + "="*60)
    print("  گزارش کامل پروژه:")
    print("="*60)

    report = """
  ┌─────────────────────────────────────────────────────────┐
  │           گزارش تحلیل پروژه TSP                        │
  ├─────────────────────────────────────────────────────────┤
  │                                                         │
  │  1. چرا این الگوریتم‌ها؟                               │
  │  ─────────────────────────────────────────────────────  │
  │  ترکیبی از الگوریتم‌های دقیق و تقریبی انتخاب شد:     │
  │  • Brute Force: پایه مقایسه (جواب بهینه)              │
  │  • Greedy: سریع و ساده برای جواب اولیه               │
  │  • Hill Climbing: بهبود محلی با 2-opt                 │
  │  • Simulated Annealing: فرار از بهینه محلی            │
  │  • Genetic Algorithm: جستجوی جهانی                    │
  │                                                         │
  │  2. مزایا و معایب                                      │
  │  ─────────────────────────────────────────────────────  │
  │  Greedy:  ✓ سریع  ✗ کیفیت پایین                      │
  │  HC:      ✓ ساده  ✗ گیر محلی                         │
  │  SA:      ✓ کیفیت خوب  ✗ پارامترگذاری               │
  │  GA:      ✓ بهترین کیفیت  ✗ کند برای n کوچک         │
  │                                                         │
  │  3. توصیه پیاده‌سازی                                   │
  │  ─────────────────────────────────────────────────────  │
  │  n ≤ 10:  Brute Force (جواب دقیق)                    │
  │  n ≤ 20:  Simulated Annealing                        │
  │  n > 20:  Genetic Algorithm                           │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
"""
    print(report)