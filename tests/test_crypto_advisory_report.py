import unittest
import xml.etree.ElementTree as ET

from src.pipeline.crypto_advisory_report import html_edition,line_figure


class Tests(unittest.TestCase):
    def test_sharable_report_embeds_chart_and_escapes_source(self):
        source='# A < B\n\n| A | B |\n|---|---|\n| x | y |\n\n![Figure](../figures/x.svg)'
        result=html_edition(source,{'x.svg':'<svg role="img"></svg>'})
        self.assertIn('A &lt; B',result)
        self.assertIn('<svg role="img">',result)
        self.assertNotIn('src="../',result)
        self.assertEqual(result.count('<table>'),result.count('</table>'))

    def test_chart_uses_actual_date_labels(self):
        svg=line_figure('Title','Subtitle',{'SPY':[100,95,105]},'Wealth',start_label='2026-01-01',end_label='2026-02-01')
        ET.fromstring(svg)
        self.assertIn('2026-01-01',svg)
        self.assertIn('2026-02-01',svg)


if __name__=='__main__':unittest.main()
