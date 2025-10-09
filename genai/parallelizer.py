# parallelizer.py
import os
import json
import asyncio
from typing import Awaitable, Callable, Iterable, Tuple, Any, List, Dict

from tqdm.asyncio import tqdm  # modern tqdm with asyncio helpers

JsonDict = Dict[str, Any]


def _load_jsonl(path: str) -> Dict[int, Any]:
    """
    Load a JSONL resume file mapping index -> result.
    Lines with JSON errors are skipped (handles partial writes).
    """
    ext = os.path.splitext(path)[1].lower()
    if not ext == ".jsonl":
        raise ValueError(f"Expected a '.jsonl' filepath for `cache_jsonl_path`; received extension '{ext}'")

    done: Dict[int, Any] = {}
    if not os.path.exists(path):
        return done
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "i" in obj:
                    done[int(obj["i"])] = obj.get("result")
            except json.JSONDecodeError:
                # Skip corrupted/partial lines
                continue
    return done


class _JsonlAppender:
    """
    Async-friendly appender for a JSONL file (with an internal asyncio.Lock).
    Use:
        app = _JsonlAppender(path)
        await app.open()
        await app.write({"i": 1, "result": ...})
        await app.close()
    """
    def __init__(self, path: str):
        self.path = path
        self._f = None
        self._lock = asyncio.Lock()

    async def open(self):
        self._f = open(self.path, "a", encoding="utf-8")

    async def write(self, obj: JsonDict):
        line = json.dumps(obj, ensure_ascii=False)
        async with self._lock:
            self._f.write(line + "\n")
            self._f.flush()
            os.fsync(self._f.fileno())

    async def close(self):
        if self._f:
            self._f.close()
            self._f = None


async def run_async_map(
    fn: Callable[..., Awaitable[Any]],
    inputs: Iterable[Tuple[Any, Any]],
    cache_jsonl_path: str,
    concurrency: int = 100,
    retries: int = 3,
    retry_base_delay: float = 0.5,
    return_only_missing: bool = False,
) -> List[Tuple[int, Any]]:
    """
    Minimal concurrent map with progress + JSONL resume.

    Args:
        fn: async function called as `await fn(a, b)` for each (a, b) input.
        inputs: iterable of 2-tuples. We enumerate() to get the index 'i'.
        cache_jsonl_path: JSONL file where we append {"i": idx, "result": ...} per completion.
                   This enables stop/restart without redoing finished items.
        concurrency: max in-flight tasks.
        retries: transient retries per item before writing {"error": True}.
        retry_base_delay: exponential backoff base (0.5, 1.0, 2.0, ...).
        return_only_missing: if True, return only results computed in this run;
                             else return merged (cache + new), sorted by index.

    Returns:
        List[(index, result)] sorted by index.
    """
    # Load prior results
    done_cache = _load_jsonl(cache_jsonl_path)

    # Materialize inputs so we can enumerate and compute total
    items = list(enumerate(inputs))  # [(i, (a, b)), ...]
    total = len(items)

    # Output accumulator for *this* run
    new_results: Dict[int, Any] = {}

    # Writer
    app = _JsonlAppender(cache_jsonl_path)
    await app.open()

    sem = asyncio.Semaphore(concurrency)

    async def worker(i: int, a: Any, b: Any) -> Tuple[int, Any]:
        # Already cached? Return immediately (no write)
        if i in done_cache:
            return (i, done_cache[i])

        attempt = 0
        while True:
            attempt += 1
            try:
                async with sem:
                    res = await fn(a, b)
                # Persist success
                await app.write({"i": i, "result": res})
                return (i, res)
            except Exception:
                if attempt > retries:
                    res = {"error": True}
                    await app.write({"i": i, "result": res})
                    return (i, res)
                # basic exponential backoff
                await asyncio.sleep(retry_base_delay * (2 ** (attempt - 1)))

    # Build coroutines: skip cached if the caller wants only missing
    coros = []
    for i, (a, b) in items:
        if return_only_missing and i in done_cache:
            continue
        coros.append(worker(i, a, b))

    # Turn into tasks
    tasks = [asyncio.create_task(c) for c in coros]

    # Progress loop (tqdm.asyncio)
    results: List[Tuple[int, Any]] = []
    for fut in tqdm.as_completed(tasks, total=len(tasks), desc="Processing"):
        results.append(await fut)

    # Close writer
    await app.close()

    # Store results from this run
    for i, res in results:
        new_results[i] = res

    # Prepare return
    if return_only_missing:
        merged_pairs = sorted(new_results.items(), key=lambda kv: kv[0])
    else:
        merged = {**done_cache, **new_results}
        merged_pairs = sorted(merged.items(), key=lambda kv: kv[0])

    return merged_pairs


def run_map(
    fn: Callable[..., Awaitable[Any]],
    inputs: Iterable[Tuple[Any, Any]],
    cache_jsonl_path: str,
    **kwargs,
) -> List[Tuple[int, Any]]:
    """
    Synchronous wrapper around run_async_map (uses asyncio.run).
    """
    return asyncio.run(run_async_map(fn, inputs, cache_jsonl_path, **kwargs))
