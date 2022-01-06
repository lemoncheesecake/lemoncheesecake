#!/usr/bin/env python3

import os
import os.path as osp
import sys
import shutil
import glob


if os.system("yarn build") != 0:
    sys.exit(1)

dst_dir = osp.join("..", "lemoncheesecake", "resources", "html")

shutil.copy(
    glob.glob(osp.join("build", "static", "js", "main.*.js"))[0],
    osp.join(dst_dir, "report.js")
)
shutil.copy(
    glob.glob(osp.join("build", "static", "css", "main.*.css"))[0],
    osp.join(dst_dir, "report.css")
)

print("Copied JS and CSS files into %s" % dst_dir)
