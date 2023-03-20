import json
import logging
import time
from datetime import datetime
from typing import Callable

from data_processing.const import out_path
from data_processing.pandas_test import do_pandas_test
from data_processing.polars_test import do_polars_test

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)8s - %(message)s")

log = logging.getLogger(__name__)


def _do_test(func: Callable):
    n = 5
    run_times = dict()
    log.info(f"start {func.__name__}")
    for i in range(n):
        counter_start = time.perf_counter_ns()
        func()
        counter_end = time.perf_counter_ns() - counter_start
        log.info(f"<<< Ending {func.__name__} round {i} after {counter_end}ns")
        run_times[n] = {"ns taken": counter_end - counter_start}

    with open(out_path / f"{func.__name__}.{datetime.now().isoformat()}.json", "w+") as f:
        json.dump(run_times, f)


def do_test():
    _do_test(do_polars_test)
    _do_test(do_pandas_test)


# do_test()
