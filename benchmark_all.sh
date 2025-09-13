run_benchmark(){
	(cd $1 && rm -rf *_out )
	(cd $1 && python3 run.py > out${2}.log)
}

run_benchmark ./hado-benchmark/ 1
run_benchmark ./hado-benchmark/ 2
run_benchmark ./hado-benchmark/ 3

run_benchmark ./trivy-benchmark/ 1
run_benchmark ./trivy-benchmark/ 2
run_benchmark ./trivy-benchmark/ 3
