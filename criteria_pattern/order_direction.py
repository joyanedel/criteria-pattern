"""
Order direction module.
"""

from enum import Enum, unique


@unique
class OrderDirection(str, Enum):
    """
    OrderDirection enum class.

    Example:
    ```python
    from criteria_pattern import OrderDirection

    direction = OrderDirection.ASC
    print(direction)
    # >>> ASC
    ```
    """

    ASC = 'ASC'
    DESC = 'DESC'
