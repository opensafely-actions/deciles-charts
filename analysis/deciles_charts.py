import argparse
import glob
import json
import logging
import pathlib
import re

import jsonschema
import numpy
import pandas
from ebmdatalab import charts


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


DEFAULT_CONFIG = {
    "show_outer_percentiles": False,
    "charts": {
        "output": True,
    },
}

CONFIG_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "show_outer_percentiles": {"type": "boolean"},
        "charts": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "output": {"type": "boolean"},
            },
        },
    },
}

MEASURE_FNAME_REGEX = re.compile(r"measure_(?P<id>\w+)\.csv")


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


def get_deciles_chart(measure_table, config):
    return charts.deciles_chart(
        measure_table,
        period_column="date",
        column="value",
        show_outer_percentiles=config["show_outer_percentiles"],
    )


def write_deciles_chart(deciles_chart, path):
    deciles_chart.savefig(path, bbox_inches="tight")


def get_path(*args):
    return pathlib.Path(*args).resolve()


def match_paths(pattern):
    return [get_path(x) for x in glob.glob(pattern)]


def parse_config(config_json):
    user_config = json.loads(config_json)
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    try:
        jsonschema.validate(config, CONFIG_SCHEMA)
    except jsonschema.ValidationError as e:
        raise argparse.ArgumentTypeError(e.message) from e
    return config


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
        "--config",
        default=DEFAULT_CONFIG.copy(),
        type=parse_config,
        help="JSON-encoded configuration",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_files = args.input_files
    output_dir = args.output_dir
    config = args.config

    for measure_table in get_measure_tables(input_files):
        measure_table = drop_zero_denominator_rows(measure_table)
        if config["charts"]["output"]:
            chart = get_deciles_chart(measure_table, config)
            id_ = measure_table.attrs["id"]
            fname = f"deciles_chart_{id_}.png"
            write_deciles_chart(chart, output_dir / fname)


if __name__ == "__main__":
    main()
