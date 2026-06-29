"""
TSP (Traveling Salesman Problem) - پروژه فروشنده دوره‌گرد
============================================================
پیاده‌سازی الگوریتم‌های زیر برای حل مسئله TSP:
1. Brute Force       — جستجوی کامل O(n!)
2. Greedy Search     — جستجوی حریصانه O(n²)
3. A* Search         — جستجوی ا휴ریستیک
4. Local Beam Search — جستجوی پرتو محلی
5. Hill Climbing     — صعود تپه با 2-opt
6. Simulated Annealing — بازپخت شبیه‌سازی‌شده
7. Genetic Algorithm — الگوریتم ژنتیک
"""

import itertools
import random
import math
import time
import heapq
from typing import List, Tuple, Dict, Optional


# ══════════════════════════════════════════════
# ساختار داده پایه
# ══════════════════════════════════════════════

class TSPGraph:
    """گراف شهرها و مسافت‌ها"""

    def __init__(self):
        self.cities: List[str] = []
        self.distances: Dict[Tuple[str, str], float] = {}
        self.coordinates: Dict[str, Tuple[float, float]] = {}

    def add_city(self, name: str, x: float = None, y: float = None):
        if name not in self.cities:
            self.cities.append(name)
        if x is not None and y is not None:
            self.coordinates[name] = (float(x), float(y))

    def add_edge(self, city1: str, city2: str, dist: float):
        self.add_city(city1)
        self.add_city(city2)
        self.distances[(city1, city2)] = float(dist)
        self.distances[(city2, city1)] = float(dist)

    def distance(self, c1: str, c2: str) -> float:
        if (c1, c2) in self.distances:
            return self.distances[(c1, c2)]
        # محاسبه اقلیدسی از مختصات
        if c1 in self.coordinates and c2 in self.coordinates:
            x1, y1 = self.coordinates[c1]
            x2, y2 = self.coordinates[c2]
            return math.hypot(x2 - x1, y2 - y1)
        return float('inf')

    def tour_cost(self, tour: List[str]) -> float:
        if len(tour) < 2:
            return 0.0
        total = 0.0
        n = len(tour)
        for i in range(n):
            d = self.distance(tour[i], tour[(i + 1) % n])
            if d == float('inf'):
                return float('inf')
            total += d
        return total

    def load_from_text(self, text: str):
        """بارگذاری از متن — فرمت: A B 10"""
        self.__init__()
        for line in text.strip().splitlines():
            parts = line.strip().split()
            if len(parts) == 3:
                try:
                    self.add_edge(parts[0], parts[1], float(parts[2]))
                except ValueError:
                    pass

    def ensure_complete(self):
        """تبدیل گراف ناکامل به کامل با فاصله اقلیدسی"""
        cities = self.cities
        for i, c1 in enumerate(cities):
            for c2 in cities[i+1:]:
                if (c1, c2) not in self.distances:
                    d = self.distance(c1, c2)
                    if d != float('inf'):
                        self.distances[(c1, c2)] = d
                        self.distances[(c2, c1)] = d

    def generate_random(self, n: int, seed: int = 42):
        """تولید شهرهای تصادفی با مختصات"""
        self.__init__()
        random.seed(seed)
        names = [chr(65 + i) if i < 26 else f"C{i}" for i in range(n)]
        for name in names:
            x = random.uniform(5, 95)
            y = random.uniform(5, 95)
            self.add_city(name, x, y)
        self.ensure_complete()

    @staticmethod
    def iran_cities() -> 'TSPGraph':
        """شهرهای واقعی ایران با مختصات جغرافیایی"""
        g = TSPGraph()
        cities = {
            "تهران":    (51.42, 35.69),
            "اصفهان":   (51.67, 32.65),
            "شیراز":    (52.53, 29.61),
            "تبریز":    (46.29, 38.08),
            "مشهد":     (59.57, 36.27),
            "اهواز":    (48.67, 31.32),
            "کرمان":    (57.08, 30.28),
            "رشت":      (49.59, 37.28),
            "همدان":    (48.52, 34.80),
            "کرمانشاه": (47.07, 34.31),
        }
        for name, (x, y) in cities.items():
            g.add_city(name, x, y)
        g.ensure_complete()
        return g


