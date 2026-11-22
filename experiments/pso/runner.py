#!/usr/bin/env python3
"""PSO runner cho bài toán CPU/RAM (Chương 3).

6 bước: khởi tạo -> áp cấu hình + đo -> tính F -> cập nhật pBest/gBest ->
cập nhật vận tốc/vị trí -> lặp tới điều kiện dừng.

Chạy trên host VPS (cần python3 + pyyaml + docker), stack `rental-exp` đang chạy:
    python3 experiments/pso/runner.py --dry-run          # kiểm tra logic, không đụng Docker
    python3 experiments/pso/runner.py --max-evals 4      # smoke thật, 4 evaluation
    python3 experiments/pso/runner.py                    # chạy đủ theo config
"""

import argparse
import copy
import glob
import hashlib
import json
import math
import os
import random
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(ROOT, "experiments", "config.yaml")
RESULTS_DIR = os.path.join(ROOT, "experiments", "results", "raw")


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def config_hash(path=CONFIG_PATH):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def git_commit():
    try:
        return sh(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"]).stdout.strip()
    except Exception:
        return None


def host_load1():
    try:
        with open("/proc/loadavg") as f:
            return float(f.read().split()[0])
    except Exception:
        return None


# ---------- Docker / cgroup ----------

def container_name(logical):
    return f"rental-exp-{logical}"


def docker_inspect(name, fmt):
    return sh(["docker", "inspect", "-f", fmt, name]).stdout.strip()


_CGROUP_CACHE = {}


def cgroup_dir(name):
    # Container có thể nằm trong system.slice (không cô lập) hoặc
    # rental.slice/rental-exp.slice (EXP_ISOLATE=1) -> tìm theo container id.
    cid = docker_inspect(name, "{{.Id}}")
    if cid not in _CGROUP_CACHE:
        hits = glob.glob(f"/sys/fs/cgroup/**/docker-{cid}.scope", recursive=True)
        _CGROUP_CACHE[cid] = hits[0] if hits else \
            f"/sys/fs/cgroup/system.slice/docker-{cid}.scope"
    return _CGROUP_CACHE[cid]


def read_kv(path):
    out = {}
    try:
        with open(path) as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2:
                    out[parts[0]] = int(parts[1])
    except OSError:
        pass
    return out


def read_int(path, default=0):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return default


def wait_health(url, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        # OOM/restart loop: dừng sớm thay vì chờ hết timeout.
        for name in ("rental-exp-backend",):
            try:
                if docker_inspect(name, "{{.State.OOMKilled}}") == "true":
                    return False
            except Exception:
                pass
        time.sleep(2)
    return False


class Sampler(threading.Thread):
    """Đọc cgroup mỗi 1s trong lúc chạy tải."""

    def __init__(self, names, interval=1.0):
        super().__init__(daemon=True)
        self.names = names
        self.interval = interval
        self.stop_flag = False
        self.samples = []

    def run(self):
        cgs = {n: cgroup_dir(container_name(n)) for n in self.names}
        while not self.stop_flag:
            snap = {"t": time.time()}
            for n, cg in cgs.items():
                snap[n] = {
                    "mem": read_int(f"{cg}/memory.current"),
                    "cpu": read_kv(f"{cg}/cpu.stat"),
                }
            self.samples.append(snap)
            time.sleep(self.interval)


def sampler_metrics(samples, names):
    if len(samples) < 2:
        return {"cpu_used": {}, "cpu_peak": {}, "mem_peak_mb": {}, "throttled_ratio": {}}
    first, last = samples[0], samples[-1]
    dt = max(last["t"] - first["t"], 1e-9)
    cpu_used, cpu_peak, mem_peak, throttled = {}, {}, {}, {}
    for n in names:
        du = last[n]["cpu"].get("usage_usec", 0) - first[n]["cpu"].get("usage_usec", 0)
        cpu_used[n] = round(du / 1e6 / dt, 3)
        rates = []
        for a, b in zip(samples, samples[1:]):
            d = b["t"] - a["t"]
            if d > 0:
                rates.append((b[n]["cpu"].get("usage_usec", 0)
                              - a[n]["cpu"].get("usage_usec", 0)) / 1e6 / d)
        cpu_peak[n] = round(max(rates), 3) if rates else 0.0
        mem_peak[n] = round(max(s[n]["mem"] for s in samples) / (1024 * 1024), 1)
        tu = last[n]["cpu"].get("throttled_usec", 0) - first[n]["cpu"].get("throttled_usec", 0)
        throttled[n] = round(tu / du, 4) if du > 0 else 0.0
    return {"cpu_used": cpu_used, "cpu_peak": cpu_peak,
            "mem_peak_mb": mem_peak, "throttled_ratio": throttled}


def oom_snapshot(names):
    snap = {}
    for n in names:
        name = container_name(n)
        ev = read_kv(f"{cgroup_dir(name)}/memory.events")
        snap[n] = {
            "oom": ev.get("oom", 0),
            "oom_kill": ev.get("oom_kill", 0),
            "restarts": int(docker_inspect(name, "{{.RestartCount}}")),
        }
    return snap


def oom_delta(before, after, names):
    out = {"oom": 0, "oom_kill": 0, "restarts": 0}
    for n in names:
        out["oom"] += max(0, after[n]["oom"] - before[n]["oom"])
        out["oom_kill"] += max(0, after[n]["oom_kill"] - before[n]["oom_kill"])
        out["restarts"] += max(0, after[n]["restarts"] - before[n]["restarts"])
    return out


# ---------- Miền nghiệm ----------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def snap(v, lo, hi, step, floor=False):
    v = clamp(v, lo, hi)
    k = math.floor((v - lo) / step) if floor else round((v - lo) / step)
    return round(clamp(lo + k * step, lo, hi), 6)


def repair(vec, cfg):
    cpu = cfg["search_space"]["cpus"]
    mem = cfg["search_space"]["mem_mb"]
    cpu_avail = cfg["resources"]["cpu_avail"]
    ram_avail = cfg["resources"]["ram_avail_mb"]

    for n in vec:
        vec[n][0] = clamp(vec[n][0], cpu["min"], cpu["max"])
        vec[n][1] = clamp(vec[n][1], mem["min"], mem["max"])

    sum_cpu = sum(v[0] for v in vec.values())
    sum_mem = sum(v[1] for v in vec.values())
    scale = min(1.0, cpu_avail / sum_cpu if sum_cpu else 1.0,
                ram_avail / sum_mem if sum_mem else 1.0)
    if scale < 1.0:
        for n in vec:
            vec[n][0] = max(cpu["min"], vec[n][0] * scale)
            vec[n][1] = max(mem["min"], vec[n][1] * scale)

    for n in vec:
        vec[n][0] = snap(vec[n][0], cpu["min"], cpu["max"], cpu["step"], floor=True)
        vec[n][1] = snap(vec[n][1], mem["min"], mem["max"], mem["step"], floor=True)

    while sum(v[0] for v in vec.values()) > cpu_avail + 1e-9:
        n = max(vec, key=lambda k: vec[k][0])
        if vec[n][0] - cpu["step"] < cpu["min"]:
            break
        vec[n][0] = round(vec[n][0] - cpu["step"], 6)
    while sum(v[1] for v in vec.values()) > ram_avail + 1e-9:
        n = max(vec, key=lambda k: vec[k][1])
        if vec[n][1] - mem["step"] < mem["min"]:
            break
        vec[n][1] = vec[n][1] - mem["step"]
    return vec


def init_particle(cfg):
    cpu = cfg["search_space"]["cpus"]
    mem = cfg["search_space"]["mem_mb"]
    vec = {n: [random.uniform(cpu["min"], cpu["max"]),
               random.uniform(mem["min"], mem["max"])]
           for n in cfg["resources"]["containers"]}
    return repair(vec, cfg)


# ---------- Áp cấu hình + đo ----------

def apply_config(vec, base_url):
    for n, (cpus, mem_mb) in vec.items():
        sh(["docker", "update", f"--cpus={cpus}", f"--memory={int(mem_mb)}m", container_name(n)])
    # JVM chỉ đọc lại MaxRAMPercentage khi khởi động.
    sh(["docker", "restart", container_name("backend")])
    return wait_health(base_url)


def run_k6(cfg):
    load = cfg["load"]
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, "steady.json")
    if os.path.exists(out):
        os.remove(out)
    cmd = [
        "docker", "run", "--rm", "-i", "--network", "host",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{RESULTS_DIR}:/out",
        "-e", f"BASE_URL={load['base_url']}",
        "-e", f"RPS={load['target_rps']}",
        "-e", f"WARMUP={load['warmup_seconds']}s",
        "-e", f"STEADY={load['steady_seconds']}s",
        "-e", "PATHS=" + ",".join(load["endpoints"]),
        "grafana/k6:latest", "run", "-",
    ]
    with open(os.path.join(ROOT, "experiments", "load", "steady.js")) as script:
        subprocess.run(cmd, stdin=script, check=True, text=True,
                       stdout=subprocess.DEVNULL)
    with open(out, encoding="utf-8") as f:
        return json.load(f)


def fake_metrics(vec, cfg):
    be, db = vec["backend"], vec["mysql"]
    p95 = 500 / (0.5 + be[0]) + 100 / (0.5 + db[0]) + 30
    oom = 1 if be[1] < 1000 else 0
    return {
        "p95_ms": round(p95, 1),
        "error_rate": 0.0,
        "rps": cfg["load"]["target_rps"],
        "throughput_rps": cfg["load"]["target_rps"],
        "requests": int(cfg["load"]["target_rps"] * cfg["load"]["steady_seconds"]),
        "cpu_used": {"backend": round(min(be[0], 1.5), 2), "mysql": round(min(db[0], 0.5), 2)},
        "cpu_peak": {"backend": round(min(be[0] * 1.2, 4.0), 2),
                     "mysql": round(min(db[0] * 1.2, 4.0), 2)},
        "mem_peak_mb": {"backend": round(be[1] * 0.85, 1), "mysql": round(db[1] * 0.4, 1)},
        "throttled_ratio": {"backend": 0.0, "mysql": 0.0},
        "oom": oom, "oom_kill": oom, "restarts": oom, "healthy": True,
    }


def evaluate(vec, cfg, dry=False):
    started = time.time()
    if dry:
        metrics = fake_metrics(vec, cfg)
        metrics["elapsed_s"] = round(time.time() - started, 2)
        return metrics

    names = cfg["resources"]["containers"]
    if not apply_config(vec, cfg["load"]["base_url"]):
        return {"error": "backend khong healthy sau khi ap cau hinh",
                "p95_ms": float("inf"), "error_rate": 1.0,
                "oom": 0, "oom_kill": 0, "restarts": 0, "healthy": False,
                "elapsed_s": round(time.time() - started, 1)}

    before = oom_snapshot(names)
    sampler = Sampler(names)
    sampler.start()
    try:
        k6 = run_k6(cfg)
    finally:
        sampler.stop_flag = True
        sampler.join(timeout=5)
    after = oom_snapshot(names)

    metrics = {
        "p95_ms": k6.get("p95_ms"),
        "error_rate": k6.get("error_rate"),
        "rps": k6.get("rps"),
        "throughput_rps": round(k6["requests"] / cfg["load"]["steady_seconds"], 2)
        if k6.get("requests") else None,
        "requests": k6.get("requests"),
        **sampler_metrics(sampler.samples, names),
        **oom_delta(before, after, names),
        "healthy": True,
        "elapsed_s": round(time.time() - started, 1),
    }
    return metrics


# ---------- Hàm mục tiêu ----------

def fitness(vec, metrics, cfg):
    p95 = metrics.get("p95_ms")
    if p95 is None or not math.isfinite(p95):
        return float("inf")
    slo = cfg["slo"]["p95_ms"]
    fit = cfg["fitness"]
    cpu_avail = cfg["resources"]["cpu_avail"]
    ram_avail = cfg["resources"]["ram_avail_mb"]
    l_norm = p95 / slo
    r_norm = 0.5 * (sum(v[0] for v in vec.values()) / cpu_avail
                    + sum(v[1] for v in vec.values()) / ram_avail)
    p_sla = max(0.0, (p95 - slo) / slo) + fit["w_oom"] * metrics.get("oom", 0)
    return fit["alpha"] * l_norm + fit["beta"] * r_norm + fit["gamma"] * p_sla


def is_feasible(metrics, cfg):
    slo = cfg["slo"]
    p95 = metrics.get("p95_ms")
    return bool(
        p95 is not None and math.isfinite(p95) and p95 <= slo["p95_ms"]
        and metrics.get("oom", 0) == 0
        and metrics.get("restarts", 0) == 0
        and (metrics.get("error_rate") or 0) <= slo["max_error_rate"]
        and metrics.get("healthy", False)
    )


# ---------- Ba phương án so sánh (Chương 3) ----------

def fixed_vector(cfg):
    m = cfg["methods"]["fixed"]
    return {n: [float(m[n]["cpus"]), float(m[n]["mem_mb"])]
            for n in cfg["resources"]["containers"]}


def rule_vector(cfg, metrics):
    """CPU = ceil(peak_cpu*1.5/0.25)*0.25; RAM = ceil(peak_ws*1.3/128)*128."""
    rule = cfg["methods"]["rule"]
    cpu, mem = cfg["search_space"]["cpus"], cfg["search_space"]["mem_mb"]
    vec = {}
    for n in cfg["resources"]["containers"]:
        peak_cpu = metrics.get("cpu_peak", {}).get(n) or metrics["cpu_used"].get(n, 0)
        c = math.ceil(peak_cpu * rule["cpu_headroom"] / cpu["step"]) * cpu["step"]
        r = math.ceil(metrics["mem_peak_mb"][n] * rule["ram_headroom"] / mem["step"]) * mem["step"]
        vec[n] = [clamp(round(c, 6), cpu["min"], cpu["max"]),
                  clamp(round(r, 6), mem["min"], mem["max"])]
    return repair(vec, cfg)


def latest_gbest():
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "gbest-*.json")))
    if not files:
        raise SystemExit("chưa có gbest-*.json để validate")
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def _mean(vals):
    return round(statistics.mean(vals), 2) if vals else None


