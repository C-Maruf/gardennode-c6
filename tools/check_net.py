import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, find, find1
from design import nets
t = parse(open(sys.argv[1]).read())[0]
got = {}
for n in find(find1(t, 'nets'), 'net'):
    name = find1(n, 'name')[1].lstrip('/')
    nodes = {(find1(x, 'ref')[1], find1(x, 'pin')[1]) for x in find(n, 'node') if not find1(x, 'ref')[1].startswith('#')}
    if nodes: got[name] = nodes
exp = {k: set(v) for k, v in nets().items()}
bad = 0
for k in sorted(set(exp) | set(got)):
    if exp.get(k) != got.get(k):
        bad += 1; print('MISMATCH', k, 'exp-only', exp.get(k, set()) - got.get(k, set()), 'sch-only', got.get(k, set()) - exp.get(k, set()))
print('nets expected', len(exp), 'schematic', len(got), 'mismatches', bad)
