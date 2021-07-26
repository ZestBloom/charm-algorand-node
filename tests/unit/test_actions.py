import yaml
import unittest

from pathlib import Path

class CharmTestCase(unittest.TestCase):

    def setUp(self, obj, patches):
        super(CharmTestCase, self).setUp()
        self.patches = patches
        self.obj = obj

        # Make default config available
        with open(Path("./config.yaml"), "r") as config_file:
            config = yaml.safe_load(config_file)

        self.charm_config = config
        # self.test_relation = TestRelation()
        self.patch_all()

    def patch(self, method):
        _m = mock.patch.object(self.obj, method)
        mock = _m.start()
        self.addCleanup(_m.stop)
        return mock

    def patch_all(self):
        for method in self.patches:
            setattr(self, method, self.patch(method))