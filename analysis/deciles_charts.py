import argparse
import glob
import logging
import pathlib
import re

import numpy
import pandas
from ebmdatalab import charts


MEASURE_FNAME_REGEX = re.compile(r"measure_(?P<id>\w+)\.csv")

# replicate cohort-extractor's logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s [%(levelname)-9s] %(message)s [%(module)s]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
logger.addHandler(handler)


def get_measure_tables(input_files):
    for input_file in input_files:
        measure_fname_match = re.match(MEASURE_FNAME_REGEX, input_file.name)
        if measure_fname_match is not None:
            measure_table = pandas.read_csv(input_file, parse_dates=["date"])
            measure_table.attrs["id"] = measure_fname_match.group("id")
            yield measure_table


def drop_zero_denominator_rows(measure_table):
    """
    Zero-denominator rows could cause the deciles to be computed incorrectly, so should
    be dropped beforehand. For example, a practice can have zero registered patients. If
    the measure is computed from the number of registered patients by practice, then
    this practice will have a denominator of zero and, consequently, a value of inf.
    Depending on the implementation, this practice's value may be sorted as greater than
    other practices' values, which may increase the deciles.
    """
    # It's non-trivial to identify the denominator column without the associated Measure
    # instance. It's much easier to test the value column for inf, which is returned by
    # Pandas when the second argument of a division operation is zero.
    is_not_inf = measure_table["value"] != numpy.inf
    num_is_inf = len(is_not_inf) - is_not_inf.sum()
    logger.info(f"Dropping {num_is_inf} zero-denominator rows")
    return measure_table[is_not_inf].reset_index(drop=True)


def get_deciles_chart(measure_table, show_outer_percentiles):
    return charts.deciles_chart(measure_table, period_column="date", column="value", show_outer_percentiles=show_outer_percentiles)


def write_deciles_chart(deciles_chart, path):
    deciles_chart.savefig(path)


def get_path(*args):
    return pathlib.Path(*args).resolve()


def match_paths(pattern):
    return [get_path(x) for x in glob.glob(pattern)]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-files",
        required=True,
        type=match_paths,
        help="Glob pattern for matching one or more input files",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=get_path,
        help="Path to the output directory",
    )
    parser.add_argument(
        "--show-outer-percentiles",
        required=False,
        default=False,
        action="store_true",
        help="Show the outer percentiles (1-9 & 91-99)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_files = args.input_files
    output_dir = args.output_dir
    show_outer_percentiles=args.show_outer_percentiles

    for measure_table in get_measure_tables(input_files):
        measure_table = drop_zero_denominator_rows(measure_table)
        chart = get_deciles_chart(measure_table, show_outer_percentiles=show_outer_percentiles)
        id_ = measure_table.attrs["id"]
        fname = f"deciles_chart_{id_}.png"
        write_deciles_chart(chart, output_dir / fname)


if __name__ == "__main__":
    main()
