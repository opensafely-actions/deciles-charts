import pandas
from pandas import testing

from analysis import deciles_charts


def test_get_measure_tables(tmp_path):
    # For each measure, the measures framework writes a csv for each week/month, adding
    # the date as a suffix to the file name; and a csv for all weeks/months, adding the
    # date to a column in the file. We define a "measure table" as the latter, because
    # it's easier to work with one file, than with many files/file names. However, it's
    # hard to write a glob pattern that matches the latter but not the former, so
    # `get_measure_tables` filters `input_files`.

    # arrange
    # this is a csv for a week/month
    input_file_1 = tmp_path / "measure_sbp_by_practice_2021-01-01.csv"
    input_file_1.touch()

    # this is a csv for all weeks/months
    measure_table_in = pandas.DataFrame(
        {
            "practice": [1],  # group_by
            "has_sbp_event": [1],  # numerator
            "population": [1],  # denominator
            "value": [1],  # assigned by the measures framework
            "date": ["2021-01-01"],  # assigned by the measures framework
        }
    )
    measure_table_in["date"] = pandas.to_datetime(measure_table_in["date"])
    input_file_2 = tmp_path / "measure_sbp_by_practice.csv"
    measure_table_in.to_csv(input_file_2, index=False)

    # act
    measure_tables_out = list(
        deciles_charts.get_measure_tables([input_file_1, input_file_2])
    )

    # assert
    assert len(measure_tables_out) == 1
    measure_table_out = measure_tables_out[0]
    testing.assert_frame_equal(measure_table_out, measure_table_in)
    assert measure_table_out.attrs["id"] == "sbp_by_practice"
    assert measure_table_out.attrs["denominator"] == "population"
    assert measure_table_out.attrs["group_by"] == ["practice"]


def test_drop_zero_denominator_rows():
    # arrange
    measure_table = pandas.DataFrame(
        {
            "practice": [1, 2],
            "has_sbp_event": [0, 1],
            "population": [0, 1],
            "value": [0, 1],
            "date": ["2021-01-01", "2021-01-01"],
        }
    )
    measure_table.attrs["denominator"] = "population"
    exp_measure_table = pandas.DataFrame(
        {
            "practice": [2],
            "has_sbp_event": [1],
            "population": [1],
            "value": [1],
            "date": ["2021-01-01"],
        }
    )
    exp_measure_table.attrs["denominator"] = "population"

    # act
    obs_measure_table = deciles_charts.drop_zero_denominator_rows(measure_table)

    # assert
    testing.assert_frame_equal(obs_measure_table, exp_measure_table)
    assert obs_measure_table.attrs == exp_measure_table.attrs
    assert obs_measure_table is not measure_table  # test it's a copy
    assert obs_measure_table.attrs is not measure_table.attrs  # test it's a copy


def test_parse_args(tmp_path, monkeypatch):
    # arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "deciles_charts.py",
            "--input-files",
            "input/measure_*.csv",
            "--output-dir",
            "output",
        ],
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()

    input_files = []
    for input_file_name in [
        "measure_has_sbp_event_by_stp_code.csv",
        "measure_has_sbp_event_by_stp_code_2021-01-01.csv",
        "measure_has_sbp_event_by_stp_code_2021-02-01.csv",
        "measure_has_sbp_event_by_stp_code_2021-03-01.csv",
        "measure_has_sbp_event_by_stp_code_2021-04-01.csv",
        "measure_has_sbp_event_by_stp_code_2021-05-01.csv",
        "measure_has_sbp_event_by_stp_code_2021-06-01.csv",
    ]:
        input_file = input_dir / input_file_name
        input_file.touch()
        input_files.append(input_file)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # act
    args = deciles_charts.parse_args()

    # assert
    assert sorted(args.input_files) == sorted(input_files)
    assert args.output_dir == output_dir