def aggregate(rows, names):
    p95 = [r["metrics"]["p95_ms"] for r in rows if r["metrics"].get("p95_ms") is not None]
    thr = [r["metrics"]["throughput_rps"] for r in rows
           if r["metrics"].get("throughput_rps") is not None]
    err = [r["metrics"]["error_rate"] for r in rows
           if r["metrics"].get("error_rate") is not None]
    return {
        "runs": len(rows),
        "p95_mean": _mean(p95),
        "p95_median": round(statistics.median(p95), 2) if p95 else None,
        "p95_min": round(min(p95), 2) if p95 else None,
        "p95_max": round(max(p95), 2) if p95 else None,
        "throughput_mean": _mean(thr),
        "error_rate_mean": _mean(err),
        "cpu_used_mean": {n: _mean([r["metrics"]["cpu_used"].get(n, 0) for r in rows]) for n in names},
        "mem_peak_mean": {n: _mean([r["metrics"]["mem_peak_mb"].get(n, 0) for r in rows]) for n in names},
        "oom_total": sum(r["metrics"].get("oom", 0) for r in rows),
        "restarts_total": sum(r["metrics"].get("restarts", 0) for r in rows),
        "feasible": sum(1 for r in rows if r["feasible"]),
        "F_mean": _mean([r["F"] for r in rows if math.isfinite(r["F"])]),
    }


