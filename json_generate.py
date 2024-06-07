#import necessities 
import csv
import shutil
import git
from git import Repo
import os
import pandas as pd
import yaml
import json

import pydriller as pydrill
from pydriller import Repository

import subprocess
from pathlib import Path

IAC_TOOLS = {
    'Terraform': ['.tf', '.tf.json'],#  we might have to look at like specific files within the directories of the repo that each tool must have? or most likely has?
    'Pulumi': ['.yaml', '.yml',],
    'Crossplane': ['.yaml', '.yml'],
    'AWS CloudFormation': ['.yaml', '.yml', '.json'],
    'Azure Resource Manager': ['.json'],
    'Google Cloud Deployment Manager': ['.yaml'],
    'Ansible': ['.yaml', '.yml'],
    'Chef': ['.rb'],
    'Puppet': ['.conf', '.pp'], #im gonna have to include full extension like puppet.conf
    'SaltStack': ['.sls'],
    'Bicep': ['.bicep'],
    'OpenTofu': ['.tf', '.tf.json'],
    'Vagrant': ['.vm', '.ssh', '.winrm', '.winssh', '.vagrant'],
    'Docker Compose': ['.yaml', '.yml']  
}
IAC_TOOLS_ABBREV = {
    'Terraform': 'TF',
    'Pulumi': 'PUL',
    'Crossplane': 'CP',
    'AWS CloudFormation': 'AWS',
    'Azure Resource Manager': 'AZ',
    'Google Cloud Deployment Manager': 'GOOG',
    'Ansible': 'ANS',
    'Chef': 'CH',
    'Puppet': 'PUP', 
    'SaltStack': 'SS',
    'Bicep': 'BIC',
    'OpenTofu': 'OT',
    'Vagrant': 'VAG',
    'Docker Compose': 'DOC'  
}
special_extensions = ['.tf' , '.tf.json', '.yaml','.yml','.json','.rb','.conf','.pp','.sls','.bicep','.vm','.ssh','.winrm','.winssh','.vagrant']
# Initialize global dictionaries
links_dict = {}
new_repo_json_dict = {}
working_link = ""
working_userRepo = ""
working_target_dir = ""


working_all_file_extensions = []
working_all_yaml = []
working_all_yml = []
working_all_json = []
working_all_rb  = [] 
working_all_conf = []
working_all_pp = []
working_all_sls = []
working_all_bicep = []
working_all_tf = []
working_all_tf_json = []
working_all_vm = []
working_all_ssh = []
working_all_winrm = []
working_all_winssh = []
working_all_vagrant = []

working_has_iac = 0
working_all_iac_intersections={}
working_all_used_iac_tools = [] 
working_all_iac_bool = []

failed_cloned_repos = {}

#reigon csv generation

csv_file_path = "output.csv"
working_json_string = ""
working_iac_used_string = ""

#endreigon



# Define the log file path
failed_path = "failed.txt"
log_file_path = 'checking.txt'
getting_missing_tf = 'missing_tf.txt'
other = "other.txt"

#define folder for all json files
json_directory = 'ALL_REPO_JSON'

def write_list_to_file(file_path, lst):
    with open(file_path, 'a') as file:  # Open in append mode
        for item in lst:
            file.write(f"{item}\n")

def write_to_file(file_path, text):
    with open(file_path, 'a') as file:  # Open in append mode
        if text != None:
            file.write(text + '\n')

def write_dict_to_file(file_path, dictionary):
    with open(file_path, 'a') as file:  # Open in append mode
        for key, value in dictionary.items():
            file.write(f"{key}: {value}\n")

def get_intersections():
    global working_all_iac_intersections
    for tool, extensions in IAC_TOOLS.items():
        tool_extensions_set = set(extensions)
        common_extensions = tool_extensions_set.intersection(working_all_file_extensions)
        write_list_to_file(other, common_extensions)
        working_all_iac_intersections[tool] = common_extensions
    write_dict_to_file(other, working_all_iac_intersections)
    return working_all_iac_intersections

def get_abbreviation(tool):
    for tool_,abbrev in IAC_TOOLS_ABBREV.items():
        if tool == tool_:
            return abbrev

