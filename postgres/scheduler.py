#!/usr/bin/env python2

import os
import schedule
import subprocess
import time


BASE_PATH = os.path.dirname(__file__)


def run_standalone_module(name):
    print((" Starting %s " % name).center(80, '='))
    script_name = os.path.join(BASE_PATH, name + '.py')
    subprocess.call(script_name, shell=False)
    print((" Finished %s " % name).center(80, '-'))


def import_assets_job():
    run_standalone_module('import_assets')


def import_holders_job():
    run_standalone_module('import_holders')


def import_markets_job():
    run_standalone_module('import_markets')


def import_referrers_job():
    run_standalone_module('import_referrers')


schedule.every().day.at("02:30").do(import_assets_job)
schedule.every(2).hours.do(import_holders_job)
schedule.every().hour.do(import_markets_job)
schedule.every(4).hours.do(import_referrers_job)


try:
    while True:
        schedule.run_pending()
        time.sleep(30)
except KeyboardInterrupt:
    pass
