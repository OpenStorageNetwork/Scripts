#!/home/ansible/seans-NCSA/boto-test/bin/python3

from subprocess import Popen, PIPE
import os
import shlex
import argparse
import boto3
import botocore
#boto3.set_stream_logger('')

def parse_options():
    """
    Parse the command line options.
    """
    global parser
    parser = argparse.ArgumentParser(
       prog = 'radosgw-util',
       description = 'radosgw-admin wrapper',
       epilog = 'This must be run as a user with permissions to run the radosgw-admin command.'
    )
    parser.add_argument('-p', dest='project_name', action='store', type=str, required=True,
                        help='Create a project with defined project name.')
    parser.add_argument('-q', dest='quota', action='store', type=int, required=True,
                        help='Set quota for the defined project(-p).')
    parser.add_argument('-b', dest='bucket', action='store', type=str,
                        help='Create bucket with defined name, for the defined project(-p).')
    parser.add_argument('-d','--debug', dest='debug', action='store_true', default=False,
                        help='Toggle Debug Mode. DEFAULT: %(default)s')
    parser.add_argument('-u', dest='url', action='store', type=str, required=True,
                        help='The fully qualifed name of the target pod: ex. https://ncsa.osn.xsede.org')
    parser.add_argument('-n', dest='dryrun', action='store_true', default=False,
                        help='Do not actually run, but log what would be done. Implies debug option. DEFAULT: %(default)s')

    args = parser.parse_args()
    if args.dryrun:
        args.debug = True

    return args

def run_cmd( cmdstr=None ):
    """
    Wrapper around subprocess module calls.
    """
    if not cmdstr:
        return None
    cmd = shlex.split(cmdstr)
    subp = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    (outdata, errdata) = subp.communicate()
    if subp.returncode != 0:
        msg = "Error\n  Command: {0}\n  Message: {1}".format(cmdstr,errdata)
        raise UserWarning( msg )
        sys.exit( subp.returncode )
    return( outdata )

def print_lines( inlines ):
   for line in inlines.splitlines():
      print (line.strip())

def create_project():
   cmd_str="sudo radosgw-admin user create --uid={} --gen-access-key --gen-secret --key-type=s3 --display-name={} --access=full".format(args.project_name, args.project_name)   
   cmd_out=run_cmd(cmd_str)

   for line in cmd_out.splitlines():
      print(line.strip())
      if 'access_key' in line:
         with open(args.project_name+"-access_key","a") as fp:
            fp.write(line)
            access_key = line.split()[1].strip('"').strip(',').strip('"')
         print(access_key)
      if 'secret_key' in line:
         with open(args.project_name+"-secret_key","a") as fp:
            fp.write(line)
            secret_key =line.split()[1].strip('"')
         print(secret_key)

   return access_key,secret_key

def create_subuser(username,access):
   if access == 'read':
      subuser = username+"_ro"
   elif access == 'readwrite':
      subuser = username+"_rw"

   cmd_str="sudo radosgw-admin subuser create --uid={} --subuser={} --gen-access-key --gen-secret --key-type=s3 --access={}".format(args.project_name,subuser,access)
   cmd_out=run_cmd(cmd_str)
   print_lines(cmd_out)

def set_quota():
   tera = 2**40
   giga = 2**30
   size = args.quota* giga
   cmd_str="sudo radosgw-admin quota set --quota-scope=user --uid={} --max-size={}".format(args.project_name, size)
   cmd_out=run_cmd(cmd_str)
   print_lines(cmd_out)

def set_max_buckets():
   cmd_str="sudo radosgw-admin user modify --uid={} --max-buckets=1".format(args.project_name)
   cmd_out=run_cmd(cmd_str)
   print_lines(cmd_out)

def enable_quota():
   cmd_str="sudo radosgw-admin quota enable --quota-scope=user --uid={}".format(args.project_name)
   cmd_out=run_cmd(cmd_str)
   print_lines(cmd_out)

def create_bucket(access_key,secret_key):
   s3 = boto3.resource('s3',
                     endpoint_url=args.url,
                     aws_access_key_id=access_key,
                     aws_secret_access_key=secret_key,
                     region_name='',)
   
   bucket=s3.Bucket(args.project_name)
   bucket.create()

def get_buckets(access_key,secret_key):
   s3 = boto3.client('s3',
                     endpoint_url=args.url,
                     aws_access_key_id=access_key,
                     aws_secret_access_key=secret_key,
                     region_name='',)

   response = s3.list_buckets()
   for item in response['Buckets']:
        print(item['CreationDate'], item['Name'])
 

if __name__ == "__main__":
   args = parse_options()

   proj_access_key,proj_secret_key = create_project()


   create_subuser(args.project_name,'read')
   create_subuser(args.project_name,'readwrite')

   set_max_buckets()
   create_bucket(proj_access_key, proj_secret_key)
   set_quota()
   enable_quota()

   get_buckets(proj_access_key, proj_secret_key)

