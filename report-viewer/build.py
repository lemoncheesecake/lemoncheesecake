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
shutil.copy(
    osp.join("node_modules", "bootstrap-icons", "font", "bootstrap-icons.css"),
    dst_dir
)
# The Bootstrap Icons fonts are handled outside the React app since controlling the font paths inside the built CSS
# is not (easily) feasible
shutil.copy(
    osp.join("node_modules", "bootstrap-icons", "font", "fonts", "bootstrap-icons.woff"),
    osp.join(dst_dir, "fonts")
)
shutil.copy(
    osp.join("node_modules", "bootstrap-icons", "font", "fonts", "bootstrap-icons.woff2"),
    osp.join(dst_dir, "fonts")
)

print("Copied JS, CSS and font files into %s" % dst_dir)