def get_list_of_bool_values(intersections):
    global working_all_iac_bool
    global working_all_used_iac_tools
    for tool,list in intersections.items():
        temp_set = set(list)
        if len(temp_set)>0:
            working_all_iac_bool.append(1)
            abbrev = get_abbreviation(tool)
            working_all_used_iac_tools.append(abbrev)

        else:
            working_all_iac_bool.append(0)
    write_list_to_file(other, working_all_iac_bool)
    return working_all_iac_bool

def determine_iac_usage(bool_list):
    for item in bool_list:
        if item==1:
            return 1
    return 0
            
def get_iac_comparisons():
    global working_all_iac_bool
    global working_has_iac
    global working_all_used_iac_tools
    global working_all_iac_intersections
    working_all_iac_intersections =get_intersections()
    working_all_iac_bool=get_list_of_bool_values(working_all_iac_intersections)
    working_has_iac= determine_iac_usage(working_all_iac_bool)

def open_csv_file():
    # Define the path to the CSV file
    csv_file_path = 'P.U_merged_filtered - Final_merged_only_not_excluded_yes_ms_unarchived_commit_hash v2.0.csv'
    
    # Try different encodings
    encodings = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            write_to_file(log_file_path, f"Trying encoding: {encoding}")
            with open(csv_file_path, mode='r', newline='', encoding=encoding) as file:
                csv_reader = csv.reader(file)
                
                # Skip the header row
                next(csv_reader)
                
                # Print the first and third columns of each row in the CSV file
                for row in csv_reader:
                    if row:  # Check if the row is not empty
                        first_column = row[0]  # Get the first column value
                        third_column = row[2]  # Get the third column value
                        write_to_file(log_file_path, first_column)
                        write_to_file(log_file_path, third_column)

                        if third_column != 'identifier':  # Check if third_column is not empty or 'identifier'
                            links_dict[first_column] = third_column
            break  # Exit the loop if no error occurs
        except UnicodeDecodeError as e:
            write_to_file(log_file_path, f"Encoding {encoding} failed: {e}")
        except FileNotFoundError:
            write_to_file(log_file_path, f"Error: The file '{csv_file_path}' does not exist.")
            break
        except Exception as e:
            write_to_file(log_file_path, f"An unexpected error occurred: {e}")
            break

    # Print the dictionary
    write_to_file(log_file_path, "Links and their identifiers:")
    write_dict_to_file(log_file_path, links_dict)


def fetch_new_url():
    if links_dict:
        first_key = next(iter(links_dict))  # Get the first key
        first_value = links_dict.pop(first_key)  # Remove the first key-value pair and get the value
        first_value = change_slash(first_value)
        return first_key, first_value
    else:
        return None, None
   
def change_slash(value):
    value = value.replace('/', '\\')
    return value

#copies working pair to global values
def copy_pair(key,value):
    global working_link
    global working_userRepo
    working_link = key
    working_userRepo = value
    
def clone_repo(): #clones directory to target directory 
    # Get URL
    key, value = fetch_new_url()
    print(value)
    new_val = change_slash(value)
    print(new_val)
    write_to_file(log_file_path, f"Fetched URL: {key}, Path: {new_val}")  # Debugging statement
    copy_pair(key,new_val)
    if not key or not value:
        write_to_file(log_file_path, "No more URLs to process.")
        return None

    global working_target_dir
    target_dir = r'C:\\ClonedRepos\\' + new_val
    working_target_dir = target_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    else:
        write_to_file(log_file_path, f"Directory already exists: {target_dir}")  # Debugging statement
        return None

    try:
        repo = Repo.clone_from(key, target_dir)
        write_to_file(log_file_path, "cloned!")  # This should print if cloning is successful
    except Exception as e:
        write_to_file(log_file_path, f"Failed to clone repo: {e}")  # Debugging statement for cloning failure
        write_to_file(failed_path, f"USER / REPO :" + working_userRepo + ", LINK : " + working_link + "\n")
        return None

    return target_dir

def delete_cloned_repo(repo_path):
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
        print(f"Repository at {repo_path} has been deleted.")
    else:
        print(f"Repository at {repo_path} does not exist.")

