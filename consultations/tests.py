from django.test import SimpleTestCase

from consultations.views import _split_items


class SplitItemsTests(SimpleTestCase):
	def test_split_items_returns_empty_list_for_none(self):
		self.assertEqual(_split_items(None), [])

	def test_split_items_returns_empty_list_for_empty_string(self):
		self.assertEqual(_split_items(''), [])

	def test_split_items_parses_comma_and_newline_values(self):
		raw_value = 'cbc, x-ray\n  mri  \n\n urinalysis '
		self.assertEqual(_split_items(raw_value), ['cbc', 'x-ray', 'mri', 'urinalysis'])

