from data_processing.pandas_test import do_pandas_test
from data_processing.polars_test import do_polars_test


def test_pandas():
    res = do_pandas_test()
    assert res is not None


def test_polars():
    res = do_polars_test()
    assert res is not None
