import multiprocessing
import random
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Callable, Generator

import pandas as pd
import polars as pl
from dateutil.relativedelta import relativedelta

random.seed(1234)


class PayFrequency(Enum):
    AtMaturity = "at maturity"
    Annual = "annual"
    Monthly = "monthly"
    Quarterly = "quarterly"
    Semiannual = "semiannual"


def generate_dates(
    start_date: date, end_date: date, pay_freq: PayFrequency, run_date: date = None, move_to_weekday: bool = True
) -> Generator[date, None, None]:
    if not run_date or run_date < start_date:
        run_date = start_date

    if run_date > end_date:
        return

    if pay_freq == PayFrequency.AtMaturity:
        rd = relativedelta(end_date, start_date)
    elif pay_freq == PayFrequency.Annual:
        rd = relativedelta(years=1)
    elif pay_freq == PayFrequency.Monthly:
        rd = relativedelta(months=1)
    elif pay_freq == PayFrequency.Quarterly:
        rd = relativedelta(months=3)
    elif pay_freq == PayFrequency.Semiannual:
        rd = relativedelta(months=6)
    else:
        raise ValueError(f"Cannot gen delta from {pay_freq}")

    multiplier = 0
    yield_date = start_date
    latest_pay_date = start_date
    latest_pay_date_yielded = False

    while yield_date < end_date:
        yield_date = start_date + (multiplier * rd)
        multiplier += 1

        if yield_date >= end_date:
            if not latest_pay_date_yielded:
                yield latest_pay_date
            break

        if yield_date <= run_date:
            latest_pay_date = yield_date
            continue

        if not latest_pay_date_yielded:
            yield latest_pay_date
            latest_pay_date_yielded = True

        yield yield_date

    yield end_date


def wrapper(
    start_date: date, end_date: date, pay_freq: PayFrequency, run_date: date = None, move_to_weekday: bool = True
):
    return list(
        generate_dates(
            start_date,
            end_date,
            pay_freq,
            run_date,
            move_to_weekday,
        )
    )


def random_date(date_1: date, date_2: date) -> date:
    assert date_1 < date_2
    dif = date_2 - date_1
    n_days = random.randrange(1, dif.days - 1)
    new_d = date_1 + timedelta(days=n_days)
    assert date_1 < new_d < date_2
    return new_d


@dataclass
class Result:
    function: Callable
    # result: pd.DataFrame
    time_taken_ms: float
    run_id: uuid.UUID = field(default_factory=uuid.uuid4)


def time_it_ms(func: Callable, args: tuple, iters: int = 25):
    runs_ = []
    for i in range(iters):
        print(f"Testing {func.__name__} - {i + 1:2}/{iters}")
        start_time = time.perf_counter()
        res = func(*args)
        total_time = time.perf_counter() - start_time
        runs_.append(
            Result(
                func.__name__,
                # res,
                total_time,
            )
        )
    return runs_


start = date(2020, 1, 1)
mid = date(2023, 1, 1)
end = date(2026, 1, 1)

pay_freqs = list(PayFrequency)
df_pandas = pd.DataFrame(
    data=(
        (uuid.uuid4(), random_date(start, mid), random_date(mid, end), random.choice(pay_freqs)) for _ in range(10_000)
    ),
    columns=["id", "start_date", "end_date", "pay_freq"],
)
df_polars = pl.from_pandas(df_pandas)


def t_pd_apply() -> pd.DataFrame:
    df_ = df_pandas.copy(True)
    df_["flows"] = df_.apply(lambda r: wrapper(r.start_date, r.end_date, r.pay_freq), axis=1)
    df2_ = df_.explode("flows")
    return df2_


def t_multiproc_zip(pool_: multiprocessing.Pool) -> pd.DataFrame:
    df_ = df_pandas.copy(True)
    args_ = zip(
        df_["start_date"],
        df_["end_date"],
        df_["pay_freq"],
    )
    df_["flows"] = pool_.starmap(wrapper, args_)
    df2_ = df_.explode("flows")
    return df2_


def t_zip() -> pd.DataFrame:
    df_ = df_pandas.copy(True)
    args_ = zip(
        df_["start_date"],
        df_["end_date"],
        df_["pay_freq"],
    )
    df_["flows"] = [wrapper(sd, ed, pf) for sd, ed, pf in args_]
    df2_ = df_.explode("flows")
    return df2_


def t_itertuples() -> pd.DataFrame:
    df_ = df_pandas.copy(True)
    args_ = zip(
        df_["start_date"],
        df_["end_date"],
        df_["pay_freq"],
    )
    flows = []
    for r in df_.itertuples():
        flows.append(wrapper(r.start_date, r.end_date, r.pay_freq))
    df_["flows"] = flows
    df2_ = df_.explode("flows")
    return df2_


if __name__ == "__main__":
    procs = multiprocessing.cpu_count() - 1
    with multiprocessing.Pool(procs) as pool:
        results: list[Result] = [
            *time_it_ms(t_itertuples, ()),
            *time_it_ms(t_pd_apply, ()),
            *time_it_ms(t_multiproc_zip, (pool,)),
            *time_it_ms(t_zip, ()),
        ]
    out_records = pd.DataFrame.from_records((asdict(r) for r in results))
    for func, results_ in out_records.groupby("function"):
        print(func)
        print(results_.describe())
