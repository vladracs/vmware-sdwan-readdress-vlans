#!/usr/bin/env python3
#
# Author: vfrancadesou@vmware.com
#
# Not to be considered as best practices in using VMware VCO API
# Meant to be used in Lab environments - Please test it and use at your own risk
#
# please note that VMWare API and Support team - do not guarantee this samples
# It is provided - AS IS - i.e. while we are glad to answer questions about API usage
# and behavior generally speaking, VMware cannot and do not specifically support these scripts
#
# Compatible with api v1 of the vmware sd-wan vco api
# using tokens to authenticate

import os
import sys
import requests
import json
from copy import deepcopy
import ipaddress
from ipaddress import IPv4Interface
import netaddr
from netaddr import IPNetwork
import argparse

########## VCO info and credentials
token = "Token %s" %(os.environ['VCO_TOKEN'])
vco_url = 'https://' + os.environ['VCO_HOSTNAME'] + '/portal/rest/'
headers = {"Content-Type": "application/json", "Authorization": token}
ProfileName='AWS Hub Profile'
EdgeName='Test-VCE-AWSset'
#EdgeName='AWS-VCE-'+str(random.randint(1,10000))
EdgeContactName='Vladimir'
EdgeContactEmail='vfrancadesou-aws@vmware.com'

######## VCO API methods
get_enterprise = vco_url + 'enterprise/getEnterprise'
get_edgelist = vco_url+'enterprise/getEnterpriseEdgeList'
get_edgeconfig = vco_url + 'edge/getEdgeConfigurationStack'
update_edgeconfig = vco_url+'configuration/updateConfigurationModule'
edge_prov = vco_url+'edge/edgeProvision'
get_profiles =vco_url + 'enterprise/getEnterpriseConfigurationsPolicies'
create_profile = vco_url+'configuration/cloneEnterpriseTemplate'

######## VCO FUNCTIONS
#### RETRIEVE ENTERPRISE ID for this user
def find_velo_enterpriseId():
	#Fetch enterprise id convert to JSON
	eid=0
	try:
         #print(headers)
         enterprise = requests.post(get_enterprise, headers=headers, data='')
	except Exception as e:
	   print('Error while retrivieng Enterprise')
	   print(e)
	   sys.exit()
	ent_j = enterprise.json()
	eid=ent_j['id']
	print('Enterprise Id = %d'%(eid))

	return eid

#### Find Edge in the list
def search_name(name,listName):
    for p in listName:
        if p['name'] == name:
            return p
######################### Main Program #####################
#### MAIN BODY
######################### Main Program #####################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("CSVfile", help="CSV file containing Edge/Vlan name and IPs")
    args = parser.parse_args()
    #Define user to serach for based on command line input
    if len(sys.argv) != 2:
    		raise ValueError('Please specify file with vlan addresses.  Example usage:  "python3 api_vco_vlan_readdress.py vlans.txt"')
    else:
    		fileVlans = sys.argv[1]
    print('Reading '+fileVlans+' readdressing Vlans')
    eid = find_velo_enterpriseId()
    with open(fileVlans) as fp:
        for line in fp:
            vlanArray = line.strip().split(' ')
            EdgeName = vlanArray[0]
            VlanId = vlanArray[1]
            vIP = IPNetwork(vlanArray[2])
            NewVlanIP = vIP.ip
            NewcidrPrefix = vIP.prefixlen
            NewNetmask= vIP.netmask
            params = {'enterpriseId': eid}
            edgesList = requests.post(get_edgelist, headers=headers, data=json.dumps(params))
            eList_dict=edgesList.json()
            length = len(eList_dict)
            name=search_name(EdgeName, eList_dict)
            edid = name['id']
            #print(name)
            if not (name=='None'):
                i=0
                EdgeId=0
                while i < length:
                     if(EdgeName==eList_dict[i]['name']):
                         EdgeId = eList_dict[i]['id']
                         print (EdgeName+' found on VCO with Edge id: '+str(EdgeId))
                         print("Searching for Vlan "+VlanId)
                         params = {'edgeId': edid}
                         respj = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
                         resp=respj.json()
                         edgeSpecificProfile = dict(resp[0])
                         edgeSpecificProfileDeviceSettings = [m for m in edgeSpecificProfile['modules'] if m['name'] == 'deviceSettings'][0]
                         edgeSpecificProfileDeviceSettingsData = edgeSpecificProfileDeviceSettings['data']
                         moduleId = edgeSpecificProfileDeviceSettings['id']
                         VlansNetworks = edgeSpecificProfileDeviceSettingsData['lan']['networks']
                         length2 = len(VlansNetworks)
                         h=0
                         while h < length2:
                                     #find vlan id in response

                                     if(str(VlanId)==str(VlansNetworks[h]['vlanId'])):
                                         print('Vlan Id in file: '+str(VlanId)+' Found Vlan Id in response: '+str(VlansNetworks[h]['vlanId']))
                                         print('Vlan IP:'+str(VlansNetworks[h]['cidrIp'])+' cidrPrefix: '+str(VlansNetworks[h]['cidrPrefix'])+' netmask: '+str(VlansNetworks[h]['netmask']))
                                         VlansNetworks[h]['cidrIp']=str(NewVlanIP)
                                         VlansNetworks[h]['cidrPrefix']=NewcidrPrefix
                                         VlansNetworks[h]['netmask']=str(NewNetmask)
                                         print('New Vlan IP:'+str(VlansNetworks[h]['cidrIp'])+'; New cidrPrefix: '+str(VlansNetworks[h]['cidrPrefix'])+'; New netmask: '+str(VlansNetworks[h]['netmask']))
                                         edgeSpecificProfileDeviceSettingsData['lan']['networks']=VlansNetworks
                                         d={"data":{}}
                                         d['data']=edgeSpecificProfileDeviceSettingsData
                                         params3 = {
                                         "id" : moduleId,
                                         "returnData" : 'true',
                                         "_update":  d,
                                         "name":"deviceSettings"}
                                         resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params3)))
                                         #print(resp.json())

                                     h+=1
                     i+=1

if __name__ == "__main__":
        main()