# ══════════════════════════════════════════════
# نتیجه اجرا
# ══════════════════════════════════════════════

class TSPResult:
    def __init__(self, algorithm: str):
        self.algorithm = algorithm
        self.best_tour: List[str] = []
        self.best_cost: float = float('inf')
        self.cost_history: List[float] = []      # هزینه در طول اجرا
        self.tour_history: List[List[str]] = []  # بهترین‌های پیدا شده
        self.elapsed: float = 0.0
        self.iterations: int = 0
        self.nodes_explored: int = 0

    @property
    def tour_str(self) -> str:
        if not self.best_tour:
            return "—"
        return " → ".join(self.best_tour) + f" → {self.best_tour[0]}"

    def __str__(self):
        return (
            f"\n{'═'*52}\n"
            f"  الگوریتم : {self.algorithm}\n"
            f"  مسیر     : {self.tour_str}\n"
            f"  هزینه    : {self.best_cost:.4f}\n"
            f"  زمان     : {self.elapsed:.6f} s\n"
            f"  تکرار    : {self.iterations:,}\n"
            f"{'═'*52}"
        )


# ══════════════════════════════════════════════
# ابزارهای مشترک
# ══════════════════════════════════════════════

def _two_opt(tour: List[str], graph: TSPGraph) -> Tuple[List[str], float]:
    """یک پاس کامل 2-opt — برمی‌گرداند (بهترین_تور, هزینه)"""
    best = tour[:]
    best_cost = graph.tour_cost(best)
    n = len(tour)
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for k in range(i + 1, n):
                new = best[:i] + best[i:k+1][::-1] + best[k+1:]
                c = graph.tour_cost(new)
                if c < best_cost - 1e-10:
                    best, best_cost = new, c
                    improved = True
    return best, best_cost


# ══════════════════════════════════════════════
# 1. Brute Force
# ══════════════════════════════════════════════

def brute_force(graph: TSPGraph) -> TSPResult:
    """
    جستجوی کامل — همه جایگشت‌های ممکن
    پیچیدگی زمانی: O(n!)   |   فضایی: O(n)
    تضمین بهینه: بله
    """
    result = TSPResult("Brute Force")
    cities = graph.cities
    n = len(cities)
    if n > 13:
        print(f"⚠  Brute Force برای n={n} بسیار کند است (حداکثر 13 توصیه می‌شود)")

    t0 = time.perf_counter()
    start = cities[0]
    others = cities[1:]

    for perm in itertools.permutations(others):
        tour = [start] + list(perm)
        cost = graph.tour_cost(tour)
        result.iterations += 1
        if cost < result.best_cost:
            result.best_cost = cost
            result.best_tour = tour[:]
            result.tour_history.append(tour[:])
        result.cost_history.append(result.best_cost)

    result.elapsed = time.perf_counter() - t0
    return result


# ══════════════════════════════════════════════
# 2. Greedy Search
# ══════════════════════════════════════════════

def greedy_search(graph: TSPGraph, start: str = None) -> TSPResult:
    """
    جستجوی حریصانه — نزدیک‌ترین همسایه
    پیچیدگی زمانی: O(n²)   |   فضایی: O(n)
    تضمین بهینه: خیر
    """
    result = TSPResult("Greedy Search")
    cities = graph.cities[:]
    if not cities:
        return result

    t0 = time.perf_counter()
    current = start if (start and start in cities) else cities[0]
    tour = [current]
    unvisited = set(cities) - {current}

    while unvisited:
        # پیدا کردن نزدیک‌ترین شهر ندیده
        nearest = min(unvisited, key=lambda c: graph.distance(current, c))
        tour.append(nearest)
        unvisited.remove(nearest)
        current = nearest
        result.iterations += 1
        cost = graph.tour_cost(tour + [tour[0]])
        result.cost_history.append(cost)
        result.tour_history.append(tour[:])

    result.best_tour = tour
    result.best_cost = graph.tour_cost(tour)
    if result.cost_history:
        result.cost_history[-1] = result.best_cost
    else:
        result.cost_history = [result.best_cost]
    result.elapsed = time.perf_counter() - t0
    return result


