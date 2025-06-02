"""
Test the parser functionalities.
"""

import pytest

from criteria_pattern.criteria import Criteria
from criteria_pattern.filter import Filter
from criteria_pattern.filter_operator import FilterOperator
from criteria_pattern.parser import validate_object


@pytest.fixture
def target_obj():  # noqa: D103
    return {'lt_value': 10, 'gt_value': 5, 'str_value': 'lorem ipsum dolor sit amet'}


@pytest.mark.parametrize(
    'criteria, expected_result',
    [
        (Criteria(filters=[Filter('lt_value', FilterOperator.LESS, 20)]), True),
        (Criteria(filters=[Filter('lt_value', FilterOperator.LESS, 10)]), False),
        (Criteria(filters=[Filter('gt_value', FilterOperator.GREATER, 1)]), True),
        (Criteria(filters=[Filter('gt_value', FilterOperator.GREATER, 5)]), False),
        (Criteria(filters=[Filter('str_value', FilterOperator.CONTAINS, 'sit')]), True),
        (Criteria(filters=[Filter('str_value', FilterOperator.CONTAINS, 'loremipsum')]), False),
        (
            Criteria(
                filters=[
                    Filter('lt_value', FilterOperator.BETWEEN, [4, 16]),
                    Filter('gt_value', FilterOperator.EQUAL, 5),
                ]
            ),
            True,
        ),
        (
            Criteria(filters=[Filter('lt_value', FilterOperator.LESS, 20)])
            | Criteria(filters=[Filter('str_value', FilterOperator.EQUAL, "NO")]),
            True,
        ),
        (Criteria(filters=[Filter('str_value', FilterOperator.LIKE, '%lorem_ipsum%')]), True),
        (Criteria(filters=[Filter('str_value', FilterOperator.NOT_LIKE, '%lorem__ipsum%')]), True),
    ],
)
def test_filter_obj_with_criteria(criteria, expected_result, target_obj):
    """
    Test the validate object functionality.
    """
    result = validate_object(target_obj, criteria)
    assert result == expected_result
