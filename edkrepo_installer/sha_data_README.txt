Note: sha_data.cfg is used to determine if the edkrepo.cfg file should be upgraded or not.
Only if the hash of the older edkrepo.cfg file matches this hash, and the newer edkrepo.cfg
file bundled in the installer does NOT match this hash will we replace the config file

one can compute the hash of the edkrepo.cfg file using the following command in git bash
cat edkrepo.cfg | sha256sum
