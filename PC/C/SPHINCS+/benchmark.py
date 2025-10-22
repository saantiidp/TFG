#! /usr/bin/env python3
import fileinput
import itertools
import os
import sys
from subprocess import DEVNULL, run

implementations = [
                   ('ref', ['sha2']), #'shake', 
                   ('shake-avx2', ['shake']),
                   ('sha2-avx2', ['sha2']),
                   ]

options = ["f", "s"]
sizes = [128, 192, 256]
thashes = ['simple']

for impl, fns in implementations:
    params = os.path.join(impl, "params.h")
    for fn in fns:
        for opt, size, thash in itertools.product(options, sizes, thashes):
            paramset = "sphincs-{}-{}{}".format(fn, size, opt)
            paramfile = "params-{}.h".format(paramset)

            print("Benchmarking", paramset, thash, "using", impl, flush=True)

            params = 'PARAMS={}'.format(paramset)  # overrides Makefile var
            thash = 'THASH={}'.format(thash)  # overrides Makefile var
            
            #Inicialmente sin /usr/bin/time
            run(["/usr/bin/time", "-v", "make", "-C", impl, "clean", thash, params],
                stdout=DEVNULL, stderr=sys.stderr)
            run(["/usr/bin/time", "-v", "make", "-C", impl, "benchmarks", thash, params],
                stdout=DEVNULL, stderr=sys.stderr)
            run(["/usr/bin/time", "-v", "make", "-C", impl, "benchmark", thash, params],
                stdout=sys.stdout, stderr=sys.stderr)

            print(flush=True)

