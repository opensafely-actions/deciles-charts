from unittest import mock

import pandas
import pytest
from pandas import testing

import deciles_chart


def test_version():
    assert deciles_chart.__version__ == "0.1.0"


class TestGetMeasureTables:
    # It's important to materialise the temporary files and paths within the methods of
    # this class so that they can, for example, be iterated over.

    def test_path_is_not_dir(self, tmp_path):
        tmp_file = tmp_path / "measure_sbp_by_practice.csv"
        tmp_file.touch()
        with pytest.raises(AttributeError):
            next(deciles_chart.get_measure_tables(tmp_file))

    def test_no_recurse(self, tmp_path):
        tmp_sub_path = tmp_path / "measures"
        tmp_sub_path.mkdir()
        with pytest.raises(StopIteration):
            next(deciles_chart.get_measure_tables(tmp_path))

    def test_input_table(self, tmp_path):
        tmp_file = tmp_path / "input_2019-01-01.csv"
        tmp_file.touch()
        with pytest.raises(StopIteration):
            next(deciles_chart.get_measure_tables(tmp_path))

    def test_measure_table(self, tmp_path):
        tmp_file = tmp_path / "measure_sbp_by_practice.csv"
        tmp_file.touch()
        measure_table_csv = pandas.DataFrame(
            columns=[
                "practice",  # group_by
                "has_sbp_event",  # numerator
                "population",  # denominator
                "value",  # assigned by the measures framework
                "date",  # assigned by the measures framework
            ]
        )
        with mock.patch("pandas.read_csv", return_value=measure_table_csv) as mocked:
            measure_table = next(deciles_chart.get_measure_tables(tmp_path))

            mocked.assert_called_once()
            mocked.assert_called_with(tmp_file, parse_dates=["date"])
            assert measure_table.attrs["id"] == "sbp_by_practice"
            assert measure_table.attrs["denominator"] == "population"
            assert measure_table.attrs["group_by"] == ["practice"]


class TestDropRows:
    def test_denominator_is_zero(self):
        measure_table = pandas.DataFrame(
            {
                "practice": [1, 2],
                "has_sbp_event": [1, 0],
                "population": [1, 0],
                "value": [1, 0],
                "date": ["2021-01-01", "2021-01-01"],
            }
        )
        measure_table.attrs["denominator"] = "population"

        obs = deciles_chart.drop_rows(measure_table)

        exp = pandas.DataFrame(
            {
                "practice": [1],
                "has_sbp_event": [1],
                "population": [1],
                "value": [1],
                "date": ["2021-01-01"],
            }
        )
        exp.attrs["denominator"] = "population"

        # Reference tests
        assert measure_table is not obs
        assert measure_table.attrs is not obs.attrs

        # Value tests
        testing.assert_frame_equal(obs, exp)
        assert obs.attrs == exp.attrs
