def _url_from_swagger_spec(path_name, path_spec):

    if 'parameters' not in path_spec['get']:
        return path_name

    params = []
    for param_spec in path_spec['get']['parameters']:
        params.append('{}={}'.format(param_spec['name'], param_spec['default']))
    return '{}?{}'.format(path_name, '&'.join(params))

def _identify_service_from_tag(tags):
    if 'api' in tags:
        return 'explorer-api'
    if 'wrapper' in tags:
        return 'es-wrapper'
    if 'udf' in tags:
        return 'udf'
    return None

def pytest_generate_tests(metafunc):
    if 'path' in metafunc.fixturenames:
        from swagger_parser import SwaggerParser
        from specsynthase.specbuilder import SpecBuilder
        import glob
        from os import path

        spec = SpecBuilder()
        for spec_file in glob.glob(path.join(path.dirname(__file__), '../swagger/*')):
            spec.add_spec(spec_file)

        requests = []
        for path_name, path_spec in spec['paths'].iteritems():
            url = _url_from_swagger_spec(path_name, path_spec)
            service = _identify_service_from_tag(path_spec['get']['tags'])
            requests.append((service, url))
        metafunc.parametrize("service,path", requests)