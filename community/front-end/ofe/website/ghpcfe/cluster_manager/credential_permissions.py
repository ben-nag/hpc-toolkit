#!/usr/bin/env python3
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Cloud credential permission routines"""

import logging
import json
import warnings
import subprocess

from google.oauth2 import service_account

logger = logging.getLogger(__name__)

def service_account_active_IAM_roles(credential_obj, service_acct_name, project_name):
    '''
    Returns the current IAM roles of the given service account in GCP
    Using the provided credential file
    '''
    from google.oauth2 import service_account
    import googleapiclient.discovery
    if not "serviceAccount:" in service_acct_name:
        service_acct_name = "serviceAccount:" + service_acct_name
    service = googleapiclient.discovery.build(
        'cloudresourcemanager', 'v1', credentials=credential_obj)
    response = service.projects().getIamPolicy(resource=project_name, body={}).execute()["bindings"]
    active_roles = []
    for roledict in response:
        if service_acct_name in roledict["members"]:
            active_roles.append(roledict["role"])
    return active_roles


def get_role_list(role_file):
    '''
    Get necessary roles for OFE from file.

    TODO: Retrieve from Git?
    '''
    role_list = []
    role_file_read = open(role_file,"r").readlines()
    for row in role_file_read:
        row = row.strip()
        if not row.startswith("roles/"):
            row = "roles/"+row
        role_list.append(row)
    return role_list

def service_account_check_roles(credential_obj, service_acct_name, role_list_file,project_name):
    '''
    Compare the live roles on the service account, to those listed in the role file
    Returns a dictionary of states to be parsed by the front end
    '''
    active_roles = service_account_active_IAM_roles(credential_obj,service_acct_name,project_name)
    needed_roles = get_role_list(role_list_file)
    all_roles = list(set(active_roles + needed_roles))
    role_check_dict = {}
    for role in all_roles:
        if role in active_roles and role in needed_roles:
            role_state = "ok"
        elif role in active_roles and not role in needed_roles:
            role_state = "surplus"
        elif not role in active_roles and role in needed_roles:
            role_state = "required"
        role_check_dict[role]= role_state
    return role_check_dict

def get_credential_object(credential_info):
    '''
    Return a google credential object from the Credential Model
    '''
    from google.oauth2 import service_account
    import json
    cred_detail = credential_info.__dict__["detail"]
    cred_detail_json = json.loads(cred_detail)
    credentials = service_account.Credentials.from_service_account_info(cred_detail_json)
    return credentials

def check_credential_permissions(credential_detail):
    '''
    Returns credential role status given credential object
    Provides a list of roles with statuses:
    [installed, installed but not necessary, not installed and needed]
    '''
    credential_detail_json = json.loads(credential_detail.__dict__["detail"])
    project_name = credential_detail_json["project_id"]
    service_acct_addr = credential_detail_json["client_email"]
    credential_obj = get_credential_object(credential_detail)
    role_file = "/opt/gcluster/hpc-toolkit/community/front-end/ofe/website/ghpcfe/cluster_manager/role_list" 
    sacct_info = service_account_check_roles(credential_obj,service_acct_addr,role_file,project_name)
    sorted_sacct_info = {k: v for k, v in sorted (sacct_info.items ())}
    return sorted_sacct_info

