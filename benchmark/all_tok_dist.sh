for llm in "UniXcoder" "CodeGen" "CodeGen25" "StarCoderPlus"; do
	for c in "2" "10" "20" "40"; do
		echo ${llm}_${c}---------------------------------------------------
	        for project in "aaugustin_websockets" "arrow-py_arrow" "geopy_geopy" "graphql-python_graphene" "lektor_lektor" "mwaskom_seaborn" "nvbn_thefuck" "psf_black" "scikit-learn_scikit-learn" "Parsely_streamparse" "Supervisor_supervisor"; do
			python benchmark/token_distance.py --results res_${project}_${llm}c${c}k5t01testsapi
		done
	done
done
