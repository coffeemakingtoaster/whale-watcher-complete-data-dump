echo "Running for $(cat ./sources.txt | wc -l) sources"

while read line; do
  go run ./main.go $line
done <./sources.txt
