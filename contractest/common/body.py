import json
from typing import List, Optional

import xmltodict
from termcolor import colored

from contractest.common.discrepancy import Discrepancy, DiscrepancyTypes
from contractest.config import config


class Body:
    def __init__(self, body: str, api_path: str):
        self.body = body
        self.content_type = self.determine_content_type()
        self.dict = self.parse_body()
        self.api_path = api_path

    def determine_content_type(self) -> str:
        if isinstance(self.body, (dict, list)):  # this happens usually on empty body
            return "application/json"
        if self.body.startswith("{") or self.body.startswith("["):
            return "application/json"
        if self.body.startswith("<"):
            return "application/xml"
        return "text/plain"

    def parse_body(self):
        if self.body == "":
            return {}

        body = self.body
        if self.content_type == "application/json":
            if isinstance(body, str):
                body = json.loads(self.body)
        if self.content_type == "application/xml":
            if isinstance(body, str):
                body = xmltodict.parse(self.body)

        # order by keys alphabetically
        # it should not matter in case of JSON/dict
        # but it can matter in arrays
        k = {}
        for key in sorted(body.keys()):
            k[key] = body[key]

        return k

    def compare(self, expected_body: "Body") -> List[Discrepancy]:
        discrepancies = find_mismatch_of_dicts(
            expected_body.dict, self.dict, self.api_path, discrepancies=[]
        )

        if config.body_comparison.strict_match:
            return discrepancies

        value_discrepancies = [
            d
            for d in discrepancies
            if d.discrepancy_type == DiscrepancyTypes.VALUE_MISMATCH
        ]
        if config.body_comparison.value_match and value_discrepancies:
            return value_discrepancies

        structural_discrepancies = [
            d
            for d in discrepancies
            if d.discrepancy_type == DiscrepancyTypes.KEY_MISMATCH
            or d.discrepancy_type == DiscrepancyTypes.TYPE_MISMATCH
        ]
        if config.body_comparison.structure_match and structural_discrepancies:
            return structural_discrepancies

        order_discrepancies = [
            d
            for d in discrepancies
            if d.discrepancy_type == DiscrepancyTypes.LENGTH_MISMATCH
            or d.discrepancy_type == DiscrepancyTypes.ORDER_MISMATCH
        ]
        if config.body_comparison.array_order_match and order_discrepancies:
            return order_discrepancies

        return discrepancies


def find_mismatch_of_dicts(
    expected_dict,
    actual_dict,
    api_path,
    nested_key="",
    discrepancies: List[Discrepancy] = [],
) -> List[Discrepancy]:
    """
    Find if two dicts are structurally same
    and their values are same.
    Dicts can be nested in multiple levels.
    """
    exp_keys = sorted(expected_dict.keys())
    actual_keys = sorted(actual_dict.keys())
    # TODO implement ignore fields/keys
    for ig in (
        config.body_comparison.ignore_fields or []
    ) + config.body_comparison.ignore_fields_by_path.get(api_path, []):
        if ig in exp_keys:
            exp_keys.remove(ig)
        if ig in actual_keys:
            actual_keys.remove(ig)

    for exp_key, actual_key in zip(exp_keys, actual_keys):
        if exp_key != actual_key:
            discrepancies.append(
                Discrepancy(
                    msg="keys mismatch",
                    discrepancy_type=DiscrepancyTypes.KEY_MISMATCH,
                    path=f"{nested_key}.{exp_key}" if nested_key else exp_key,
                    expected_value=exp_key,
                    actual_value=actual_key,
                )
            )

    common_keys = set(exp_keys).intersection(set(actual_keys))

    for key in common_keys:
        if isinstance(actual_dict[key], dict):
            find_mismatch_of_dicts(
                expected_dict[key],
                actual_dict[key],
                f"{nested_key}.{key}" if nested_key else key,
                discrepancies,
            )
        elif isinstance(actual_dict[key], list):
            find_mismatch_of_lists(
                expected_dict[key],
                actual_dict[key],
                f"{nested_key}.{key}" if nested_key else key,
                discrepancies,
            )
        else:
            # compare types
            if type(expected_dict[key]) != type(actual_dict[key]):  # noqa: E721
                discrepancies.append(
                    Discrepancy(
                        msg="type mismatch",
                        discrepancy_type=DiscrepancyTypes.TYPE_MISMATCH,
                        path=f"{nested_key}.{key}" if nested_key else key,
                        expected_value=type(expected_dict[key]).__name__,
                        actual_value=type(actual_dict[key]).__name__,
                    )
                )

            # compare values
            if expected_dict[key] != actual_dict[key]:
                discrepancies.append(
                    Discrepancy(
                        msg="value mismatch",
                        discrepancy_type=DiscrepancyTypes.VALUE_MISMATCH,
                        path=f"{nested_key}.{key}" if nested_key else key,
                        expected_value=expected_dict[key],
                        actual_value=actual_dict[key],
                    )
                )

    return discrepancies


