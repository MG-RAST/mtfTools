#! /usr/bin/env python
import json, urllib, sys, os, shutil
import md5

# picking example project
#func= "Thr operon leader peptide"
#params = urllib.urlencode({'annotation': func, "type" : "function"})
# u = urllib.urlopen("http://api.metagenomics.anl.gov/query/?%s" % params)

root="./mtf"
shutil.rmtree(root)
os.mkdir(root)

provider="metagenomics.anl.gov"
apiUrl="api.metagenomics.anl.gov"

def mkdirMtf(id):
	checksum = md5.new(id).hexdigest()
	path = "%s/%s/%s/%s/%s" % (root, checksum[0:2], checksum[2:4], checksum[4:6], id)
	os.makedirs(path)
	os.mkdir("%s/providers" % (path))
	return path

def mkdirMtfProvider(path, provider):
	os.mkdir("%s/providers/%s" % (path, provider))
			
# grab all metagenomes 
u = urllib.urlopen("http://api.metagenomics.anl.gov/Metagenome/")
response = json.loads(u.read())
for mgid in response["metagenomes"]:	
	u = urllib.urlopen("http://api.metagenomics.anl.gov/Metagenome/%s" % (mgid))
	mg = json.loads(u.read())	
	u = urllib.urlopen("http://api.metagenomics.anl.gov/SequenceSet/%s" % (mgid))
	mgFiles = json.loads(u.read())	

	spec = {
		"id" : mgid,
		"metadata" : {
			"%s.metadata.json" % mgid : { "format" : "json", "provider" : provider }, 
		},
		"sequences" : { "%s.fna.gz" % mgid : { "format" : "fasta", "compression" : "gzip", "provider" : provider, "url" : "http://%s/reads/%s" % (apiUrl, mgid) }},
		"providers" : [provider]
	}
	
	providerSpec = {
		"id" : mgid,
		"provider" : provider,
		"providerId" : mgid,
		"files" : {},
		"formats" : {
			"mgrast-info" : { "specification" : "http://metagenomics.anl.gov/mtf/specifications#mgrast-info" },			
			"mgrast-gcs" : { "specification" : "http://metagenomics.anl.gov/mtf/specifications#mgrast-gcs"	},
			"mgrast-stats" : { "specification" : "http://metagenomics.anl.gov/mtf/specifications#mgrast-stats" }			
		}
	}
	
	for f in mgFiles:
		providerSpec["files"][f["file_name"]] = {
			"stage_name" : f["stage_name"],
			"url" : "http://%s/SequenceSet/%s" % (apiUrl, f["id"])
		}
		if f["file_name"][-2:] == "gz":
			providerSpec["files"][f["file_name"]]["compression"] = "gzip" 			
	
	print mgid
	path = mkdirMtf(mgid)
	mkdirMtfProvider(path, provider)
	
	specFile = open("%s/%s.spec" % (path, mgid), 'w')	
	metadataFile = open("%s/%s.metadata.json" % (path, mgid), 'w')
	providerSpecFile = open("%s/providers/%s/%s.spec" % (path, provider, provider), 'w')

	specFile.write(json.dumps(spec, sort_keys=True, indent=4))
	metadataFile.write(json.dumps(mg["metadata"], sort_keys=True, indent=4))
	providerSpecFile.write(json.dumps(providerSpec, sort_keys=True, indent=4))
	
	specFile.close()
	metadataFile.close()
	providerSpecFile.close()