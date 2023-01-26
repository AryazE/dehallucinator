from pathlib import Path
import xml.etree.ElementTree as ET

def read_test_results(test_res_path: str, id: int):
    p = Path(test_res_path)
    results = dict()
    if p.exists():
        tree = ET.parse(p)
        root = tree.getroot()
        for child in list(root):
            if child.tag == 'testsuite':
                results.update({
                    'tests': int(child.attrib['tests']),
                    'errors': int(child.attrib['errors']),
                    'failures': int(child.attrib['failures']),
                    'skipped': int(child.attrib['skipped'])
                })
    else:
        results.update({
            'tests': -1,
            'errors': -1,
            'failures': 0,
            'skipped': 0
        })
    results.update({'id': id})
    return results