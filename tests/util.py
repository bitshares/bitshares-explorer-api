from tavern.util.dict_util import check_keys_match_recursive

def validate_unique_value(response, unique_value):
    check_keys_match_recursive(unique_value, response.json(), [], strict=False)

def validate_list_of(response, element_desc):
    elements = response.json()
    assert type(elements) == list
    for e in elements:
        check_keys_match_recursive(element_desc, e, [], strict=False)

