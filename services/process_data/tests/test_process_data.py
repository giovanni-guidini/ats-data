from unittest.mock import MagicMock

import pytest

from services.process_data import ProcessDataService


class TestProcessData(object):
    @pytest.mark.parametrize(
        "durations,expected",
        [
            (
                [],
                dict(
                    mean_duration=None,
                    median_duration=None,
                    stdev_duration=None,
                    p90_duration=None,
                ),
            ),
            (
                [1],
                dict(
                    mean_duration=1,
                    median_duration=1,
                    stdev_duration=None,
                    p90_duration=None,
                ),
            ),
            (
                [2, 2],
                dict(
                    mean_duration=2,
                    median_duration=2,
                    stdev_duration=0,
                    p90_duration=2,
                ),
            ),
            (
                [2, 3, 4, 5],
                dict(
                    mean_duration=3.5,
                    median_duration=3.5,
                    stdev_duration=1.118033988749895,
                    p90_duration=4.7,
                ),
            ),
        ],
    )
    def test_calculate_statistics(self, durations, expected):
        process_data = ProcessDataService(MagicMock())
        assert process_data.calculate_statistics(durations) == expected
