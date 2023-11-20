
mkfile_path:= $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir:= $(dir $(mkfile_path))


build-NaclBlockListUpdateLambda: 
ifeq ($(OS), Windows_NT)
	copy "$(mkfile_dir)src/index.py" "$(ARTIFACTS_DIR)"
else
	cp "$(mkfile_dir)src/index.py" "$(ARTIFACTS_DIR)"
endif
