import unittest
from unittest import TestCase

import log_analyzer


class TestLogAnalyzer(TestCase):

    def test_get_url(self):
        line = '1.138.198.128 -  - [30/Jun/2017:03:28:20 +0300] "GET /api/v2/banner/25100820 HTTP/1.1" 200 1294 "-" "python-requests/2.8.1" "-" "1498782499-440360380-4707-10488693" "4e9627334" 0.634'
        result, parsed = log_analyzer.get_url(line)
        self.assertEqual(result, "/api/v2/banner/25100820")
        self.assertTrue(parsed)

        line = '1.202.56.176 -  - [30/Jun/2017:03:20:14 +0300] "0" 400 166 "-" "-" "-" "-" "-" 0.000'
        result, parsed = log_analyzer.get_url(line)
        self.assertFalse(parsed)

    def test_get_date_from_postfix(self):
        filename = 'log_analyzer\\log\\nginx-access-ui.log-20170630.gz'
        result = log_analyzer.get_date_from_postfix(filename)
        self.assertEqual(result, '20170630')

        filename = 'log_analyzer\\log\\nginx-access-ui.log'
        result = log_analyzer.get_date_from_postfix(filename)
        print(result)
        self.assertEqual(result, "")

    def test_collect_statistics(self):
        data_gen = iter([("1", 1, 1, 0), ("2", 1, 2, 0), ("3", 1, 3, 0), ("2", 2, 4, 0), ("3", 2, 5, 0), ("3", 3, 6, 0)])
        result = log_analyzer.collect_statistics(data_gen)
        result = sorted(result, key=lambda x: x['url'])
        self.assertAlmostEqual(result[0]["time_sum"], 1, 4)
        self.assertAlmostEqual(result[1]['time_med'], 1.5, 4)
        self.assertAlmostEqual(result[2]['count'], 3, 4)
        self.assertAlmostEqual(sum(map(lambda x: x['time_perc'], result)), 100, 1, "sum of percent is not a 100")

    def test_get_duration(self):
        line = '1.138.198.128 -  - [30/Jun/2017:03:28:20 +0300] "GET /api/v2/banner/25100820 HTTP/1.1" 200 1294 "-" "python-requests/2.8.1" "-" "1498782499-440360380-4707-10488693" "4e9627334" 0.634'
        result, parsed = log_analyzer.get_duration(line)
        self.assertAlmostEqual(result, 0.634, 4)


if __name__ == '__main__':
    unittest.main()

