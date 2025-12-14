import unittest
from edkrepo_manifest_parser import edk_manifest

INPUT_MANIFEST_FILE = 'test_manifest.xml'

class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.manifest = edk_manifest.ManifestXml(INPUT_MANIFEST_FILE)

    def test_parse_project_info(self):
        self.assertEquals(self.manifest.project_info.codename, 'Edk2TestProject')
        self.assertEquals(self.manifest.project_info.description, 'Test Project')
        self.assertEquals(self.manifest.project_info.dev_leads, ['kevin.sun@intel.com', 'ashley.e.desimone@intel.com'])
        self.assertEquals(self.manifest.project_info.reviewers, ['nathaniel.l.desimone@intel.com', 'erik.c.bjorge@intel.com'])
        self.assertEquals(self.manifest.project_info.org, 'TianoCore')
        self.assertEquals(self.manifest.project_info.short_name, 'EDKII')

    def test_parse_general_config(self):
        self.assertEquals(self.manifest.general_config.default_combo, 'main')
        self.assertEquals(self.manifest.general_config.current_combo, 'main')
        self.assertEquals(self.manifest.general_config.pin_path, 'test/pins')
        self.assertEquals(self.manifest.general_config.source_manifest_repo, None)

    def test_parse_remotes(self):
        [remote_a, remote_b] = self.manifest.remotes
        self.assertEquals(remote_a.name, 'Edk2Repo')
        self.assertEquals(remote_a.url, 'https://github.com/tianocore/edk2.git')
        self.assertEquals(remote_b.name, 'Edk2Platforms')
        self.assertEquals(remote_b.url, 'https://github.com/tianocore/edk2-platforms.git')

    def test_parse_combinations(self):
        combo = self.manifest.combinations[0]
        self.assertEquals(combo.name, 'main')
        self.assertEquals(combo.description, 'Main Combo')
        self.assertFalse(combo.venv_enable)

    def test_parse_githooks(self):
        [githook_a, githook_b] = self.manifest.repo_hooks
        self.assertEquals(githook_a.source, 'hooks/hook-wrapper')
        self.assertEquals(githook_a.dest_path, '.git/hooks')
        self.assertEquals(githook_a.dest_file, 'hooks/pre-push')
        self.assertEquals(githook_a.remote_url, 'https://github.com/tianocore/edk2.git')
        self.assertEquals(githook_b.source, 'hooks/hook-wrapper')
        self.assertEquals(githook_b.dest_path, '.git/hooks')
        self.assertEquals(githook_b.dest_file, 'hooks/pre-commit')
        self.assertEquals(githook_b.remote_url, 'https://github.com/tianocore/edk2.git')

    def test_parse_dsc_list(self):
        dsc = self.manifest.dsc_list[0]
        self.assertEquals(dsc, 'Edk2/IntelFsp2Pkg/IntelFsp2Pkg.dsc')

    def test_parse_sparse_settings(self):
        self.assertTrue(self.manifest.sparse_settings.sparse_by_default)

    def test_parse_sparse_data(self):
        sparse_data = self.manifest.sparse_data[0]
        self.assertEquals(sparse_data.combination, None)
        self.assertEquals(sparse_data.remote_name, 'Edk2Repo')
        self.assertEquals(sparse_data.always_include, ['*.*'])
        self.assertEquals(sparse_data.always_exclude, ['UnitTestFrameworkPkg'])

    def test_parse_folder_to_folder_mappings(self):
        f2f = self.manifest.folder_to_folder_mappings[0]
        [f2f_mapping_a, f2f_mapping_b] = f2f.folders

        self.assertEquals(f2f.project1, 'SRC')
        self.assertEquals(f2f.project2, 'DST')
        self.assertEquals(f2f.remote_name, 'remote')
        self.assertEquals(f2f_mapping_a.project1_folder, 'SrcFspPkg')
        self.assertEquals(f2f_mapping_a.project2_folder, 'DestFspPkg')
        self.assertEquals(f2f_mapping_a.excludes, [])
        self.assertEquals(f2f_mapping_b.project1_folder, 'SrcFspPkg/SrcFspPkg.dsc')
        self.assertEquals(f2f_mapping_b.project2_folder, 'DestFspPkg/DestFspPkg.dsc')
        self.assertEquals(f2f_mapping_b.excludes, [])

    def test_parse_current_combo(self):
        self.assertEquals(self.manifest.current_combo, 'main')

    def test_parse_commit_templates(self):
        self.assertEquals(self.manifest.commit_templates, {'Edk2Repo': 'Templates/template.txt'})

    def test_parse_submodule_alternate_remotes(self):
        submodule_redirect = self.manifest.submodule_alternate_remotes[0]
        self.assertEquals(submodule_redirect.remote_name, 'Edk2Repo')
        self.assertEquals(submodule_redirect.original_url, 'https://git.cryptomilk.org/projects/cmocka.git')
        self.assertEquals(submodule_redirect.alternate_url, 'https://github.com/tianocore/edk2-cmocka.git')


if __name__ == "__main__":
    unittest.main()
