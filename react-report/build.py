#!/usr/bin/env python2

import os
import os.path as osp
import sys
import shutil
import glob


if os.system("npm run build") != 0:
    sys.exit(1)

js_src_filename = glob.glob(osp.join("build", "static", "js", "main.*.js"))[0]
js_dst_filename = osp.join("..", "lemoncheesecake", "resources", "html", "report.js")
print "Copy %s into %s" % (js_src_filename, js_dst_filename)
shutil.copy(js_src_filename, js_dst_filename)
