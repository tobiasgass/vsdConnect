#!/usr/bin/python

import connectVSD
import sys
import argparse
import json

parser = argparse.ArgumentParser(description='Download original image files from SMIR to a specific folder.')


#parser.add_argument('--targetProject', dest='targetProject', required=1,                   help='Project/Folder Name of VSD (sub folder of SSMProjects)')


args=parser.parse_args()
#con=connectVSD.VSDConnecter("username","password")
#con=connectVSD.VSDConnecter()
con=connectVSD.VSDConnecter("Z2Fzc3RAdmlzaW9uLmVlLmV0aHouY2g6VGgxbktiVj0=")


print "Retrieving folder list from SMIR.."
folderList=con.getFolderList()


folderHash=con.readFolders(folderList)

for folderKey in folderHash:
    folder=folderHash[folderKey]
    print folder.name, folder.ID, folder.parentFolder


#con.downloadFile(56738)
