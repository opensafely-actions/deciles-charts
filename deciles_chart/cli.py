import pathlib

import click

import deciles_chart


@click.command()
@click.argument(
    "input_dir", type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path)
)
def main(input_dir):
    for measures_table in deciles_chart.get_measures_tables(input_dir):
        measures_table = deciles_chart.drop_zero_denominator_rows(measures_table)
        click.echo("Hello, world!")
