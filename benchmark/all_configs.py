from pathlib import Path
import make_config
import API_config

here = Path(__file__).parent
with open(here/'repo_list_4.txt', 'r') as f:
    lines = f.read().splitlines()
for line in lines:
    parts = line.split(' ')
    url = parts[0]
    owner = url.split('/')[-2]
    repo = url.split('/')[-1][:-4]
    tests = parts[-1]
    # make_config.make_config(str(here/'GitHubProjects'/f'{owner}_{repo}'), str(here/'GitHubProjects'/f'{owner}_{repo}'/tests))
    API_config.make_config(str(here/'GitHubProjects'/f'{owner}_{repo}'), str(here/'GitHubProjects'/f'{owner}_{repo}'/tests), repo.replace('-', '_'), with_tests=True)