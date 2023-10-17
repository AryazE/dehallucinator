# DiCoder
Developer assistant with dialog between an LLM and a code analyzer

This repository contains the scripts and dataset for "DiCoder: Iterative Code Completion" paper.

The `benchmark` directory contains the scripts and configuration files needed to run the evaluations.
The `coder` directory contains the implementation of DiCoder.
The scripts in `server` allow running open source LLMs on a remote server so that DiCoder can use them through an API call.  

## How to use
Install DiCoder:
```bash
pip install -r requirements-client.txt
pip install -e .
```
DiCoder is currently in experimental phase, so the use is through completion specifications from json files.
Samples of such files can be found in `benchmark/benchmark_configs/`.
The files can be generated for any project via `benchmark/make_config.py` and `benchmark/API_config.py` scripts.  

Steps to run DiCoder from scratch:  
1. Copy the project to `benchmark/GitHubProjects/`.
2. Run 
```bash
python benchmark/API_config.py --project benchmark/GitHubProjects/<your_project> --tests <path_to_tests> --packageName <package_name>
```
3. Create the experiments directory:
```bash
mkdir benchmark/experiment
```
4. Run
```bash
python benchmark/run_project.py --model <model_name> --config benchmark/becnhmark_configs/<project_config>.json --mode comment --k 4 --c 20 --noTests
```
These steps will first generate the completion tasks for your project, and then run DiCoder to generate the completions.  

To rerun the experiments from our paper, run
```bash
bash benchmark/run_all.sh
```
to run the baselines and DiCoder with default settings on the 11 projects.  
To run the ablation study, run
```bash
bash benchmark/run_var.sh
```
To generate the results from these experiments, run
```bash
python benchmark/process_results.py --project <path_to_project_in_experiment> --modes <list_of_modes> --output <output_dir>
python benchmark/further_process_results.py --results <output_from_previous>
```
