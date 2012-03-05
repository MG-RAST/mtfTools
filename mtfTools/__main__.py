#!/usr/bin/env python
import os, sys, json, shutil
import argparse
import prettytable as pt
from progressbar import Counter, ProgressBar, Timer

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

def mtfpath_type(mtfpath):
	if mtfpath.count("/") > 0:
		[mtf, rest] = mtfpath.split("/", 1)
		if mtf_type(mtf) == mtf:
			return mtfpath
	else:
		return mtf_type(mtfpath)

def mtf_type(mtf):
	global MTFPATH	
	mtfCache = loadMtf()
	if mtfCache.has_key(mtf):
		return mtf
	else:
		msg = "%s not found in MTFPATH. MTFPATH includes %s" % (mtf, MTFPATH)
		raise argparse.ArgumentTypeError(msg)		

# setup option/arg parser
parser = argparse.ArgumentParser(prog='mtf', epilog='Use "mtf command -h" for more information about a command.')
parser.add_argument('--MTFPATH', help='Overrules env variable MTFPATH')
subparsers = parser.add_subparsers(dest='command', title='The commands are')

# init -h
p_init = subparsers.add_parser('init', description='Manually rebuilds cache file. Maybe useful after updates.', help='manually rebuilds cache file')

# list -h
p_list = subparsers.add_parser('list', description='Lists the mtf(s) available in MTFPATH or the contents of a mtf.', help='list available metagenomes')
p_list.add_argument('mtfId', type=mtf_type, nargs='?',help='')
p_list.add_argument('-p', action='store_true', help='disables pretty print for ease of parsing and use with other command line utilities')

# get -h
p_get = subparsers.add_parser('get', help='get all or partial selection of a metagenome\'s files')
p_get.add_argument('--decompress', action='store_true', help='decompress file(s)')
p_get.add_argument('mtf', type=mtfpath_type, help='source mtf or mtf/file')
p_get.add_argument('target_dir', type=dir_type, help='target directory to copy file(s) to')

# replace -h
p_replace = subparsers.add_parser('replace-spec', description="Replaces mtf spec file or provider spec file.", help='replace mtf spec file or provider spec file')
p_replace.add_argument('source_spec', type=file_type, help='source mtf spec file or provider spec file')

# add -h
p_add = subparsers.add_parser('add-provider', description="Adds provider spec file to a mtf.", help='add new provider')
p_add.add_argument('source_spec', type=file_type, help='provider spec file to be added to mtf')
	
'''
Old version of the code I'm not fully willing to give up yet.

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
		args[0][bn] = {}
		args[0][bn]["path"] = dirname
		args[0][bn]["metadata"] = []
		args[0][bn]["providers"] = {}
		for f in filenames:			
			if f == "%s.spec" % bn:
				fileCount += 1
				args[0][bn]["spec"] = parseSpec("%s/%s" % (dirname, f))
			elif "metadata" in f.split("."):
				fileCount += 1
				args[0][bn]["metadata"].append(f)
		for r, rv in args[0][bn]["spec"]["raw"].iteritems():
			if rv.has_key("size") and rv["size"]:
				size += int(rv["size"])
		for p in args[0][bn]["spec"]["providers"]:
			spec = parseSpec("%s/providers/%s.spec" % (dirname, p))
			args[0][bn]["providers"][p] = {"files" : spec["files"]}
			for f, fv in spec["files"].iteritems():
				if fv.has_key("size") and fv["size"]:
					size += int(fv["size"])
				fileCount += 1
		args[0][bn]["fileCount"] = fileCount
		args[0][bn]["size"] = size
		args[2] += 1	
		args[1].update(args[2])
'''	

