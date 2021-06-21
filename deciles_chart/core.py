import functools
import pathlib
import re
from typing import Iterator

import numpy
import pandas

MEASURE_FNAME_REGEX = re.compile(r"measure_(?P<id>\w+)\.csv")
DECILES = pandas.Series(numpy.arange(0.1, 1, 0.1), name="deciles")


def _get_denominator(measure_table):
    return measure_table.columns[-3]


def _get_group_by(measure_table):
    return list(measure_table.columns[:-4])


def get_measure_tables(path: pathlib.Path) -> Iterator[pandas.DataFrame]:
    if not path.is_dir():
        raise AttributeError()

    for sub_path in path.iterdir():
        if not sub_path.is_file():
            continue

        measure_fname_match = re.match(MEASURE_FNAME_REGEX, sub_path.name)
        if measure_fname_match is not None:
            # The `date` column is assigned by the measures framework.
            measure_table = pandas.read_csv(sub_path, parse_dates=["date"])

            # We can reconstruct the parameters passed to `Measure` without
            # the study definition.
            measure_table.attrs["id"] = measure_fname_match.group("id")
            measure_table.attrs["denominator"] = _get_denominator(measure_table)
            measure_table.attrs["group_by"] = _get_group_by(measure_table)

            yield measure_table


def is_measure_table(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        measure_table = args[0]

        assert "value" in measure_table.columns, "Missing value column"
        assert "date" in measure_table.columns, "Missing date column"

        assert "id" in measure_table.attrs, "Missing id attribute"
        assert "denominator" in measure_table.attrs, "Missing denominator attribute"
        assert "group_by" in measure_table.attrs, "Missing group_by attribute"

        return func(*args, **kwargs)

    return wrapper


@is_measure_table
def drop_zero_denominator_rows(measure_table: pandas.DataFrame) -> pandas.DataFrame:
    mask = measure_table[measure_table.attrs["denominator"]] > 0
    return measure_table[mask].reset_index(drop=True)


@is_measure_table
def get_deciles_table(measure_table: pandas.DataFrame) -> pandas.DataFrame:
    by = ["date"] + measure_table.attrs["group_by"][1:]
    deciles_table = measure_table.groupby(by)["value"].quantile(DECILES).reset_index()
    # `measure_table.attrs` isn't persisted.
    deciles_table.attrs = measure_table.attrs.copy()
    return deciles_table


def is_deciles_table(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        deciles_table = args[0]

        assert "date" in deciles_table.columns, "Missing date column"
        assert "deciles" in deciles_table.columns, "Missing deciles column"
        assert "value" in deciles_table.columns, "Missing value column"

        assert "id" in deciles_table.attrs, "Missing id attribute"
        assert "denominator" in deciles_table.attrs, "Missing denominator attribute"
        assert "group_by" in deciles_table.attrs, "Missing group_by attribute"

        return func(*args, **kwargs)

    return wrapper
