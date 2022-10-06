from uasyncio import run 
from tests import lens_test, switch_test, xb_test 

run(lens_test.LensTest(verbose = True).run_test(repeats=5))  
run(switch_test.SwitchTest(verbose = True).run_test(secs=20))
run(xb_test.xbTest(verbose = True).run_test(repeats=5)) 