#!/usr/bin/env python

import os, sys, json
import argparse
import prettytable as pt

# set mtfPath
MTFPATH = os.getenv("MTFPATH")

# arg type checking
def file_type(f):
	if not os.path.isfile(f):
		msg = "%s is not a file" % f
		raise argparse.ArgumentTypeError(msg)
	else:
		return f

def dir_type(d):
	if not os.path.isdir(d):
		msg = "%s is not a directory" % d
		raise argparse.ArgumentTypeError(msg)
	else:
		return d

def mtf_type(mtf):
	if not os.path.isdir(mtf):
		msg = "%s not found. Check environment variable MTFPATH or --MTFPATH." % mtf
		raise argparse.ArgumentTypeError(msg)
	else:
		return mtf

def valid_mtf(mtf):
	return true

# setup option/arg parser
parser = argparse.ArgumentParser(prog='mtf', epilog='Use "mtf command -h" for more information about a command.')
parser.add_argument('--MTFPATH', help='Overrules env variable MTFPATH')
subparsers = parser.add_subparsers(dest='command', title='The commands are')

# init -h
p_init = subparsers.add_parser('init', description='Manually rebuilds cache file. Maybe useful after updates.', help='manually rebuilds cache file')

# list -h
p_list = subparsers.add_parser('list', description='Lists the mtf(s) available in MTFPATH or the contents of a mtf.', help='list available metagenomes')
p_list.add_argument('mtfId', nargs='?',help='')
p_list.add_argument('-p', action='store_true', help='disables pretty print for ease of parsing and use with other command line utilities')

# get -h
p_get = subparsers.add_parser('get', help='get all or partial selection of a metagenome\'s files')
p_get.add_argument('--decompress', action='store_true', help='decompress file(s)')
p_get.add_argument('source_mtf', help='source mtf or mtf/file')
p_get.add_argument('target_dir', type=dir_type, help='target directory to copy file(s) to')

# replace -h
p_replace = subparsers.add_parser('replace-spec', description="Replaces mtf spec file or provider spec file.", help='replace mtf spec file or provider spec file')
p_replace.add_argument('source_spec', type=file_type, help='source mtf spec file or provider spec file')

# add -h
p_add = subparsers.add_parser('add-provider', description="Adds provider spec file to a mtf.", help='add new provider')
p_add.add_argument('source_spec', type=file_type, help='provider spec file to be added to mtf')

def parseSpec(filename):
	specFile = open(filename, 'rU')
	spec = json.load(specFile)
	specFile.close()
	return spec
		
def parseMtf(args, dirname, filenames):
	if "providers" in dirname.split('/'):
		return
	bn = os.path.basename(dirname)
	if "%s.spec" % bn in filenames:
		fileCount = 0
		size = 0
		args[bn] = {}
		args[bn]["path"] = dirname
		args[bn]["metadata"] = []
		args[bn]["providers"] = {}
		for f in filenames:			
			if f == "%s.spec" % bn:
				fileCount += 1
				args[bn]["spec"] = parseSpec("%s/%s" % (dirname, f))
			elif "metadata" in f.split("."):
				fileCount += 1
				args[bn]["metadata"].append(f)
		for p in os.listdir("%s/providers" % dirname):
			spec = parseSpec("%s/providers/%s/%s.spec" % (dirname, p, p))
			args[bn]["providers"][p] = {"files" : spec["files"]}
			fileCount += len(spec["files"])
		args[bn]["fileCount"] = fileCount
		args[bn]["size"] = size
			
def loadMtf(fromDir=False):
	global MTFPATH
	mtfCache = {}
	if fromDir:
		os.path.walk(MTFPATH, parseMtf, mtfCache)		
	else:
		cacheFile = open("%s/mtf.cache.json" % MTFPATH, 'rU')
		mtfCache = json.load(cacheFile)
		cacheFile.close()
	return mtfCache	
			
def main():
	global MTFPATH
	args = parser.parse_args()

	if args.MTFPATH:
		MTFPATH = args.MTFPATH
				
	if not MTFPATH:
		print parser.print_usage()
		print "mtf: err: MTFPATH not set"
		sys.exit()

	print args
	if args.command == "init":
		if os.path.exists("%s/mtf.cache.json" % MTFPATH):
			os.unlink("%s/mtf.cache.json" % MTFPATH)	
		mtfCache = loadMtf(True)
		cacheFile = open("%s/mtf.cache.json" % MTFPATH, 'w')
		cacheFile.write(json.dumps(mtfCache))
		cacheFile.close()
		print len(mtfCache)
		
	elif args.command == "list":
		mtfCache = loadMtf()
		table = ""
		if not args.mtfId:
			table = pt.PrettyTable(["id", "providers", "file count", "size"])
			table.set_field_align("id", "l")			
			for k, v in mtfCache.iteritems():
				print v.keys()
				table.add_row([k, ", ".join(v["providers"]), v["fileCount"], "10GB"])
		else:
			mtf = mtfCache[args.mtfId]
			table = pt.PrettyTable(["file", "size", "format", "compression", "url"])
			table.set_field_align("file", "l")
			table.set_field_align("format", "l")
			table.set_field_align("url", "l")			
			table.add_row(["%s.spec" % args.mtfId, "", "spec", "", ""])
			for i in mtf["metadata"]:
				table.add_row([i, "", "json","", ""])
			for r, rv in mtf["spec"]["sequences"].iteritems():
				table.add_row(["raw/%s" % r, "", "fasta", (rv["compression"] or ""), (rv["url"] or "")])	
			for p, v in sorted(mtf["providers"].iteritems()):
				table.add_row(["%s/%s.spec" % (p, p), "", "spec", "", ""])
				for f, fv in sorted(v["files"].iteritems()):
					table.add_row(["%s/%s" % (p, f), "", "fasta", (fv["compression"] or ""), (fv["url"] or "")])
				
		print table	
	elif args.command == "get":
		pass
	elif args.command == "replace-spec":
		pass
	elif args.command == "add-provider":
		pass
		
	sys.exit()

if __name__ == '__main__':
    main()
