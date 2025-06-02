"""
This module contains the parser functions.
"""

from typing import Any

from .criteria import AndCriteria, Criteria, NotCriteria, OrCriteria
from .filter import Filter
from .filter_operator import FilterOperator


def parse_rules(rule_data: dict[str, Any]) -> Criteria:
    """
    Parse rule data dictionary into Criteria objects, preserving messages.
    """
    filters = []

    for field, filter_def in rule_data['filters'].items():
        operator = _convert_operator(filter_def['operator'])
        value = filter_def['value']
        # Create filter and add message as an attribute
        filter = Filter(field=field, operator=operator, value=value)
        if 'message' in filter_def:
            filter.message = filter_def['message']
        filters.append(filter)

    return Criteria(filters=filters)


def validate_object(obj: dict, criteria: Criteria) -> bool:
    """
    Validate if an object (dictionary) meets all the criteria filters.

    Args:
        obj: The dictionary object to validate
        criteria: The Criteria object containing filters to apply

    Returns:
        bool: True if object meets all criteria, False otherwise
    """
    if not criteria.has_filters():
        return True  # No filters means object is valid

    # Handle different criteria types
    if isinstance(criteria, AndCriteria):
        return validate_object(obj, criteria.left) and validate_object(obj, criteria.right)
    elif isinstance(criteria, OrCriteria):
        return validate_object(obj, criteria.left) or validate_object(obj, criteria.right)
    elif isinstance(criteria, NotCriteria):
        return not validate_object(obj, criteria.criteria)

    # Base case - evaluate all filters in the criteria
    for filter in criteria.filters:
        field_value = obj.get(filter.field)
        if not _evaluate_filter(field_value, filter):
            return False

    return True


def validate_object_with_messages(obj: dict, criteria: Criteria) -> tuple[bool, list[str]]:
    """
    Validate object and return error messages for failed filters.

    Args:
        obj: The dictionary object to validate
        criteria: The Criteria object

    Returns:
        tuple: (is_valid, error_messages)
    """
    if not criteria.has_filters():
        return (True, [])

    errors = []
    is_valid = True

    # Handle different criteria types
    if isinstance(criteria, AndCriteria):
        valid1, errors1 = validate_object_with_messages(obj, criteria.left)
        valid2, errors2 = validate_object_with_messages(obj, criteria.right)
        return (valid1 and valid2, errors1 + errors2)
    elif isinstance(criteria, OrCriteria):
        valid1, errors1 = validate_object_with_messages(obj, criteria.left)
        valid2, errors2 = validate_object_with_messages(obj, criteria.right)
        return (valid1 or valid2, errors1 if valid1 else errors2)
    elif isinstance(criteria, NotCriteria):
        valid, msgs = validate_object_with_messages(obj, criteria.criteria)
        return (not valid, msgs)

    # Base case - evaluate all filters
    for filter in criteria.filters:
        field_value = obj.get(filter.field)
        if not _evaluate_filter(field_value, filter):
            # Try to get a message if available
            message = getattr(filter, 'message', None) or f"Field '{filter.field}' failed {filter.operator} check"
            errors.append(message)
            is_valid = False

    return (is_valid, errors)


def _evaluate_filter(obj_value: Any, filter: Filter) -> bool:  # noqa: C901
    """
    Evaluate a single filter against an object's value.

    Args:
        obj_value: The value from the object to compare
        filter: The filter to apply

    Returns:
        bool: True if the filter condition is met
    """
    operator = filter.operator
    filter_value = filter.value

    # Handle NULL checks first
    if operator == FilterOperator.IS_NULL:
        return obj_value is None
    elif operator == FilterOperator.IS_NOT_NULL:
        return obj_value is not None

    # For other operators, if obj_value is None and we're not checking for NULL, return False
    if obj_value is None:
        return False

    # Comparison operators
    if operator == FilterOperator.EQUAL:
        return obj_value == filter_value
    elif operator == FilterOperator.NOT_EQUAL:
        return obj_value != filter_value
    elif operator == FilterOperator.GREATER:
        return obj_value > filter_value
    elif operator == FilterOperator.GREATER_OR_EQUAL:
        return obj_value >= filter_value
    elif operator == FilterOperator.LESS:
        return obj_value < filter_value
    elif operator == FilterOperator.LESS_OR_EQUAL:
        return obj_value <= filter_value

    # String operators
    if isinstance(obj_value, str):
        if operator == FilterOperator.LIKE:
            # Convert SQL LIKE pattern to Python regex
            pattern = filter_value.replace('%', '.*').replace('_', '.')
            import re

            return bool(re.fullmatch(pattern, obj_value))
        elif operator == FilterOperator.NOT_LIKE:
            pattern = filter_value.replace('%', '.*').replace('_', '.')
            import re

            return not bool(re.fullmatch(pattern, obj_value))
        elif operator == FilterOperator.CONTAINS:
            return filter_value in obj_value
        elif operator == FilterOperator.NOT_CONTAINS:
            return filter_value not in obj_value
        elif operator == FilterOperator.STARTS_WITH:
            return obj_value.startswith(filter_value)
        elif operator == FilterOperator.NOT_STARTS_WITH:
            return not obj_value.startswith(filter_value)
        elif operator == FilterOperator.ENDS_WITH:
            return obj_value.endswith(filter_value)
        elif operator == FilterOperator.NOT_ENDS_WITH:
            return not obj_value.endswith(filter_value)

    # Range operators
    if operator == FilterOperator.BETWEEN:
        if not isinstance(filter_value, list | tuple) or len(filter_value) != 2:
            raise ValueError('BETWEEN operator requires a 2-element list/tuple as value')
        return filter_value[0] <= obj_value <= filter_value[1]
    elif operator == FilterOperator.NOT_BETWEEN:
        if not isinstance(filter_value, list | tuple) or len(filter_value) != 2:
            raise ValueError('NOT BETWEEN operator requires a 2-element list/tuple as value')
        return not (filter_value[0] <= obj_value <= filter_value[1])

    # If we get here, the operator isn't supported
    raise ValueError(f'Unsupported filter operator: {operator}')


def _convert_operator(op_str: str) -> FilterOperator:
    """
    Convert operator string from JSON to FilterOperator enum.

    Args:
        op_str: Operator string from JSON

    Returns:
        FilterOperator: The corresponding enum value

    Raises:
        ValueError: If operator string is not recognized
    """
    operator_map = {
        'eq': FilterOperator.EQUAL,
        'ne': FilterOperator.NOT_EQUAL,
        'gt': FilterOperator.GREATER,
        'ge': FilterOperator.GREATER_OR_EQUAL,
        'lt': FilterOperator.LESS,
        'le': FilterOperator.LESS_OR_EQUAL,
        'contains': FilterOperator.CONTAINS,
        'not_contains': FilterOperator.NOT_CONTAINS,
        'starts_with': FilterOperator.STARTS_WITH,
        'not_starts_with': FilterOperator.NOT_STARTS_WITH,
        'ends_with': FilterOperator.ENDS_WITH,
        'not_ends_with': FilterOperator.NOT_ENDS_WITH,
        'like': FilterOperator.LIKE,
        'not_like': FilterOperator.NOT_LIKE,
        'is_null': FilterOperator.IS_NULL,
        'is_not_null': FilterOperator.IS_NOT_NULL,
        'between': FilterOperator.BETWEEN,
        'not_between': FilterOperator.NOT_BETWEEN,
    }

    if op_str not in operator_map:
        raise ValueError(f'Unknown operator: {op_str}')

    return operator_map[op_str]
