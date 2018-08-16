def pytest_generate_tests(metafunc):
    if 'path' in metafunc.fixturenames:
        from swagger_parser import SwaggerParser

        parser = SwaggerParser(swagger_path='../api.yaml')

        requests = []
        for path_name, path_spec in parser.paths.iteritems():
            params = []
            for param_name, param_spec in path_spec['get']['parameters'].iteritems():
                params.append('{}={}'.format(param_name, param_spec['default']))
            requests.append('{}{}'.format(path_name, '' if not params else '?{}'.format('&'.join(params))))
        metafunc.parametrize("path", requests)