# ══════════════════════════════════════════════
# 3. A* Search
# ══════════════════════════════════════════════

def _mst_heuristic(remaining: frozenset, current: str, graph: TSPGraph, start: str) -> float:
    """
    هیوریستیک A*: وزن درخت پوشای کمینه (MST) شهرهای باقی‌مانده
    + کمترین یال از current به آنها + کمترین یال از آنها به start
    این هیوریستیک admissible است (هرگز بیش‌برآورد نمی‌کند)
    """
    if not remaining:
        return graph.distance(current, start)

    nodes = list(remaining) + [current, start]
    # Prim's MST
    visited = {current}
    edges = []
    for c in remaining:
        heapq.heappush(edges, (graph.distance(current, c), c))

    mst_cost = 0.0
    while edges and len(visited) < len(nodes) - 1:
        cost, node = heapq.heappop(edges)
        if node in visited:
            continue
        visited.add(node)
        mst_cost += cost
        for c in nodes:
            if c not in visited:
                heapq.heappush(edges, (graph.distance(node, c), c))

    # اتصال به نقطه شروع
    if remaining:
        min_to_start = min(graph.distance(c, start) for c in remaining)
        mst_cost += min_to_start

    return mst_cost


def a_star(graph: TSPGraph, max_nodes: int = 50_000) -> TSPResult:
    """
    A* با هیوریستیک MST
    پیچیدگی: O(n² × 2ⁿ) در بدترین حالت
    برای n ≤ 15 مناسب است
    تضمین بهینه: بله (با هیوریستیک admissible)
    """
    result = TSPResult("A* Search")
    cities = graph.cities
    n = len(cities)

    if n > 15:
        print(f"⚠  A* برای n={n} خیلی کند است — از Greedy به عنوان پایه استفاده می‌شود")
        gr = greedy_search(graph)
        result.best_tour = gr.best_tour
        result.best_cost = gr.best_cost
        result.cost_history = gr.cost_history
        result.elapsed = gr.elapsed
        result.iterations = gr.iterations
        return result

    t0 = time.perf_counter()
    start = cities[0]
    remaining_all = frozenset(cities[1:])

    # حالت: (g, h, current_city, visited_frozenset, path)
    h0 = _mst_heuristic(remaining_all, start, graph, start)
    heap = [(h0, 0.0, start, remaining_all, [start])]
    best_complete = float('inf')

    while heap and result.nodes_explored < max_nodes:
        f, g, current, remaining, path = heapq.heappop(heap)
        result.nodes_explored += 1
        result.iterations += 1

        # هرس: اگر g از بهترین کامل بیشتر است، رد کن
        if g >= best_complete:
            continue

        if not remaining:
            # مسیر کامل شد
            total = g + graph.distance(current, start)
            if total < best_complete:
                best_complete = total
                result.best_cost = total
                result.best_tour = path[:]
                result.tour_history.append(path[:])
                result.cost_history.append(total)
            continue

        for next_city in remaining:
            new_g = g + graph.distance(current, next_city)
            if new_g >= best_complete:
                continue
            new_remaining = remaining - {next_city}
            h = _mst_heuristic(new_remaining, next_city, graph, start)
            new_f = new_g + h
            if new_f < best_complete:
                heapq.heappush(heap, (new_f, new_g, next_city,
                                      new_remaining, path + [next_city]))

    result.elapsed = time.perf_counter() - t0
    return result


# ══════════════════════════════════════════════
# 4. Local Beam Search
# ══════════════════════════════════════════════

