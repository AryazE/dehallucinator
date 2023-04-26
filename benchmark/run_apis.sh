time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/psf_black-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/psf_black-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/Parsely_streamparse-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/Parsely_streamparse-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/nvbn_thefuck-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/nvbn_thefuck-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/arrow-py_arrow-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/arrow-py_arrow-apis.json --mode baseline1api --log 1 --k 4 --noTests

time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/geopy_geopy-apis.json --mode comment1api --log 1 --k 4 --noTests
time python benchmark/run_project.py --model lCodeGen --config benchmark/benchmark_configs/geopy_geopy-apis.json --mode baseline1api --log 1 --k 4 --noTests
