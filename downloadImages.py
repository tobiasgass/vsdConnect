#!/usr/bin/python

import connectVSD
import sys
import argparse

parser = argparse.ArgumentParser(description='Download original image files from SMIR to a specific folder.')
parser.add_argument('--targetFolder', dest='targetFolder', default="./",
                   help='folder to store images in')
parser.add_argument('--targetProject', dest='targetProject', required=1,
                   help='Project/Folder Name of VSD (sub folder of SSMProjects)')

args=parser.parse_args()
#con=connectVSD.VSDConnecter("username","password")
#con=connectVSD.VSDConnecter()

con=connectVSD.VSDConnecter("Z2Fzc3RAdmlzaW9uLmVlLmV0aHouY2g6VGgxbktiVj0=")


SSMFolderID=2811
print "Retrieving folder list from SMIR.."
folderList=con.getFolderList()

folderHash=con.readFolders(folderList)

targetProject=args.targetProject

SSMFolder=folderHash[SSMFolderID]
ProjectFolder=None
OriginalFolder=None
SegmentationFolder=None

print "Retrieving target folder IDs from folder list."
for child in SSMFolder.childFolders:
    if (child.name==targetProject):
        ProjectFolder=child
        break
for child in ProjectFolder.childFolders:
    if (child.name=="01_Original"):
        OriginalFolder=child
    elif (child.name=="02_AutomaticSegmentation"):
        SegmentationFolder=child

print "Retrieving file list from folder.."
fileList=con.getFileListInFolder(OriginalFolder.ID)
fileIDList=con.getFileIDs(fileList)

for ID in fileIDList:
    print ID
    con.downloadFile(ID,args.targetFolder)


#con.downloadFile(56738)
