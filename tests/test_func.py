import filecmp
import shutil
import subprocess

import pytest
import yaml


def get_test_name(configfile: str):
    return configfile.split("/")[-1].split(".")[0]


def run_a_test(configfile: str):
    subprocess.run(["sh", "./main.sh", configfile], check=True)
    tmp = yaml.safe_load(open(configfile, "r"))
    shutil.move("global.log", f"./results/{get_test_name(configfile)}.log")
    for i in range(2, int(tmp["servers"]) + 1):
        if not filecmp.cmp(f"1.log", f"{i}.log", shallow=False):
            return False
    return True


def test_basic():
    assert run_a_test("config/basic.yaml")


def test_111():
    assert run_a_test("config/one_one_one.yaml")


def test_113():
    assert run_a_test("config/one_one_three.yaml")


def test_119():
    assert run_a_test("config/one_one_nine.yaml")


def test_331():
    assert run_a_test("config/three_one_one.yaml")


def test_333():
    assert run_a_test("config/three_three_three.yaml")


def test_339():
    assert run_a_test("config/three_three_nine.yaml")
