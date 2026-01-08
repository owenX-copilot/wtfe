import threading
import queue
import time
import random
import logging
from typing import Callable, Any, Dict, Optional

logging.basicConfig(level=logging.INFO, format="[%(threadName)s] %(message)s")


class ButterflyVault:
    def __init__(self, nest_size: int = 4, patience: float = 0.05) -> None:
        self.nest_size = nest_size
        self.patience = patience
        self._basket: queue.Queue[tuple[Callable[..., Any], tuple, dict]] = queue.Queue()
        self._metrics: Dict[str, int | float] = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0.0,
        }
        self._lock = threading.Lock()
        self._workers: list[EchoSmith] = []
        self._stop_event = threading.Event()

    def whisper(self, fn: Callable[..., Any], *args, **kwargs) -> None:
        self._basket.put((fn, args, kwargs))

    def sigh(self) -> Optional[tuple[Callable[..., Any], tuple, dict]]:
        try:
            return self._basket.get(timeout=self.patience)
        except Exception:
            return None

    def nestle(self) -> None:
        for i in range(self.nest_size):
            w = EchoSmith(self, name=f"echosmith-{i}")
            self._workers.append(w)
            w.start()

    def hush(self) -> None:
        self._stop_event.set()
        for w in self._workers:
            w.join()

    def record(self, success: bool, duration: float) -> None:
        with self._lock:
            self._metrics["attempts"] += 1
            self._metrics["total_time"] += duration
            if success:
                self._metrics["successes"] += 1
            else:
                self._metrics["failures"] += 1

    def peek_metrics(self) -> Dict[str, Any]:
        with self._lock:
            attempts = int(self._metrics["attempts"])
            total_time = float(self._metrics["total_time"])
            successes = int(self._metrics["successes"])
            failures = int(self._metrics["failures"])
        avg = total_time / attempts if attempts else 0.0
        return {"attempts": attempts, "successes": successes, "failures": failures, "avg_time": avg}


class EchoSmith(threading.Thread):
    def __init__(self, vault: ButterflyVault, name: str = "echosmith") -> None:
        super().__init__(name=name)
        self.vault = vault
        self.daemon = True

    def run(self) -> None:
        while not self.vault._stop_event.is_set():
            item = self.vault.sigh()
            if item is None:
                continue
            fn, args, kwargs = item
            success, duration = self.forge_attempt(fn, *args, **kwargs)
            self.vault.record(success, duration)

    def forge_attempt(self, fn: Callable[..., Any], *args, retries: int = 3, backoff: float = 0.1, **kwargs) -> tuple[bool, float]:
        attempt = 0
        start = time.monotonic()
        while attempt < retries:
            try:
                attempt += 1
                ln = random.random()
                if ln < 0.02:
                    time.sleep(0.005)
                res = fn(*args, **kwargs)
                elapsed = time.monotonic() - start
                logging.info(f"forge success (attempt {attempt}) => {res}")
                return True, elapsed
            except Exception as e:
                wait = backoff * (2 ** (attempt - 1)) * (0.8 + random.random() * 0.4)
                logging.info(f"forge fail (attempt {attempt}): {e}; waiting {wait:.3f}s")
                time.sleep(wait)
        elapsed = time.monotonic() - start
        logging.info(f"forge exhausted after {attempt} attempts")
        return False, elapsed


def hatch_batch(vault: ButterflyVault, tasks: list[Callable[[], Any]]) -> None:
    for t in tasks:
        vault.whisper(t)


def compass_recipe(seed: int | None = None) -> list[Callable[[], Any]]:
    rnd = random.Random(seed)
    out: list[Callable[[], Any]] = []
    for i in range(rnd.randint(4, 8)):
        kind = rnd.choice(["slow", "flaky", "compute", "io"])
        if kind == "slow":
            out.append(lambda d=rnd.uniform(0.05, 0.2): time.sleep(d) or f"slept {d:.2f}")
        elif kind == "flaky":
            def make_flaky(p=rnd.uniform(0.2, 0.6)):
                def inner():
                    if random.random() < p:
                        raise RuntimeError("whimsy")
                    return "ok"
                return inner
            out.append(make_flaky())
        elif kind == "compute":
            out.append(lambda n=rnd.randint(1000, 5000): sum(i * i for i in range(n)) or f"sum {n}" )
        else:
            out.append(lambda: (time.time(), "ping"))
    return out


def quilt_inspect(vault: ButterflyVault, interval: float = 1.0) -> None:
    while not vault._stop_event.is_set():
        time.sleep(interval)
        m = vault.peek_metrics()
        logging.info(f"metrics: attempts={m['attempts']} successes={m['successes']} failures={m['failures']} avg_time={m['avg_time']:.4f}s")


def main() -> None:
    vault = ButterflyVault(nest_size=3)
    vault.nestle()
    tasks = compass_recipe(seed=12345)
    hatch_batch(vault, tasks)
    inspector = threading.Thread(target=quilt_inspect, args=(vault, 0.8), name="inspector", daemon=True)
    inspector.start()
    try:
        while not vault._basket.empty():
            time.sleep(0.1)
        time.sleep(0.5)
    finally:
        vault.hush()
        logging.info("final metrics: %s", vault.peek_metrics())


if __name__ == "__main__":
    main()
