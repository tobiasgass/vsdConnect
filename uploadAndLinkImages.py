#!/usr/bin/python

import connectVSD
import sys
import argparse
import json

parser = argparse.ArgumentParser(description='Download original image files from SMIR to a specific folder.')
parser.add_argument('--targetFolder', dest='targetFolder', default="./",
                   help='folder to store images in')
parser.add_argument('--targetProject', dest='targetProject', required=1,
                   help='Project/Folder Name of VSD (sub folder of SSMProjects)')

#parser.add_argument('--targetProject', dest='targetProject', required=1,                   help='Project/Folder Name of VSD (sub folder of SSMProjects)')


args=parser.parse_args()
#con=connectVSD.VSDConnecter("username","password")
#con=connectVSD.VSDConnecter()
#con=connectVSD.VSDConnecter("Z2Fzc3RAdmlzaW9uLmVlLmV0aHouY2g6VGgxbktiVj0=")

con=connectVSD.VSDConnecter("ZGVtb0B2aXJ0dWFsc2tlbGV0b24uY2g6ZGVtbw==")
con.seturl("https://demo.virtualskeleton.ch/api/")

#con.downloadFile(110,args.targetFolder)

segID=con.uploadSegmentation(278,"/home/gasst/work3/data2/mandibles/segmentations/0129-segmentation-tobias-iso.nii")
print con.getObject(segID)
sys.exit()


obj110=con.getObject(110)
#link={'id': 1, 'selfurl':'https://demo.virtualskeleton.ch/api/object-links/1', 'object1':'https://demo.virtualskeleton.ch/api/objects/110' , 'object2':'https://demo.virtualskeleton.ch/api/objects/91'}
result=con.addLink(110,91)
print result
sys.exit()

#print con.getRequest("objects/"+str(2811))

#fileinfo=con.uploadFile("/home/gasst/work/src/vsdConnectPY/Variant_artery-110_0.mha")

fileinfo={'relatedObject':{'selfUrl':"https://demo.virtualskeleton.ch/api/objects/275"}}

#originalFileInfo=open(originalFileInfoFilenName,'r').read()




SSMFolderID=2811
print "Retrieving folder list from SMIR.."
folderList=con.getFolderList()
folder=folderList['items'][3]

print folder['containedObjects']

entry={'selfUrl' : 'https://demo.virtualskeleton.ch/api/objects/110'}
folder['containedObjects'].append(entry)

print folder

con.putRequest('folders',json.dumps(folder))

sys.exit()

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
