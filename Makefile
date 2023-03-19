PROTO_DIR := "./protobufs"

run:
	python -m cli
generate-proto:
	find $(PROTO_DIR) -iname "*.proto" -exec python -m grpc_tools.protoc -I $(PROTO_DIR) --python_out=. --pyi_out=. \
		--grpc_python_out=. {} \;
