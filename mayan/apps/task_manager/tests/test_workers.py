from django.test import SimpleTestCase

from ..classes import Worker


class WorkerMemoryLimitTestCase(SimpleTestCase):
    """The limit is in KiB, the unit of the Celery option."""

    def _get_worker(self, **kwargs):
        worker = Worker(name='_test_worker_memory', **kwargs)
        self.addCleanup(Worker._registry.pop, '_test_worker_memory')
        return worker

    def test_limit_is_displayed_from_kib(self):
        worker = self._get_worker(maximum_memory_per_child=500000)
        self.assertEqual(
            worker.get_maximum_memory_per_child().replace('\xa0', ' '),
            '488.3 MB'
        )

    def test_worker_without_limit(self):
        worker = self._get_worker()
        self.assertEqual(
            worker.get_maximum_memory_per_child().replace('\xa0', ' '),
            '0 bytes'
        )
