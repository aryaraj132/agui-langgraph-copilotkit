import pytest
from pydantic import ValidationError

from agui_backend_demo.schemas.segment import Condition, ConditionGroup, Segment


def test_condition_creation():
    c = Condition(field="age", operator="greater_than", value=25)
    assert c.field == "age"
    assert c.operator == "greater_than"
    assert c.value == 25


def test_condition_string_value():
    c = Condition(field="country", operator="equals", value="US")
    assert c.value == "US"


def test_condition_float_value():
    c = Condition(field="total_spent", operator="greater_than", value=99.99)
    assert c.value == 99.99


def test_condition_list_value():
    c = Condition(field="country", operator="in", value=["US", "CA", "UK"])
    assert c.value == ["US", "CA", "UK"]


def test_condition_group_and():
    group = ConditionGroup(
        logical_operator="AND",
        conditions=[
            Condition(field="country", operator="equals", value="US"),
            Condition(field="age", operator="greater_than", value=18),
        ],
    )
    assert group.logical_operator == "AND"
    assert len(group.conditions) == 2


def test_condition_group_invalid_operator():
    with pytest.raises(ValidationError):
        ConditionGroup(
            logical_operator="XOR",
            conditions=[Condition(field="age", operator="equals", value=25)],
        )


def test_segment_full():
    segment = Segment(
        name="Active US Users",
        description="Users from the US who are active",
        condition_groups=[
            ConditionGroup(
                logical_operator="AND",
                conditions=[
                    Condition(field="country", operator="equals", value="US"),
                    Condition(
                        field="last_login_date",
                        operator="within_last",
                        value="30 days",
                    ),
                ],
            )
        ],
        estimated_scope="Users matching all activity and location criteria",
    )
    assert segment.name == "Active US Users"
    assert len(segment.condition_groups) == 1
    assert len(segment.condition_groups[0].conditions) == 2


def test_segment_serialization_roundtrip():
    segment = Segment(
        name="Test Segment",
        description="A test",
        condition_groups=[
            ConditionGroup(
                logical_operator="OR",
                conditions=[
                    Condition(field="plan_type", operator="equals", value="premium"),
                    Condition(field="total_spent", operator="greater_than", value=100),
                ],
            )
        ],
    )
    json_str = segment.model_dump_json()
    restored = Segment.model_validate_json(json_str)
    assert restored == segment


def test_segment_optional_estimated_scope():
    segment = Segment(
        name="Minimal",
        description="Minimal segment",
        condition_groups=[
            ConditionGroup(
                logical_operator="AND",
                conditions=[
                    Condition(field="age", operator="equals", value=30),
                ],
            )
        ],
    )
    assert segment.estimated_scope is None
