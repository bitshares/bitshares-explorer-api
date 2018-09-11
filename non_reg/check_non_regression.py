import pytest
import json
import requests
from json_delta import diff, udiff
from swagger_parser import SwaggerParser

TESTED = {
    'explorer-api': 'http://localhost:5000',
    'es-wrapper': 'http://localhost:5000',
    'udf': 'http://localhost:5000'
}

REF = {
    'explorer-api': 'http://localhost:5005',
    'es-wrapper': 'http://localhost:5006',
    'udf': 'http://localhost:5007'
}

def test_request(service, path):
    ref = requests.get(REF[service] + path)
    actual = requests.get(TESTED[service] + path)
    assert actual.status_code == ref.status_code
    assert ref.status_code == 200
    json_diff = diff(actual.json(), ref.json(), array_align=False, verbose=False)
    if (path == '/get_witnesses'):
        # Filter fields not stable between calls.
        json_diff = [d for d in json_diff if len(d[0]) != 3 or d[0][2] not in ['last_confirmed_block_num', 'last_aslot']]
    assert not json_diff, '\n'.join(udiff(actual.json(), ref.json(), json_diff))
