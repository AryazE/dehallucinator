time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/Supervisor_supervisor-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/Supervisor_supervisor-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/aaugustin_websockets-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/aaugustin_websockets-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/celery_celery-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/celery_celery-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/graphql-python_graphene-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/graphql-python_graphene-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/scikit-learn_scikit-learn-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/scikit-learn_scikit-learn-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/mwaskom_seaborn-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/mwaskom_seaborn-apis.json --mode baseline1api --log 1 --k 4 --noTests