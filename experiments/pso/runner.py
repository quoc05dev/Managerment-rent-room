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
import hashlib
import json
import math
import os
import random
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


def cgroup_dir(name):
    cid = docker_inspect(name, "{{.Id}}")
    return f"/sys/fs/cgroup/system.slice/docker-{cid}.scope"


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
        return {"cpu_used": {}, "mem_peak_mb": {}, "throttled_ratio": {}}
    first, last = samples[0], samples[-1]
    dt = max(last["t"] - first["t"], 1e-9)
    cpu_used, mem_peak, throttled = {}, {}, {}
    for n in names:
        du = last[n]["cpu"].get("usage_usec", 0) - first[n]["cpu"].get("usage_usec", 0)
        cpu_used[n] = round(du / 1e6 / dt, 3)
        mem_peak[n] = round(max(s[n]["mem"] for s in samples) / (1024 * 1024), 1)
        tu = last[n]["cpu"].get("throttled_usec", 0) - first[n]["cpu"].get("throttled_usec", 0)
        throttled[n] = round(tu / du, 4) if du > 0 else 0.0
    return {"cpu_used": cpu_used, "mem_peak_mb": mem_peak, "throttled_ratio": throttled}


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

def apply_config(vec):
    for n, (cpus, mem_mb) in vec.items():
        sh(["docker", "update", f"--cpus={cpus}", f"--memory={int(mem_mb)}m", container_name(n)])
    # JVM chỉ đọc lại MaxRAMPercentage khi khởi động.
    sh(["docker", "restart", container_name("backend")])
    return wait_health("http://127.0.0.1:8085")


def run_k6(cfg):
    load = cfg["load"]
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, "steady.json")
    if os.path.exists(out):
        os.remove(out)
    cmd = [
        "docker", "run", "--rm", "--network", "host",
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
        "requests": int(cfg["load"]["target_rps"] * cfg["load"]["steady_seconds"]),
        "cpu_used": {"backend": round(min(be[0], 1.5), 2), "mysql": round(min(db[0], 0.5), 2)},
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
    if not apply_config(vec):
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

    summary = {
        "ts": now_iso(), "commit": git_commit(), "config_sha256": config_hash(),
        "dry_run": args.dry_run, "evaluations": evals,
        "gbest": gbest, "gbest_F": gbest_f,
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
    parser.add_argument("--swarm", type=int)
    parser.add_argument("--iterations", type=int)
    parser.add_argument("--max-evals", type=int)
    args = parser.parse_args()

    cfg = load_config()
    if not args.dry_run:
        try:
            for n in cfg["resources"]["containers"]:
                docker_inspect(container_name(n), "{{.Id}}")
        except subprocess.CalledProcessError:
            raise SystemExit("Stack rental-exp chưa chạy. Chạy: bash experiments/stack/stack.sh up")
        if not wait_health(cfg["load"]["base_url"], timeout=30):
            raise SystemExit("Backend rental-exp không healthy")

    summary = run_pso(cfg, args)
    if args.dry_run:
        assert summary["gbest"] is not None, "PSO không tạo được gbest"
        assert math.isfinite(summary["gbest_F"]), "gbest_F phải hữu hạn"
        for n, (cpus, mem_mb) in summary["gbest"].items():
            assert cfg["search_space"]["cpus"]["min"] <= cpus <= cfg["search_space"]["cpus"]["max"]
            assert cfg["search_space"]["mem_mb"]["min"] <= mem_mb <= cfg["search_space"]["mem_mb"]["max"]
        assert sum(v[0] for v in summary["gbest"].values()) <= cfg["resources"]["cpu_avail"] + 1e-9
        assert sum(v[1] for v in summary["gbest"].values()) <= cfg["resources"]["ram_avail_mb"] + 1e-9
        print("dry-run OK: miền + ngân sách hợp lệ")


if __name__ == "__main__":
    main()
