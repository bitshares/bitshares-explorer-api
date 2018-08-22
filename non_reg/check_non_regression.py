import pytest
import json
import requests
from json_delta import diff, udiff
from swagger_parser import SwaggerParser

TESTED_URL = "http://localhost:5000"
REF_URL = "http://localhost:5005"

def test_request(path):
    ref = requests.get(REF_URL + path)
    actual = requests.get(TESTED_URL + path)
    assert actual.status_code == ref.status_code
    assert ref.status_code == 200
    json_diff = diff(actual.json(), ref.json(), array_align=False, verbose=False)
    if (path == '/get_witnesses'):
        # Filter fields not stable between calls.
        json_diff = [d for d in json_diff if len(d[0]) != 3 or d[0][2] not in ['last_confirmed_block_num', 'last_aslot']]
    assert not json_diff, '\n'.join(udiff(actual.json(), ref.json(), json_diff))
