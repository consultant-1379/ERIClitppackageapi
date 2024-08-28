from litp.migration import BaseMigration
from litp.migration.operations import AddProperty

class Migration(BaseMigration):
    version = '1.11.1'
    operations = [ AddProperty('package', 'epoch', '0'), ]
