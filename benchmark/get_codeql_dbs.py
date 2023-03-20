from subprocess import run, PIPE
import json

with open('repo_list.txt') as f:
    for line in f:
        line = line.strip()
        if line:
            url = line.split(' ')[0]
            owner = url.split('/')[-2]
            repo = url.split('/')[-1][:-4]
            res = run(['gh', 'api', f'/repos/{owner}/{repo}/code-scanning/codeql/databases'], stdout=PIPE, stderr=PIPE)
            if res.returncode == 0:
                has_codeql_db = json.loads(res.stdout.decode('utf-8').strip())
                for db in has_codeql_db:
                    if db['url'].endswith('python'):
                        print(f"gh api /repos/{owner}/{repo}/code-scanning/codeql/databases/python -H 'Accept: application/zip' > {owner}_{repo}.zip")
                        print(f"unzip {owner}_{repo}.zip -d CodeQLDBs/{owner}_{repo}")
                        print(f"rm {owner}_{repo}.zip")
                        print(f'git clone {url} GitHubProjects/{owner}_{repo}')
                        break
