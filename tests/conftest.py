"""Shared fixtures for all tests."""
import pytest
from axiom.core.models import CodeFile


SIMPLE_SOURCE = """\
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def compute(a, b):
    x = add(a, b)
    y = subtract(a, b)
    return x + y
"""

COMPLEX_SOURCE = """\
def process(data, mode="default"):
    if data is None:
        return None
    if not isinstance(data, list):
        raise TypeError("Expected list")
    result = []
    for item in data:
        if item > 0:
            if item > 100:
                if item > 1000:
                    print("huge")
                else:
                    print("big")
            else:
                print("small")
        elif item == 0:
            print("zero")
        else:
            print("negative")
    for chunk in result:
        if mode == "upper":
            chunk = chunk.upper()
        elif mode == "lower":
            chunk = chunk.lower()
        else:
            chunk = chunk.strip()
    while True:
        try:
            val = int(input())
            break
        except ValueError:
            pass
        except EOFError:
            break
        except OSError:
            break
    return result
"""

DOCSTRING_SOURCE = """\
def greet(name):
    \"\"\"Return a greeting for the given name.\"\"\"
    return f"Hello, {name}"

async def fetch(url):
    \"\"\"Fetch data from a URL asynchronously.\"\"\"
    pass

class MyClass:
    \"\"\"A simple example class.\"\"\"
    def method(self):
        self.greet("world")
"""


@pytest.fixture
def simple_file() -> CodeFile:
    return CodeFile(path="simple.py", language="python", source=SIMPLE_SOURCE)


@pytest.fixture
def complex_file() -> CodeFile:
    return CodeFile(path="complex.py", language="python", source=COMPLEX_SOURCE)


@pytest.fixture
def docstring_file() -> CodeFile:
    return CodeFile(path="docstring.py", language="python", source=DOCSTRING_SOURCE)
