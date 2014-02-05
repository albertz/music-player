#!/usr/bin/env python

import sys, os

assert sys.argv[1] == "-in"
txt = open(sys.argv[2], "r").read()
assert sys.argv[3] == "-out"
outfile = open(sys.argv[4], "w")
assert sys.argv[5] == "-qmake"

# Atm, we get: top_srcdir top_builddir TARGET PWD AppSignature QMAKE_MACOSX_DEPLOYMENT_TARGET
qmakeVars = {}
for arg in sys.argv[6:]:
	varname, varvalue = arg.split("=", 1)
	qmakeVars[varname] = varvalue

replaceMap = {
	"EXECUTABLE_NAME": qmakeVars["TARGET"],
	"PRODUCT_NAME:rfc1034identifier": qmakeVars["TARGET"],
	"PRODUCT_NAME": qmakeVars["TARGET"],
	"MACOSX_DEPLOYMENT_TARGET": qmakeVars["QMAKE_MACOSX_DEPLOYMENT_TARGET"]
}

import re

while True:
	m = re.search("\${([:_\w]*)}", txt)
	if not m: break
	
	replaceStr = replaceMap[m.group(1)]
	txt = txt[:m.start()] + replaceStr + txt[m.end():]

# Special rule for signature
txt = txt.replace(">????<", ">%s<" % qmakeVars["AppSignature"])

outfile.write(txt)
outfile.close()
