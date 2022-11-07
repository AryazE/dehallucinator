import os
import pytest
from simple1.main import get_credit_scores

@pytest.fixture
def file():
    with open('data.csv', 'w') as f:
        f.write('id,age,salary\n1,20,2000\n2,40,2000\n3,20,20000')
    yield
    os.remove('data.csv')

def test_get_credit_scores(file):
    s = get_credit_scores()
    assert len(s) == 3
    assert s == [100, 50, 1000]