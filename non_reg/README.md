# Non regression test

Test all API calls against a reference and a tested server, and compare results.

  - Start the Postgres database and import all data.
  - Start a witness with access to `asset_api` and `orders_api` configured.
  - Run the reference server: `cd ref && flask run --port=5005`
  - Run the tested server: `cd actual && flask run --port=5000`
  - Run tests: `pytest -v check_non_regression.py`
