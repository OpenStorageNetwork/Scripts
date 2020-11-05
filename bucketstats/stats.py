import subprocess
import json
import socket

pod = socket.gethostname()[:4]

out = subprocess.Popen(['radosgw-admin', '--format=json', 'buckets', 'list'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
stdout,stderr = out.communicate()
stats = json.loads(stdout)

cmdarry = ['radosgw-admin', '--format=json', '', 'bucket', 'stats']
bstats = {}
for bucket in stats:
	cmdarry[2] = "-b=%s" % (bucket)
	out = subprocess.Popen(cmdarry, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)	
	stdout,stderr = out.communicate()
	info = json.loads(stdout)
	bstats[info['bucket']] = info

print("Pod,Bucket,Owner,Quota Enabled, Max Size, Max Objects, Total Usage")
for k,v in bstats.iteritems():
	total = 0
	for pool, usage in v['usage'].iteritems():
		total += usage['size_actual']
	total /= 1E9 
	quota_info = v['bucket_quota']
	print("%s,%s,%s,%s,%s,%s,%s" % (pod,v['bucket'], v['owner'], quota_info['enabled'], quota_info['max_size'], quota_info['max_objects'], total))
