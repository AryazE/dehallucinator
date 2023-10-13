#for llm in "CodeGen25"; do
#       for project in "aaugustin_websockets" "arrow-py_arrow" "geopy_geopy" "graphql-python_graphene" "lektor_lektor" "mwaskom_seaborn" "nvbn_thefuck" "psf_black" "scikit-learn_scikit-learn" "Parsely_streamparse" "Supervisor_supervisor"; do 
#               echo ${llm}_${project}
#               python benchmark/process_results.py --project benchmark/experiment_${llm}/$project --modes baseline${llm}c10k5t01testsapi comment${llm}c2k5t01testsapi --output res_${project}_${llm}c2k5t01testsapi
#               python benchmark/further_process_results.py --results res_${project}_${llm}c2k5t01testsapi
#               python benchmark/process_results.py --project benchmark/experiment_${llm}/$project --modes baseline${llm}c10k5t01testsapi comment${llm}c10k5t01testsapi --output res_${project}_${llm}c10k5t01testsapi
#               python benchmark/further_process_results.py --results res_${project}_${llm}c10k5t01testsapi
#               python benchmark/process_results.py --project benchmark/experiment_${llm}/$project --modes baseline${llm}c10k5t01testsapi comment${llm}c40k5t01testsapi --output res_${project}_${llm}c40k5t01testsapi
#               python benchmark/further_process_results.py --results res_${project}_${llm}c40k5t01testsapi
#       done
#done

for llm in "CodeGen25"; do
        echo ${llm}--------------------------------
        cat res_*_*_${llm}c2k*/spreadsheet.csv
        echo "------------------------------"
        cat res_*_*_${llm}c10k*/spreadsheet.csv
        echo "------------------------------"
        cat res_*_*_${llm}c20k*/spreadsheet.csv
        echo "------------------------------"
        cat res_*_*_${llm}c40k*/spreadsheet.csv
        echo "------------------------------"
done

