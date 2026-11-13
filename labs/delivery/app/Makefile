# make test：テストを実行する。CIでも、このコマンドを使う
# make run：手元でコンテナを作って動かす（http://localhost:8080/）
.PHONY: test run
test:
	python3 -m unittest discover -s tests -v
run:
	docker build -t cloudbook-app:local .
	docker run --rm --read-only -p 8080:8080 cloudbook-app:local
