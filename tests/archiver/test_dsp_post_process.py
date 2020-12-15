from unittest import TestCase

from archiver.dsp.converter.abstracts import BaseDspConverter


class TestPostProcessing(TestCase):

    def test_dsp_attribute(self):
        # given:
        string_attribute = BaseDspConverter.dsp_attribute('name')
        numeric_attribute = BaseDspConverter.dsp_attribute(28)
        falsy_attribute = BaseDspConverter.dsp_attribute(0)

        # expect:
        self.assertEqual(1, len(string_attribute))
        self.assertEqual('name', string_attribute[0].get('value'))

        # and:
        self.assertEqual(1, len(numeric_attribute))
        self.assertEqual(28, numeric_attribute[0].get('value'))

        # and:
        self.assertEqual(1, len(falsy_attribute))
        self.assertEqual(0, falsy_attribute[0].get('value'))

        # and:
        self.assertIsNone(BaseDspConverter.dsp_attribute(None))
