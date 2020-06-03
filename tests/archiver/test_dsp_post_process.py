from unittest import TestCase

from archiver.dsp_post_process import dsp_attribute


class TestPostProcessing(TestCase):

    def test_dsp_attribute(self):
        # given:
        string_attribute = dsp_attribute('name')
        numeric_attribute = dsp_attribute(28)

        # expect:
        self.assertEqual(1, len(string_attribute))
        self.assertEqual('name', string_attribute[0].get('value'))

        # and:
        self.assertEqual(1, len(numeric_attribute))
        self.assertEqual(28, numeric_attribute[0].get('value'))

        # and:
        self.assertIsNone(dsp_attribute(None))
