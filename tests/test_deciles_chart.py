import pandas
import pytest
from pandas import testing

from analysis import deciles_chart


class TestGetMeasureTables:
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
        # arrange
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
        measure_table_in.to_csv(tmp_path / "measure_sbp_by_practice.csv", index=False)

        # act
        measure_table_out = next(deciles_chart.get_measure_tables(tmp_path))

        # assert
        testing.assert_frame_equal(measure_table_out, measure_table_in)
        assert measure_table_out.attrs["id"] == "sbp_by_practice"
        assert measure_table_out.attrs["denominator"] == "population"
        assert measure_table_out.attrs["group_by"] == ["practice"]


def test_drop_zero_denominator_rows():
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

    obs = deciles_chart.drop_zero_denominator_rows(measure_table)

    exp = pandas.DataFrame(
        {
            "practice": [2],
            "has_sbp_event": [1],
            "population": [1],
            "value": [1],
            "date": ["2021-01-01"],
        }
    )
    exp.attrs["denominator"] = "population"

    # Reference tests
    # If the argument has the same reference as the return value, then it hasn't been
    # copied and could have been edited in-place.
    assert measure_table is not obs
    assert measure_table.attrs is not obs.attrs

    # Value tests
    testing.assert_frame_equal(obs, exp)
    assert obs.attrs == exp.attrs