def parseSpec(filename):
	specFile = open(filename, 'rU')
	spec = json.load(specFile)
	size = 0
	fcount = 0
	for r, rv in spec["raw"].iteritems():
		fcount += 1
		if rv.has_key("size") and rv["size"]:
			size += int(rv["size"])
	for p, pv in spec["providers"].iteritems():
		for f, fv in pv["files"].iteritems():
			fcount += 1	
			if fv.has_key("size") and fv["size"]:
				size += int(fv["size"])
	spec["size"] = size
	spec["fileCount"] = fcount
	specFile.close()
	return spec	
					
def loadMtf(fromDir=False):
	global MTFPATH
	mtfCache = {}
	if not os.path.exists("%s/mtf.cache.json" % MTFPATH) or fromDir:
		print "Building cache file. This should be quick..."		
		pbar = ProgressBar(widgets=['Processed: ', Counter(), ' specs (', Timer(), ')'], maxval=1000000).start()
		
		#args = [mtfCache, pbar, 0]
		#os.path.walk(MTFPATH, parseMtf, args)
		count = 0
		for s in os.listdir("%s/spec" % MTFPATH):
			count += 1
			spec = parseSpec("%s/spec/%s"  % (MTFPATH, s))
			mtfCache[spec["id"]] = spec
			pbar.update(count)
			
		pbar.maxval = count
		pbar.finish()
		cacheFile = open("%s/mtf.cache.json" % MTFPATH, 'w')
		cacheFile.write(json.dumps(mtfCache))
		cacheFile.close()		
	else:
		cacheFile = open("%s/mtf.cache.json" % MTFPATH, 'rU')
		mtfCache = json.load(cacheFile)
		cacheFile.close()
	return mtfCache	

def performGet(toDo):
	global MTFPATH
	path = "%s/%s" % (toDo["path"], toDo["id"])
	print "mkdir: %s" % path
	#os.mkdir(path)

	for d in toDo["mkdir"]:
		print "mkdir: %s/%s" % (path, d)
		#os.mkdir("%s/%s" % (path, d))

	for f in toDo["copy"]:
		#print f
		des = "%s/%s" % (path, f[0])
		if f[2]:
			des = "%s/%s/%s" % (path, f[2], f[0])
		print "copy: %s/%s to %s" % (MTFPATH, f[0], des)
		#shutil.copyfile("%s/%s" % (toDo["mtf"]["path"], f[0]), des)

	for f in toDo["download"]:
		print "download: %s to %s/%s/%s" % (f[2], path, f[1], f[0])	
		
		
def convert_bytes(n):
    K, M, G, T = 1 << 10, 1 << 20, 1 << 30, 1 << 40
    if   n >= T:
        return '%.1fT' % (float(n) / T)
    elif n >= G:
        return '%.1fG' % (float(n) / G)
    elif n >= M:
        return '%.1fM' % (float(n) / M)
    elif n >= K:
        return '%.1fK' % (float(n) / K)
    else:
        return '%d' % n