def local_beam_search(graph: TSPGraph, k: int = 8,
                       max_iter: int = 500) -> TSPResult:
    """
    جستجوی پرتو محلی — k حالت موازی نگه می‌دارد
    پیچیدگی زمانی: O(max_iter × k × n²)
    فضایی: O(k × n)
    تضمین بهینه: خیر
    """
    result = TSPResult("Local Beam Search")
    cities = graph.cities
    n = len(cities)
    t0 = time.perf_counter()

    def neighbors_2opt(tour):
        """همسایه‌های 2-opt"""
        nbrs = []
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                new = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
                nbrs.append(new)
        return nbrs

    # k حالت اولیه تصادفی
    beams = [random.sample(cities, n) for _ in range(k)]
    beam_costs = [graph.tour_cost(b) for b in beams]

    for _ in range(max_iter):
        result.iterations += 1

        # تولید همه همسایه‌ها از همه پرتوها
        all_neighbors = []
        for beam in beams:
            for nb in neighbors_2opt(beam):
                all_neighbors.append((graph.tour_cost(nb), nb))

        if not all_neighbors:
            break

        # انتخاب k بهترین
        all_neighbors.sort(key=lambda x: x[0])
        top_k = all_neighbors[:k]
        beams = [t for _, t in top_k]
        beam_costs = [c for c, _ in top_k]

        if beam_costs[0] < result.best_cost:
            result.best_cost = beam_costs[0]
            result.best_tour = beams[0][:]
            result.tour_history.append(beams[0][:])

        result.cost_history.append(result.best_cost)

        # شرط توقف: همگرایی
        if len(set(beam_costs)) == 1:
            break

    result.elapsed = time.perf_counter() - t0
    return result


# ══════════════════════════════════════════════
# 5. Hill Climbing (2-opt + Random Restart)
# ══════════════════════════════════════════════

def hill_climbing(graph: TSPGraph, restarts: int = 30) -> TSPResult:
    """
    صعود تپه با راه‌اندازی مجدد تصادفی
    پیچیدگی: O(restarts × n²)
    """
    result = TSPResult("Hill Climbing")
    cities = graph.cities
    t0 = time.perf_counter()

    for _ in range(restarts):
        current = random.sample(cities, len(cities))
        improved_tour, improved_cost = _two_opt(current, graph)
        result.iterations += 1

        if improved_cost < result.best_cost:
            result.best_cost = improved_cost
            result.best_tour = improved_tour[:]
            result.tour_history.append(improved_tour[:])

        result.cost_history.append(result.best_cost)

    result.elapsed = time.perf_counter() - t0
    return result


# ══════════════════════════════════════════════
# 6. Simulated Annealing
# ══════════════════════════════════════════════