def run_method(cfg, args):
    method = args.method
    names = cfg["resources"]["containers"]
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log_path = os.path.join(RESULTS_DIR, f"compare-{stamp}-{method}.jsonl")
    log = open(log_path, "w", encoding="utf-8")
    rows, search_s = [], 0.0

    def record(iteration, particle, vec, metrics, f, feasible, note=None):
        row = {"ts": now_iso(), "method": method, "iteration": iteration,
               "particle": particle, "x": vec, "metrics": metrics,
               "F": f, "feasible": feasible, "note": note}
        log.write(json.dumps(row, ensure_ascii=False) + "\n")
        log.flush()
        return row

    if method == "fixed":
        vec = fixed_vector(cfg)
        runs = args.runs or cfg["methods"]["fixed"]["runs"]
    elif method == "rule":
        cal_vec = fixed_vector(cfg)
        cal_started = time.time()
        cal_metrics = evaluate(cal_vec, cfg, args.dry_run)
        search_s = time.time() - cal_started
        vec = rule_vector(cfg, cal_metrics)
        record(-1, -1, cal_vec, cal_metrics,
               fitness(cal_vec, cal_metrics, cfg), is_feasible(cal_metrics, cfg), "calibration")
        runs = args.runs or cfg["methods"]["rule"]["runs"]
        print(f"  rule từ calibration: {vector_str(vec)} (cal={search_s:.1f}s)")
    elif method == "validate":
        gb = latest_gbest()
        vec = {n: [float(v[0]), float(v[1])] for n, v in gb["gbest"].items()}
        runs = args.runs or cfg["pso"]["validation_runs"]
    else:
        raise SystemExit(f"method không hỗ trợ: {method}")

    started = time.time()
    for i in range(runs):
        metrics = evaluate(vec, cfg, args.dry_run)
        f = fitness(vec, metrics, cfg)
        rows.append(record(0, i, vec, metrics, f, is_feasible(metrics, cfg)))
        print(f"  {method} run {i + 1}/{runs}: F={f:.4f} "
              f"p95={metrics.get('p95_ms')} oom={metrics.get('oom')}")
    wall_s = time.time() - started

    summary = {
        "ts": now_iso(), "commit": git_commit(), "config_sha256": config_hash(),
        "dry_run": args.dry_run, "method": method, "vector": vec, "runs": runs,
        "search_s": round(search_s, 1), "wall_s": round(wall_s, 1),
        "per_eval_s": round(wall_s / runs, 1) if runs else None,
        "host_load1_end": host_load1(),
        "aggregate": aggregate(rows, names),
        "log": os.path.basename(log_path),
    }
    summary_path = os.path.join(RESULTS_DIR, f"compare-{stamp}-{method}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    log.close()
    print(f"\n{method}: {vector_str(vec)} runs={runs} search={search_s:.1f}s "
          f"wall={wall_s:.1f}s\nraw: {log_path}\nsummary: {summary_path}")
    return summary


# ---------- Vòng PSO ----------

def vector_str(vec):
    return " ".join(f"{n}=[{v[0]:.2f}c,{int(v[1])}m]" for n, v in vec.items())


def run_pso(cfg, args):
    random.seed(cfg["pso"]["seed"])
    names = cfg["resources"]["containers"]
    cpu = cfg["search_space"]["cpus"]
    mem = cfg["search_space"]["mem_mb"]
    pso = cfg["pso"]
    swarm = args.swarm or pso["swarm"]
    iterations = args.iterations or pso["iterations"]
    max_evals = args.max_evals or cfg["budget"]["max_evaluations"]

    started = time.time()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log_path = os.path.join(RESULTS_DIR, f"pso-{stamp}.jsonl")
    log = open(log_path, "w", encoding="utf-8")

    def record(iteration, particle, vec, metrics, f, feasible):
        row = {
            "ts": now_iso(), "iteration": iteration, "particle": particle,
            "x": vec, "metrics": metrics, "F": f, "feasible": feasible,
        }
        log.write(json.dumps(row, ensure_ascii=False) + "\n")
        log.flush()

    print(f"[{now_iso()}] swarm={swarm} iterations={iterations} max_evals={max_evals} "
          f"dry_run={args.dry_run} commit={git_commit()} load1={host_load1()}")

    particles = [init_particle(cfg) for _ in range(swarm)]
    velocities = [{n: [0.0, 0.0] for n in names} for _ in range(swarm)]
    pbest = [copy.deepcopy(p) for p in particles]
    pbest_f = [float("inf")] * swarm
    gbest, gbest_f = None, float("inf")
    evals = 0

    # Bước 1-3: đánh giá quần thể khởi tạo
    for i in range(swarm):
        if evals >= max_evals:
            break
        metrics = evaluate(particles[i], cfg, args.dry_run)
        f = fitness(particles[i], metrics, cfg)
        evals += 1
        pbest[i], pbest_f[i] = copy.deepcopy(particles[i]), f
        if f < gbest_f:
            gbest, gbest_f = copy.deepcopy(particles[i]), f
        record(0, i, particles[i], metrics, f, is_feasible(metrics, cfg))
        print(f"  init p{i}: {vector_str(particles[i])} F={f:.4f} "
              f"p95={metrics.get('p95_ms')} oom={metrics.get('oom')}")

    # Bước 4-6: lặp
    stall = 0
    for t in range(1, iterations):
        if evals >= max_evals:
            break
        improved = False
        for i in range(swarm):
            if evals >= max_evals:
                break
            for n in names:
                for d in (0, 1):
                    r1, r2 = random.random(), random.random()
                    v = (pso["w"] * velocities[i][n][d]
                         + pso["c1"] * r1 * (pbest[i][n][d] - particles[i][n][d])
                         + pso["c2"] * r2 * (gbest[n][d] - particles[i][n][d]))
                    lo, hi = (cpu["min"], cpu["max"]) if d == 0 else (mem["min"], mem["max"])
                    vmax = pso["vmax_ratio"] * (hi - lo)
                    velocities[i][n][d] = clamp(v, -vmax, vmax)
                    particles[i][n][d] += velocities[i][n][d]
            particles[i] = repair(particles[i], cfg)

            metrics = evaluate(particles[i], cfg, args.dry_run)
            f = fitness(particles[i], metrics, cfg)
            evals += 1
            if f < pbest_f[i]:
                pbest[i], pbest_f[i] = copy.deepcopy(particles[i]), f
            if f < gbest_f:
                gbest, gbest_f = copy.deepcopy(particles[i]), f
                improved = True
            record(t, i, particles[i], metrics, f, is_feasible(metrics, cfg))
            print(f"  it{t} p{i}: {vector_str(particles[i])} F={f:.4f} "
                  f"p95={metrics.get('p95_ms')} oom={metrics.get('oom')} best={gbest_f:.4f}")
        stall = 0 if improved else stall + 1
        if stall >= pso.get("stall_iterations", 3):
            print(f"  dừng: gBest không cải thiện {stall} vòng")
            break

    wall_s = time.time() - started
    summary = {
        "ts": now_iso(), "commit": git_commit(), "config_sha256": config_hash(),
        "dry_run": args.dry_run, "evaluations": evals,
        "gbest": gbest, "gbest_F": gbest_f,
        "wall_s": round(wall_s, 1), "search_s": round(wall_s, 1),
        "per_eval_s": round(wall_s / evals, 1) if evals else None,
        "host_load1_end": host_load1(), "log": os.path.basename(log_path),
    }
    gbest_path = os.path.join(RESULTS_DIR, f"gbest-{stamp}.json")
    with open(gbest_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    log.close()

    print(f"\nGBest: {vector_str(gbest)} F={gbest_f:.4f} evals={evals}")
    print(f"raw: {log_path}\ngbest: {gbest_path}")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="không gọi Docker, dùng metrics giả")
    parser.add_argument("--method", choices=["pso", "fixed", "rule", "validate"], default="pso")
    parser.add_argument("--runs", type=int, help="số lần lặp cho fixed/rule/validate")
    parser.add_argument("--swarm", type=int)
    parser.add_argument("--iterations", type=int)
    parser.add_argument("--max-evals", type=int)
    args = parser.parse_args()

    if args.method == "validate" and args.dry_run:
        raise SystemExit("--method validate cần gbest thật, không hỗ trợ --dry-run")

    cfg = load_config()
    if not args.dry_run:
        try:
            for n in cfg["resources"]["containers"]:
                docker_inspect(container_name(n), "{{.Id}}")
        except subprocess.CalledProcessError:
            raise SystemExit("Stack rental-exp chưa chạy. Chạy: bash experiments/stack/stack.sh up")
        if not wait_health(cfg["load"]["base_url"], timeout=30):
            raise SystemExit("Backend rental-exp không healthy")

    summary = run_pso(cfg, args) if args.method == "pso" else run_method(cfg, args)

    if args.dry_run:
        vec = summary["gbest"] if args.method == "pso" else summary["vector"]
        assert vec is not None, "không tạo được vector"
        if args.method == "pso":
            assert math.isfinite(summary["gbest_F"]), "gbest_F phải hữu hạn"
        for n, (cpus, mem_mb) in vec.items():
            assert cfg["search_space"]["cpus"]["min"] <= cpus <= cfg["search_space"]["cpus"]["max"]
            assert cfg["search_space"]["mem_mb"]["min"] <= mem_mb <= cfg["search_space"]["mem_mb"]["max"]
        assert sum(v[0] for v in vec.values()) <= cfg["resources"]["cpu_avail"] + 1e-9
        assert sum(v[1] for v in vec.values()) <= cfg["resources"]["ram_avail_mb"] + 1e-9
        print("dry-run OK: miền + ngân sách hợp lệ")


if __name__ == "__main__":
    main()
