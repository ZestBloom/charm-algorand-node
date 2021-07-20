import unittest
import zaza.model


class TestBase(unittest.TestCase):
    """ Base class for functional charm tests. """

    @classmethod
    def setUpClass(cls):
        """ Run setup for tests. """
        cls.model_name = zaza.model.get_juju_model()
        cls.application_name = "algorand-node"

class TestNode(TestBase):
    def test_01_noop(self):
        pass
