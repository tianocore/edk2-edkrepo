from common.common_repo_functions import create_local_branch
from edkrepo_manifest_parser.edk_manifest import ManifestXml
from git import Repo
import os

manifest = ManifestXml("Manifest.xml")
patchset = manifest.get_patchset("test")
repo = Repo("C:\\Users\\harshvor\\src\\edk2-edkrepo\\")
create_local_branch("test", patchset, "C:\\Users\\harshvor\\src\\edk2-edkrepo", manifest, repo)
