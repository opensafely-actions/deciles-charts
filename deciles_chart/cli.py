import pathlib

import click

import deciles_chart


@click.command()
@click.argument(
    "input_dir", type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path)
)
@click.argument(
    "output_dir", type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path)
)
def main(input_dir, output_dir):
    for measures_table in deciles_chart.get_measures_tables(input_dir):
        measures_table = deciles_chart.drop_zero_denominator_rows(measures_table)
        deciles_table = deciles_chart.get_deciles_table(measures_table)
        chart = deciles_chart.get_deciles_chart(deciles_table)
        deciles_chart.write_deciles_chart(chart, output_dir)