def find_mismatch_of_lists(expected_list, actual_list, nested_key="", discrepancies=[]):
    if config.body_comparison.array_length_match:
        if len(expected_list) != len(actual_list):
            discrepancies.append(
                Discrepancy(
                    msg="length mismatch",
                    discrepancy_type=DiscrepancyTypes.LENGTH_MISMATCH,
                    path=nested_key,
                    expected_value=len(expected_list),
                    actual_value=len(actual_list),
                )
            )
            return

    small_list = min(len(expected_list or []), len(actual_list or []))

    if config.body_comparison.array_order_match:
        for i in range(small_list):
            if isinstance(actual_list[i], dict):
                find_mismatch_of_dicts(
                    expected_list[i],
                    actual_list[i],
                    f"{nested_key}[{i}]",
                    discrepancies,
                )
            elif isinstance(actual_list[i], list):
                find_mismatch_of_lists(
                    expected_list[i],
                    actual_list[i],
                    f"{nested_key}[{i}]",
                    discrepancies,
                )
            else:
                if expected_list[i] != actual_list[i]:
                    discrepancies.append(
                        Discrepancy(
                            msg="value mismatch",
                            discrepancy_type=DiscrepancyTypes.ORDER_MISMATCH,
                            path=nested_key,
                            expected_value=expected_list[i],
                            actual_value=actual_list[i],
                        )
                    )
    else:
        for i in range(small_list):
            if isinstance(actual_list[i], dict):
                find_mismatch_of_dicts(
                    expected_list[i],
                    actual_list[i],
                    f"{nested_key}[{i}]",
                    discrepancies,
                )
            elif isinstance(actual_list[i], list):
                find_mismatch_of_lists(
                    expected_list[i],
                    actual_list[i],
                    f"{nested_key}[{i}]",
                    discrepancies,
                )
            else:
                if expected_list[i] in actual_list:
                    discrepancies.append(
                        Discrepancy(
                            msg="value mismatch",
                            discrepancy_type=DiscrepancyTypes.VALUE_MISMATCH,
                            path=nested_key,
                            expected_value=expected_list[i],
                            actual_value=actual_list[i],
                        )
                    )


def print_dict_str(
    d: dict, discrepancies: List[Discrepancy], pad=0, nested_key="", print_str=""
) -> str:
    """
    Make printable padded dict with pointing out discrepancies
    """
    key_dis = [
        dis
        for dis in discrepancies
        if dis.discrepancy_type == DiscrepancyTypes.KEY_MISMATCH
    ]
    for key in sorted(d.keys()):
        nk = f"{nested_key}.{key}" if nested_key else key
        if isinstance(d[key], dict):
            # print_str += f"\n{' ' * pad}{key}:"
            print_str += f"\n{' ' * pad}"
            if any(dis.path == nk for dis in key_dis):
                print_str += colored(
                    f"{key}: <--- {key_dis[0]}",
                    "red",
                    attrs=["reverse", "blink"],
                )
            print_str = print_dict_str(d[key], discrepancies, pad + 2, nk, print_str)
        elif isinstance(d[key], list):
            # print_str += f"\n{' ' * pad}{key}:"
            print_str += f"\n{' ' * pad}"
            if any(dis.path == nk for dis in key_dis):
                print_str += colored(
                    f"{key}: <--- {key_dis[0]}",
                    "red",
                    attrs=["reverse", "blink"],
                )
            print_str = print_list_str(d[key], discrepancies, pad + 2, nk, print_str)
        else:
            if dis := get_discrepancy_by_path(discrepancies, nk):
                print_str += colored(
                    f"\n{' ' * pad}{key}: {d[key]} <--- {dis}",
                    "red",
                    attrs=["reverse", "blink"],
                )
            else:
                print_str += f"\n{' ' * pad}{key}: {d[key]}"
    return print_str


