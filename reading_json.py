from openmdao.lib.casehandlers.api import CaseDataset
import sys

cds = CaseDataset(sys.argv[1], 'json')
data = cds.data.fetch()

print cds.data.var_names().fetch()
print cds.data.vars(['paraboloid.x', 'paraboloid.y']).fetch()
