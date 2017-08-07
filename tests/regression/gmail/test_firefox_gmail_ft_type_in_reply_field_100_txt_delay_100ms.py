from lib.perfBaseTest import PerfBaseTest


class TestSikuli(PerfBaseTest):

    def setUp(self):
        super(TestSikuli, self).setUp()
        self.set_configs(self.config_name.INDEX,
                         self.extract_platform_dep_settings(
                             {'win32': {'7': {'search-margin': 2, 'mismatch-rate-threshold': 0.005,
                                              'compare-threshold': 0.013},
                                        '10': {'search-margin': 2, 'mismatch-rate-threshold': 0.005,
                                               'compare-threshold': 0.013}}}))

    def test_firefox_gmail_ft_type_in_reply_field_100_txt_delay_100ms(self):
        self.test_url = self.global_config['gsuite']['gmail']['test-reply-url']

        self.round_status = self.sikuli.run_test(self.env.test_name,
                                                 self.env.output_name,
                                                 test_target=self.test_url,
                                                 script_dp=self.env.test_script_py_dp,
                                                 args_list=[self.env.img_sample_dp,
                                                            self.env.img_output_sample_1_fn,
                                                            self.env.DEFAULT_VIDEO_RECORDING_WIDTH,
                                                            self.env.DEFAULT_VIDEO_RECORDING_HEIGHT,
                                                            self.env.DEFAULT_TIMESTAMP])