def get_every_file(new_repo):
    global working_all_file_extensions
    # Get all files
    all_files = []
    for root, dirs, files in os.walk(new_repo):
        for file in files:
            file_path = os.path.join(root, file)
            new_file_path = change_slash(file_path)
            all_files.append(new_file_path)
            extension = get_file_extension(new_file_path)
            if extension not in working_all_file_extensions:
                working_all_file_extensions.append(extension)
    return all_files

def get_file_extension(file_path):
    global file_extension
    _, file_extension = os.path.splitext(file_path)
    if file_extension in special_extensions and not None:
        if file_extension in '.tf':
            write_to_file(getting_missing_tf,f"found tf file" + file_path + ":" + working_userRepo)
            working_all_tf.append(file_path)
        return file_extension
    
def create_dictionary():
    global new_repo_json_dict
    global working_all_file_extensions
    #clear null from file extensions 
    working_all_file_extensions = [item for item in working_all_file_extensions if item is not None]

    new_repo_json_dict = {
        "id":working_userRepo,
        "repo_link": working_link,
        "file_extensions":working_all_file_extensions,
        "iac?": working_has_iac,
        "list_of_used_iac_tools": working_all_used_iac_tools,
        "files":{
            "yml":working_all_yml,
            "yaml":working_all_yaml,
            "json":working_all_json,
            "ruby":working_all_rb,
            "conf":working_all_conf,
            "pp":working_all_pp,
            "sls":working_all_sls,
            "bicep":working_all_bicep,
            "tf":working_all_tf,
            "tfjson":working_all_tf_json,
            "vm":working_all_vm,
            "ssh":working_all_ssh,
            "winrm":working_all_winrm,
            "winssh":working_all_winssh,
            "vagrant":working_all_vagrant
            
        }
    }
    # Remove fields that have empty values
    new_repo_json_dict["files"] = {k: v for k, v in new_repo_json_dict["files"].items() if v}

#reigon filter extensions
def get_json_subset(files):
    global working_all_json
    working_all_json = [file for file in files if file.endswith('.json')]

def get_yml_subset(files):
    global working_all_yml
    working_all_yml = [file for file in files if file.endswith('.yml')]
    
def get_rb_subset(files):
     global working_all_rb
     working_all_rb = [file for file in files if file.endswith('.rb')]

def get_conf_subset(files):
     global working_all_conf
     working_all_conf = [file for file in files if file.endswith('.conf')]

def get_pp_subset(files):
     global working_all_pp
     working_all_pp = [file for file in files if file.endswith('.pp')]

def get_sls_subset(files):
     global working_all_sls
     working_all_sls = [file for file in files if file.endswith('.sls')]

def get_bicep_subset(files):
     global working_all_bicep
     working_all_bicep = [file for file in files if file.endswith('.bicep')]

def get_yaml_subset(files):
    global working_all_yaml
    working_all_yaml = [file for file in files if file.endswith('.yaml')]

def get_tf_subset(files):
     global working_all_tf
     working_all_tf = [file for file in files if file.endswith('.tf')]

def get_tf_json_subset(files):
     global working_all_tf_json
     working_all_tf_json = [file for file in files if file.endswith('.tf.json')]

def get_vm_subset(files):
     global working_all_vm
     working_all_vm = [file for file in files if file.endswith('.vm')]

def get_ssh_subset(files):
     global working_all_ssh
     working_all_ssh = [file for file in files if file.endswith('.ssh')]

def get_winrm_subset(files):
     global working_all_winrm
     working_all_winrm = [file for file in files if file.endswith('.winrm')]

def get_winsh_subset(files):
     global working_all_winssh
     working_all_winssh = [file for file in files if file.endswith('.winsh')]

def get_vagrant_subset(files):
     global working_all_vagrant
     working_all_vagrant = [file for file in files if file.endswith('.vagrant')]

#endreigon

def set_up_dir():
    global json_directory
    filename = f"data_{working_userRepo}.json"
    if not os.path.exists(json_directory):
        os.makedirs(json_directory)
    return filename