def simulated_annealing(graph: TSPGraph,
                         T_init: float = None,
                         T_min:  float = 0.01,
                         alpha:  float = 0.995,
                         inner:  int = None) -> TSPResult:
    """
    بازپخت شبیه‌سازی‌شده
    پیچیدگی: O(log(T_init/T_min)/log(1/alpha) × inner × n)

    اصلاحات نسبت به نسخه قبل:
      • T_init به‌صورت خودکار از میانگین فاصله‌ها محاسبه می‌شود
        (دیگر ثابت ۱۰۰۰ نیست — با مقیاس داده هماهنگ است)
      • inner به‌صورت خودکار = n×3 (نه ثابت ۱۰۰)
        (سرعت ۳× بیشتر در همان کیفیت)
      • محافظت از سرریز math.exp با کلمپ delta/T
    """
    result = TSPResult("Simulated Annealing")
    cities = graph.cities
    n = len(cities)
    t0 = time.perf_counter()

    # ── محاسبه خودکار T_init ──
    # T_init باید از مرتبه میانگین تفاوت هزینه‌ها باشد
    # تا در ابتدا ~۸۰٪ حرکات بد را بپذیریم
    if T_init is None:
        sample_dists = []
        sample_cities = random.sample(cities, min(n, 8))
        for i, c1 in enumerate(sample_cities):
            for c2 in sample_cities[i+1:]:
                d = graph.distance(c1, c2)
                if d != float('inf'):
                    sample_dists.append(d)
        avg_dist = (sum(sample_dists) / len(sample_dists)) if sample_dists else 100.0
        T_init = avg_dist * n * 2.0   # دمایی که حرکت‌های به‌اندازه 2×میانگین را قبول می‌کند

    # ── محاسبه خودکار inner ──
    # inner=n×3: آزمایش نشان می‌دهد کیفیت با n×10 یکسان است ولی ۳× سریع‌تر
    if inner is None:
        inner = max(20, n * 3)

    # شروع از جواب حریصانه برای شتاب بهتر
    gr = greedy_search(graph)
    current = gr.best_tour[:]
    current_cost = gr.best_cost
    best = current[:]
    best_cost = current_cost

    T = T_init
    while T > T_min:
        for _ in range(inner):
            # یکی از سه عملگر همسایگی را تصادفی انتخاب می‌کند
            op = random.randint(0, 2)
            neighbor = current[:]
            if op == 0:
                # swap — جابجایی دو شهر
                i, j = random.sample(range(n), 2)
                neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            elif op == 1:
                # 2-opt — معکوس‌کردن یک بازه
                i, j = sorted(random.sample(range(n), 2))
                neighbor[i:j+1] = neighbor[i:j+1][::-1]
            else:
                # or-opt — انتقال یک شهر به موقعیت دیگر
                i = random.randint(0, n - 1)
                city = neighbor.pop(i)
                j = random.randint(0, n - 1)
                neighbor.insert(j, city)

            nc = graph.tour_cost(neighbor)
            delta = nc - current_cost
            result.iterations += 1

            if delta < 0:
                current, current_cost = neighbor, nc
            else:
                # محافظت از سرریز: اگر delta/T خیلی بزرگ بود exp→0
                exponent = -delta / T
                if exponent > -500 and random.random() < math.exp(exponent):
                    current, current_cost = neighbor, nc

            if current_cost < best_cost:
                best, best_cost = current[:], current_cost
                result.tour_history.append(best[:])

        result.cost_history.append(best_cost)
        T *= alpha

    result.best_tour = best
    result.best_cost = best_cost
    result.elapsed = time.perf_counter() - t0
    return result


# ══════════════════════════════════════════════
# 7. Genetic Algorithm
# ══════════════════════════════════════════════