def print_list_str(
    l: list, discrepancies: List[Discrepancy], pad=0, nested_key="", print_str=""
) -> str:
    """
    Make printable padded list with pointing out discrepancies
    """
    for i, item in enumerate(l):
        if isinstance(item, dict):
            print_str += f"\n{' ' * pad}[{i}]:"
            print_str = print_dict_str(
                item, discrepancies, pad + 2, f"{nested_key}[{i}]", print_str
            )
        elif isinstance(item, list):
            print_str += f"\n{' ' * pad}[{i}]:"
            print_str = print_list_str(
                item, discrepancies, pad + 2, f"{nested_key}[{i}]", print_str
            )
        else:
            if dis := get_discrepancy_by_path(discrepancies, nested_key):
                print_str += colored(
                    f"\n{' ' * pad}[{i}]: {item} <--- {dis}",
                    "red",
                    attrs=["reverse", "blink"],
                )
            else:
                print_str += f"\n{' ' * pad}[{i}]: {item}"
    return print_str


def get_discrepancy_by_path(
    discrepancies: List[Discrepancy], path: str
) -> Optional[Discrepancy]:
    for dis in discrepancies:
        if dis.path == path:
            return dis
    return None


def determine_two_dicts_are_structurally_same(
    expected_dict, actual_dict
) -> List[Discrepancy]:
    discrepancies: List[Discrepancy] = []

    def get_dict_discrepancies(d1, d2, nested_key, discrepancies):
        for key in d1.keys():
            if key not in d2:
                discrepancies.append(
                    Discrepancy(
                        msg="key mismatch",
                        discrepancy_type=DiscrepancyTypes.KEY_MISMATCH,
                        path=f"{nested_key}.{key}" if nested_key else key,
                        expected_value=key,
                        actual_value=None,
                    )
                )
                continue
            if isinstance(d1[key], dict):
                get_dict_discrepancies(
                    d1[key],
                    d2[key],
                    f"{nested_key}.{key}" if nested_key else key,
                    discrepancies,
                )
            elif isinstance(d1[key], list):
                get_list_discrepancies(
                    d1[key],
                    d2[key],
                    f"{nested_key}.{key}" if nested_key else key,
                    discrepancies,
                )
            else:
                if d1[key] != d2[key]:
                    discrepancies.append(
                        Discrepancy(
                            msg="value mismatch",
                            discrepancy_type=DiscrepancyTypes.VALUE_MISMATCH,
                            path=f"{nested_key}.{key}" if nested_key else key,
                            expected_value=d1[key],
                            actual_value=d2[key],
                        )
                    )

    def get_list_discrepancies(l1, l2, nested_key, discrepancies):
        for i in range(len(l1)):
            if isinstance(l1[i], dict):
                get_dict_discrepancies(
                    l1[i],
                    l2[i],
                    f"{nested_key}[{i}]" if nested_key else f"[{i}]",
                    discrepancies,
                )
            elif isinstance(l1[i], list):
                get_list_discrepancies(
                    l1[i],
                    l2[i],
                    f"{nested_key}[{i}]" if nested_key else f"[{i}]",
                    discrepancies,
                )
            else:
                if l1[i] != l2[i]:
                    discrepancies.append(
                        Discrepancy(
                            msg="value mismatch",
                            discrepancy_type=DiscrepancyTypes.VALUE_MISMATCH,
                            path=f"{nested_key}[{i}]" if nested_key else f"[{i}]",
                            expected_value=l1[i],
                            actual_value=l2[i],
                        )
                    )

    get_dict_discrepancies(expected_dict, actual_dict, "", discrepancies)
    return discrepancies