# Function to save a dictionary as a JSON file in the specified directory
def save_dict_to_json_file(directory, filename, dictionary):
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w') as json_file:
        json.dump(dictionary, json_file, indent=4)
    print(f"Data has been written to {file_path}")

def process_next():
     # Clone a repo one at a time
    new_repo = clone_repo()
    write_to_file(log_file_path, f"New repo path: {new_repo}")  # Debugging statement
    if new_repo:
        files = get_every_file(new_repo)
        #print(working_all_file_extensions)
        get_json_subset(files)
        get_yml_subset(files)
        get_yaml_subset(files)
        get_rb_subset(files)
        get_conf_subset(files)
        get_pp_subset(files)
        get_sls_subset(files)
        get_bicep_subset(files)
        get_tf_subset(files)
        get_tf_json_subset(files)
        get_vm_subset(files)
        get_ssh_subset(files)
        get_winrm_subset(files)
        get_winsh_subset(files)
        get_vagrant_subset(files)
        get_iac_comparisons()
      
    create_dictionary()
 
    filename = set_up_dir()
    save_dict_to_json_file(json_directory,filename,new_repo_json_dict)
    delete_cloned_repo(working_target_dir) 

def clear_all_var():
    global new_repo_json_dict
    global working_link
    global working_userRepo
    global working_target_dir
    global working_has_iac
    global working_best_match_iac
    global working_all_file_extensions
    global working_all_yaml
    global working_all_yml
    global working_all_json
    global working_all_rb
    global working_all_conf
    global working_all_pp
    global working_all_sls
    global working_all_bicep
    global working_all_tf
    global working_all_tf_json
    global working_all_vm
    global working_all_ssh
    global working_all_winrm
    global working_all_winssh
    global working_all_vagrant
    global links_dict
    global new_repo_json_dict
    global working_link
    global working_userRepo
    global working_target_dir
    global working_all_iac_intersections
    global working_all_file_extensions
    global working_all_iac_bool
    global working_has_iac
    global working_all_used_iac_tools

    working_all_iac_intersections={}
    working_all_used_iac_tools = [] 
    working_all_iac_bool = []
    working_has_iac = 0
    new_repo_json_dict = {}
    working_link = ""
    working_userRepo = ""
    working_target_dir = ""
    working_has_iac = 0
    working_best_match_iac = []
    working_all_file_extensions = []
    working_all_yaml = []
    working_all_yml = []
    working_all_json = []
    working_all_rb  = [] 
    working_all_conf = []
    working_all_pp = []
    working_all_sls = []
    working_all_bicep = []
    working_all_tf = []
    working_all_tf_json = []
    working_all_vm = []
    working_all_ssh = []
    working_all_winrm = []
    working_all_winssh = []
    working_all_vagrant = []

def add_csv_row():
    # Open the CSV file for writing
    with open(csv_file_path, 'a', newline='') as csvfile:
        global working_json_string
        global working_iac_used_string
        global working_all_used_iac_tools

        working_json_string = json.dumps(new_repo_json_dict)
        working_iac_used_string = ', '.join(working_all_used_iac_tools)
        # Define the CSV fieldnames
        fieldnames = ['project', 'link', 'json', 'iac?', 'list of iacs used']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)


        # Write a row with the example data
        writer.writerow({
            'project': working_userRepo,
            'link': working_link,
            'json': working_json_string,
            'iac?': working_has_iac,
            'list of iacs used': working_iac_used_string
        })
    print(f"Data has been written to {csv_file_path}")

def print_header_final_csv():
    with open(csv_file_path, 'w', newline='') as csvfile:
        # Define the CSV fieldnames
        fieldnames = ['project', 'link', 'json', 'iac?', 'list of iacs used']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # Write the header
        writer.writeheader()

def main():
    write_to_file(log_file_path, 'begin')
    # Store all link:user/repo in links_dict
    open_csv_file()

    # process all repos
    write_to_file(failed_path, "FAILED CLONED REPOS")
    print_header_final_csv()
    while links_dict:
        process_next()
        add_csv_row()
        clear_all_var()
    #write_list_to_file(failed_path,failed_cloned_repos)
    



# Call the main function
main()