def main():
	global MTFPATH
	args = parser.parse_args()

	if args.MTFPATH:
		MTFPATH = args.MTFPATH
				
	if not MTFPATH:
		print parser.print_usage()
		print "mtf: err: MTFPATH not set"
		sys.exit()

	#print args
	if args.command == "init":
		if os.path.exists("%s/mtf.cache.json" % MTFPATH):
			os.unlink("%s/mtf.cache.json" % MTFPATH)	
		mtfCache = loadMtf(True)
		
	elif args.command == "list":
		mtfCache = loadMtf()
		table = ""
		if not args.mtfId:
			table = pt.PrettyTable(["id", "providers", "file count", "size"])
			table.set_field_align("id", "l")			
			table.set_field_align("size", "r")
			for k, v in mtfCache.iteritems():
				table.add_row([k, ", ".join(v["providers"].keys()), v["fileCount"], convert_bytes(v["size"])])
		else:
			mtf = mtfCache[args.mtfId]
			table = pt.PrettyTable(["file", "size", "format", "compression", "url"])
			table.set_field_align("file", "l")
			table.set_field_align("size", "r")
			table.set_field_align("format", "l")
			table.set_field_align("url", "l")			
			table.add_row(["%s.spec" % args.mtfId, "", "spec", "", ""])
			for i in mtf["metadata"]:
				table.add_row([i, "", "json","", ""])			
			if mtf.has_key("raw"):
				for r, rv in mtf["raw"].iteritems():
					size = convert_bytes(rv["size"]) if rv.has_key("size") else "n/a"
					table.add_row(["raw/%s" % r, size, "fasta", (rv["compression"] or ""), (rv["url"] or "")])	
			for p, v in sorted(mtf["providers"].iteritems()):
				for f, fv in sorted(v["files"].iteritems()):
					size = convert_bytes(fv["size"]) if fv.has_key("size") else "n/a"
					table.add_row(["%s/%s" % (p, f), size, fv["type"], (fv["compression"] or ""), (fv["url"] or "")])								
		print table	
		
	elif args.command == "get":
		mtfCache = loadMtf()
	 	toDo= {"id" : None, "mtf" : None, "path" : args.target_dir, "mkdir" : [], "download" : [], "copy" : []}
		if args.mtf.count("/") > 0:
			if args.mtf.count("/") == 1:
				[toDo["id"], rest] = args.mtf.split("/")
				toDo["mtf"] = mtfCache[toDo["id"]]
				if rest == "raw":
					toDo["mkdir"].append("raw")
					for f, v in toDo["mtf"]["raw"].iteritems():
						toDo["download"].append([f, "raw", v["url"]])
				elif rest in toDo["mtf"]["providers"].keys():
					toDo["mkdir"].append(rest)
					for f, v in toDo["mtf"]["providers"][rest]["files"].iteritems():
						toDo["download"].append([f, rest, v["url"]])
				elif "spec" in rest.split(".") or "metadata" in rest.split("."):
					toDo["copy"].append([rest, rest,""])
			elif args.mtf.count("/") == 2:
				[toDo["id"], d, f] = args.mtf.split("/")
				toDo["mtf"] = mtfCache[toDo["id"]]
				if d == "raw" and f in toDo["mtf"]["raw"].keys():
					toDo["mkdir"].append("raw")
					toDo["download"].append([f, "raw", toDo["mtf"]["raw"][f]["url"]])
				elif d in toDo["mtf"]["providers"].keys():
					toDo["mkdir"].append(d)
					if f in toDo["mtf"]["providers"][d]["files"].keys():
						toDo["download"].append([f, d, toDo["mtf"]["providers"][d]["files"][f]["url"]])
					
			elif args.mtf.count("/") > 2:
				# error?
				print "invalid mtf path"
				pass
		else:
			toDo["id"] = args.mtf
			toDo["mtf"] = mtfCache[toDo["id"]]
			toDo["copy"].append(["%s.spec" % toDo["id"] , "%s.spec" % toDo["id"], ""])
			toDo["mkdir"].append("raw")			
			for m in toDo["mtf"]["metadata"]:
				toDo["copy"].append([m, m, ""])
			for r, rv in toDo["mtf"]["raw"].iteritems():
				toDo["download"].append([r, "raw", rv["url"]])
			for p, pv in toDo["mtf"]["providers"].iteritems():
				toDo["mkdir"].append(p)
				for f, fv in pv["files"].iteritems():
					toDo["download"].append([f, p, fv["url"]])
						
		#toDo["mtf"] = None
		#print toDo
		performGet(toDo)
		#mtf = mtfCache[mtfId]
		#print mtf
		
		# u = urllib.urlopen("http://api.metagenomics.anl.gov/Metagenome/%s" % (mgid))
		# u.read()

	elif args.command == "replace-spec":
		print "Not implemented yet."
	elif args.command == "add-provider":
		print "Not implemented yet."
		
	sys.exit()

if __name__ == '__main__':
    main()