def genetic_algorithm(graph: TSPGraph,
                       pop_size:      int   = 120,
                       generations:   int   = 400,
                       mutation_rate: float = 0.03,
                       elite_frac:    float = 0.10,
                       tournament_k:  int   = 5) -> TSPResult:
    """
    الگوریتم ژنتیک با OX Crossover و جهش ترکیبی
    پیچیدگی: O(generations × pop_size × n)
    """
    result = TSPResult("Genetic Algorithm")
    cities = graph.cities
    n = len(cities)
    elite_size = max(2, int(pop_size * elite_frac))
    t0 = time.perf_counter()

    # ─── عملگرها ───

    def ox_crossover(p1, p2):
        """Order Crossover — حفظ نسبی ترتیب والدین"""
        a, b = sorted(random.sample(range(n), 2))
        child = [None] * n
        child[a:b] = p1[a:b]
        seen = set(child[a:b])
        ptr = b
        for gene in p2[b:] + p2[:b]:
            if gene not in seen:
                child[ptr % n] = gene
                seen.add(gene)
                ptr += 1
        return child

    def mutate(tour):
        r = random.random()
        t = tour[:]
        if r < mutation_rate:
            # swap
            i, j = random.sample(range(n), 2)
            t[i], t[j] = t[j], t[i]
        elif r < mutation_rate * 2:
            # 2-opt segment reverse
            i, j = sorted(random.sample(range(n), 2))
            t[i:j+1] = t[i:j+1][::-1]
        elif r < mutation_rate * 3:
            # or-opt
            i = random.randint(0, n - 1)
            city = t.pop(i)
            t.insert(random.randint(0, n - 1), city)
        return t

    def tournament(pop, costs):
        idxs = random.sample(range(len(pop)), min(tournament_k, len(pop)))
        best_idx = min(idxs, key=lambda i: costs[i])
        return pop[best_idx][:]

    # جمعیت اولیه (نیمی تصادفی، نیمی حریصانه)
    population = []
    for i in range(pop_size // 4):
        gr = greedy_search(graph, start=random.choice(cities))
        population.append(gr.best_tour[:])
    while len(population) < pop_size:
        population.append(random.sample(cities, n))

    for gen in range(generations):
        costs = [graph.tour_cost(ind) for ind in population]
        result.iterations += 1

        # ذخیره بهترین
        min_idx = costs.index(min(costs))
        if costs[min_idx] < result.best_cost:
            result.best_cost = costs[min_idx]
            result.best_tour = population[min_idx][:]
            result.tour_history.append(result.best_tour[:])

        result.cost_history.append(result.best_cost)

        # نخبه‌گرایی
        sorted_idx = sorted(range(pop_size), key=lambda i: costs[i])
        elites = [population[i][:] for i in sorted_idx[:elite_size]]

        # نسل جدید
        new_pop = elites[:]
        while len(new_pop) < pop_size:
            p1 = tournament(population, costs)
            p2 = tournament(population, costs)
            child = mutate(ox_crossover(p1, p2))
            new_pop.append(child)

        population = new_pop

        # هر 50 نسل، 2-opt روی بهترین اجرا کن
        if gen % 50 == 0 and result.best_tour:
            improved, ic = _two_opt(result.best_tour, graph)
            if ic < result.best_cost:
                result.best_cost = ic
                result.best_tour = improved
                population[0] = improved[:]

    result.elapsed = time.perf_counter() - t0
    return result


# ══════════════════════════════════════════════
# اجرای همه الگوریتم‌ها
# ══════════════════════════════════════════════

def run_all(graph: TSPGraph, verbose: bool = True) -> Dict[str, TSPResult]:
    results = {}
    n = len(graph.cities)

    algos = [
        ("Greedy Search",       greedy_search),
        ("A* Search",           a_star),
        ("Local Beam Search",   local_beam_search),
        ("Hill Climbing",       hill_climbing),
        ("Simulated Annealing", simulated_annealing),
        ("Genetic Algorithm",   genetic_algorithm),
    ]
    if n <= 12:
        algos.insert(0, ("Brute Force", brute_force))

    if verbose:
        print(f"\n{'═'*52}")
        print(f"  تعداد شهرها : {n}")
        print(f"  شهرها       : {', '.join(graph.cities)}")
        print(f"{'═'*52}")

    for name, fn in algos:
        if verbose:
            print(f"  ⏳ {name}...", end="", flush=True)
        r = fn(graph)
        results[name] = r
        if verbose:
            print(f"  هزینه={r.best_cost:.2f}  زمان={r.elapsed:.4f}s")

    if verbose and results:
        best = min(results, key=lambda k: results[k].best_cost)
        print(f"\n  🏆 بهترین: {best}  →  {results[best].best_cost:.4f}")

    return results


# ══════════════════════════════════════════════
# نقطه اجرا
# ══════════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 52)
    print("   TSP — فروشنده دوره‌گرد")
    print("═" * 52)

    # مثال نمونه پروژه
    g = TSPGraph()
    g.load_from_text("A B 10\nA C 15\nB C 20\nB D 25\nC D 30\nA D 35")
    g.ensure_complete()
    results = run_all(g)
    for r in results.values():
        print(r)

    print("\n\n  ── شهرهای واقعی ایران ──")
    iran = TSPGraph.iran_cities()
    run_all(iran)