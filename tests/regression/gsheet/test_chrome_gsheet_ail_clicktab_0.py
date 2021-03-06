from lib.perfBaseTest import PerfBaseTest


class TestSikuli(PerfBaseTest):

    def setUp(self):
        self.set_variable(test_target=self.global_config['gsuite']['gsheet-empty-number-enchar-2tabs'])
        super(TestSikuli, self).setUp()
        self.set_configs(self.config_name.INDEX,
                         self.extract_platform_dep_settings(
                             {'win32': {'7': {'search-margin': 2, 'compare-threshold': 0.008},
                                        '10': {'search-margin': 2, 'compare-threshold': 0.008}}}))

    def test_chrome_gsheet_ail_clicktab_0(self):
        self.round_status = self.sikuli.run_test(self.env.test_name, self.env.output_name, test_target=self.test_url,
                                                 script_dp=self.env.test_script_py_dp,
                                                 args_list=[self.env.img_sample_dp, self.env.img_output_sample_1_fn,
                                                            self.exec_config['video-recording-width'],
                                                            self.exec_config['video-recording-height'],
                                                            self.env.DEFAULT_TIMESTAMP])
