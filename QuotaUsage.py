#!/usr/bin/python3

import io
import sys
import subprocess
import shlex
import ast
import json

def get_user_list():

    command = "sudo radosgw-admin user list"
    command_sh = shlex.split(command)
    print(command_sh)

    process = subprocess.Popen(command_sh,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)


    #while True:
    #    return_code = process.poll()
    #    if return_code is not None:
    #        print('RETURN CODE', return_code)
    #
    #        for output in process.stdout.readlines():
    #            print(output.strip('""'))
    #        break

    users, error = process.communicate()
    print("test")
    print(users)
    print("test")

    list_users = list(users.split(","))
    new_list = []
    for i in range(len(list_users)):
        print(list_users[i].strip(" ").strip('"').strip('"').split('"')[1])
        new_list.append(list_users[i].strip(" ").strip('"').strip('"').split('"')[1])

    return new_list

def get_user_info(user_list):


    user_json = {}
    quota = ""
    stats_json = {}
    stats_string = ""

    with open('/var/log/OSN_Projects.txt', "w") as fp:
        fp.write("      QUOTAS FOR USER ACCOUNTS:\n\n")
    #    fp.write(userlist)


        for i in user_list:
            command = "sudo radosgw-admin user info --uid={}".format(i)
            command_sh = shlex.split(command)

            process = subprocess.Popen(command_sh,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)

            user_info, error = process.communicate()

            user_json = json.loads(user_info)
            print(user_json)
            user_quota_max_size = user_json['user_quota']['max_size_kb']
            quota = "      Quota for user account {} is {}Kb \n".format(i, user_quota_max_size)
            print(quota)

            fp.write(quota)

            command = "sudo radosgw-admin user stats --uid={}".format(i)
            command_sh = shlex.split(command)

            process = subprocess.Popen(command_sh,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)

            stats, error = process.communicate()

            stats_json = json.loads(stats)
            print(stats_json)
            user_stats_total_rounded = stats_json['stats']['total_bytes_rounded']
            stats_string = "      Usage for user account {} is {} bytes \n\n".format(i, user_stats_total_rounded)
            print(stats_string)

            fp.write(stats_string)

    fp.close()
        #while True:
            #return_code = process.poll()
            #if return_code is not None:
                #print('RETURN CODE', return_code)
                #for output in process.stdout.readlines():
                    #user_json = json.loads(output.strip())
                    #print(output.strip())
                    #user_json = json.loads(output.text)
                    #print(user_json)

                #break


get_user_info(get_user_list())

def display_usage():


    command = "cat /var/log/OSN_Projects.txt"
    command_sh = shlex.split(command)
    print(command_sh)

    process = subprocess.Popen(command_sh,
                    stdout=subprocess.PIPE,
                    universal_newlines=True)
    while True:
       return_code = process.poll()
       if return_code is not None:
           #print('RETURN CODE', return_code)
           for output in process.stdout.readlines():
               print(output.strip())
           break
display_usage()
