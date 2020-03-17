#!/usr/bin/python3

import sys
import io
import subprocess
import shlex
import boto
import boto.s3.connection

secret_key = ""
access_key = ""

#Defining the function for getting project name
def get_project():

# Request our project name and input it into a string variable
    project_name = input("Please enter the Project Name:")

#Let's verify the project name by outputting it to the screen
    print(project_name)
    return project_name

#Calling for the name the project
project_name = get_project()

#Sanitizing for spaces in the project_name
while (' ' in project_name) == True:
    print("The Project name cannot contain spaces!")
    get_project()

def get_allocation():
    project_size = int(input("Please enter the Project's allocation size in TB:"))

#Let's verify the project name by outputting it to the screen
    print(project_size)
    return project_size

#Calling for the name the project
project_size = get_allocation()

#Defining a TB as 2^40
tera = 2**40
#Math  for calculating interpretable allocation variable

size = project_size * tera
print(size)

#Function for creating the Account
def create_account():
    command = "sudo radosgw-admin user create --uid={} --gen-access-key --gen-secret --key-type=s3 --display-name={} --access=full".format(project_name, project_name)
    command_sh = shlex.split(command)
    print(command_sh)
    process = subprocess.Popen(command_sh,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    while True:
    #output = process.stdout.readline()
    #print(output.strip())
    ## Do something else
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
        ## Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                print(output.strip())
                if "access_key" in output:
                    with open(project_name+"-access_key","a") as fp:
                        fp.write(output)
                        access_key = output.split()[1].strip('"').strip(',').strip('"')
                    print(access_key)
                if "secret_key" in output:
                    with open(project_name+"-secret_key","a") as fp:
                        fp.write(output)
                        secret_key = output.split()[1].strip('"')
                        print(secret_key)
            break

#Create the account by calling the function
create_account()

print(access_key)
print(secret_key)

#create an s3 connection with our server

# Define the read/write subuser call
def create_rw_account():
    command = "sudo radosgw-admin subuser create --uid={} --subuser={}_rw --gen-access-key --gen-secret --key-type=s3 --access=readwrite".format(project_name, project_name)
    command_sh = shlex.split(command)
    print(command_sh)
    process = subprocess.Popen(command_sh,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    while True:
    #output = process.stdout.readline()
    #print(output.strip())
    ## Do something else
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
        ## Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                print(output.strip())
            break

#Create the account read/write subuser
create_rw_account()

# Define the read-only subuser call
def create_ro_account():
    command = "sudo radosgw-admin subuser create --uid={} --subuser={}_ro --gen-access-key --gen-secret --key-type=s3 --access=read".format(project_name, project_name)
    command_sh = shlex.split(command)
    print(command_sh)
    process = subprocess.Popen(command_sh,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    while True:
    #output = process.stdout.readline()
    #print(output.strip())
    ## Do something else
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
        ## Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                print(output.strip())
            break

#Create the account by calling the function
create_ro_account()

#Define the function to apply quotas
def apply_quotas():

#Command to set maximum bucket count to 1 for the account
    command = "sudo radosgw-admin user modify --uid={} --max-buckets=1".format(project_name)
    command_sh = shlex.split(command)
    print(command_sh)
    process = subprocess.Popen(command_sh,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    while True:
    #output = process.stdout.readline()
    #print(output.strip())
    ## Do something else
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
        ## Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                print(output.strip())
            break

#Command to set the maximum size of the account to the Allocation size
    command = "sudo radosgw-admin quota set --bucket={} --max-size={}".format(project_name, size)
    command_sh = shlex.split(command)
    print(command_sh)
    process = subprocess.Popen(command_sh,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    while True:
    #output = process.stdout.readline()
    #print(output.strip())
    ## Do something else
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
        ## Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                print(output.strip())
            break

#Command to enable the quota for the user

    command = "sudo radosgw-admin quota enable --quota-scope=bucket --bucket={}".format(project_name)
    command_sh = shlex.split(command)
    print(command_sh)
    process = subprocess.Popen(command_sh,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    while True:
    #output = process.stdout.readline()
    #print(output.strip())
    ## Do something else
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
        ## Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                print(output.strip())
            break

#Apply the quotas by calling the function
apply_quotas()
