from dataclasses import dataclass


class DiscrepancyTypes:
    KEY_MISMATCH = "key_mismatch"
    TYPE_MISMATCH = "type_mismatch"
    VALUE_MISMATCH = "value_mismatch"
    LENGTH_MISMATCH = "length_mismatch"
    ORDER_MISMATCH = "order_mismatch"


@dataclass
class Discrepancy:
    msg: str
    discrepancy_type: str
    path: str
    expected_value: str
    actual_value: str

    def __str__(self):
        return (
            f"{self.msg} at {self.path}\n"
            f"expected value: {self.expected_value}\n"
            f"actual value: {self.actual_value}"
        )
