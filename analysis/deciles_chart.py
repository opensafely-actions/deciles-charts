import argparse
import functools
import json
import pathlib
import re
from typing import Any, Dict, Iterator

import altair  # type: ignore
import numpy
import pandas


MEASURE_FNAME_REGEX = re.compile(r"measure_(?P<id>\w+)\.csv")
DECILES = pandas.Series(numpy.arange(0.1, 1, 0.1), name="deciles")

altair.data_transformers.disable_max_rows()


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
    # Previously, it wasn't necessary to rename "level_1", which is created by the call
    # to .quantile, to "deciles" because this method used the name of DECILES (i.e.
    # Series.name). However, it now is, which may be a regression in Pandas. When we
    # downgrade Pandas (a prod dependency) to match opensafely-core/python-docker, we
    # should revisit.
    deciles_table = deciles_table.rename(columns={"level_1": "deciles"})
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


@is_deciles_table
def get_deciles_chart(deciles_table: pandas.DataFrame) -> Dict[str, Any]:
    chart = (
        altair.Chart(deciles_table)
        .mark_line()
        .encode(
            x="date:T",
            y="value:Q",
            detail="deciles:O",
        )
    )

    facets = deciles_table.columns[1:-2]
    if not facets.empty:
        assert len(facets) == 1, "We cannot facet by more than one column"  # FIXME
        chart = chart.facet(row=f"{facets[0]}:N")

    # It's important to add top-level chart properties last, because `chart` may now be
    # an instance of `FacetChart`. `usermeta` is part of the VegaLite specification.
    chart = chart.properties(usermeta=deciles_table.attrs.copy())

    return chart.to_dict()


def write_deciles_chart(deciles_chart: Dict[str, Any], path: pathlib.Path) -> None:
    id_ = deciles_chart["usermeta"]["id"]
    fname = f"deciles_chart_{id_}.vl.json"
    fpath = path / fname
    with open(fpath, "w", encoding="utf8") as f:
        json.dump(deciles_chart, f, indent=2)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        required=True,
        type=pathlib.Path,
        help="Path to the input directory",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        type=pathlib.Path,
        help="Path to the output directory",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    for measures_table in get_measure_tables(input_dir):
        measures_table = drop_zero_denominator_rows(measures_table)
        deciles_table = get_deciles_table(measures_table)
        chart = get_deciles_chart(deciles_table)
        write_deciles_chart(chart, output_dir)


if __name__ == "__main__":
    main()
