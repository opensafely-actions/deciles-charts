import argparse
import functools
import pathlib
import re
from typing import Iterator

import pandas
from ebmdatalab import charts


MEASURE_FNAME_REGEX = re.compile(r"measure_(?P<id>\w+)\.csv")


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
def get_deciles_chart(measures_table):
    return charts.deciles_chart(measures_table, period_column="date", column="value")


def write_deciles_chart(deciles_chart, path):
    deciles_chart.savefig(path)


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
        chart = get_deciles_chart(measures_table)
        id_ = measures_table.attrs["id"]
        fname = f"deciles_chart_{id_}.png"
        write_deciles_chart(chart, output_dir / fname)


if __name__ == "__main__":
    main()
