#!/usr/bin/python

# connectVSD 0.1
# (c) Tobias Gass, 2015
# conncetVSD 0.2 python 3 @Michael Kistler 2015
# changed / added auth 
from __future__ import print_function

import sys
import math
if sys.version_info >= (3, 0):
    PYTHON3 = True
else:
    PYTHON3 = False

import os
import urllib
if PYTHON3:
    from urllib.parse import urlparse
    from urllib.parse import quote as urlparse_quote
else:
    from urlparse import urlparse
    from urllib import quote as urlparse_quote

import json
import getpass
if PYTHON3:
    from pathlib import Path, PurePath, WindowsPath
import requests
from requests.auth import AuthBase

import io
import base64
import zlib
import zipfile
import shutil

try:
    import lxml.etree as ET
except:
    import xml.etree.ElementTree as ET




requests.packages.urllib3.disable_warnings()

class SAMLAuth(AuthBase):
    """Attaches SMAL to the given Request object. extends the request package auth class"""
    def __init__(self, enctoken):
        self.enctoken = enctoken

    def __call__(self, r):
        # modify and return the request
        r.headers['Authorization'] = b'SAML auth=' + self.enctoken
        return r

def samltoken(fp, stsurl = 'https://ciam-dev-chic.custodix.com/sts/services/STS'):
    ''' 
    generates the saml auth token from a credentials file 

    :param fp: (Path) file with the credentials (xml file)
    :param stsurl: (str) url to the STS authority
    :returns: (byte) enctoken 
    '''

    if fp.is_file():
        tree = ET.ElementTree()
        dom = tree.parse(str(fp))
        authdata =  ET.tostring(dom, encoding = 'utf-8')

    #send the xml in the attachment to https://ciam-dev-chic.custodix.com/sts/services/STS
    r = requests.post(stsurl, data = authdata, verify = False)

    if r.status_code == 200:

        fileobject = io.BytesIO(r.content)

        tree = ET.ElementTree()
        dom = tree.parse(fileobject)
        saml = ET.tostring(dom, method = "xml", encoding = "utf-8")


        #ZLIB (RFC 1950) compress the retrieved SAML token.
        ztoken = zlib.compress(saml, 9)

        #Base64 (RFC 4648) encode the compressed SAML token.
        enctoken = base64.b64encode(ztoken)
        return enctoken
    else:
        return None

class VSDConnecter:
    APIURL='https://demo.virtualskeleton.ch/api/'

    def __init__(self, 
        authtype = 'basic',
        url = "https://demo.virtualskeleton.ch/api/",
        username = "demo@virtualskeleton.ch", 
        password = "demo", 
        version = "",
        token = None,
        ):

        if version:
            version = str(version) + '/'

        self.url = url + version

        self.s = requests.Session()
        
        self.s.verify = False

        if authtype == 'basic':
            self.username = username
            self.password = password
            self.s.auth = (self.username, self.password)

        elif authtype == 'saml':
            self.token = token
            self.s.auth = SAMLAuth(self.token)



    def getAPIObjectType(self, response):
        '''create an APIObject depending on the type 

        :param response: (json) object data
        :returns: (APIObject) object
        '''
        apiObject = APIObject()
        apiObject.set(obj = response)
        if apiObject.type == 1:
            obj = APIObjectRaw()
        elif apiObject.type == 2:
            obj = APIObjectSeg()
        elif apiObject.type == 3:
            obj = APIObjectSm()
        elif apiObject.type == 4:
            obj = APIObjectCtDef()
        elif apiObject.type == 5:
            obj = APIObjectCtData()
        else:
            obj = APIObject()
        return obj

    def fullUrl(self, resource):
        '''
        check if resource is selfUrl or relative path. a correct full path will be returned 
        
        :param resource: (str) to the api resource
        :returns: (str) the full resource path 
        '''
        res = urlparse(str(resource))

        if res.scheme == 'https':
            return resource
        else:
            return self.url + resource

    def getRequest(self, resource, rpp = None, page = None, include = None):
        '''
        generic request function

        :param resource: (str) resource path
        :param rpp: (int) results per page to show
        :param page: (int) page nr to show, starts with 0
        :param include: (str) option to include more informations
        :returns: list of objects (json) or None
        '''
      
        params = dict([('rpp', rpp),('page', page),('include', include)])

        try: 
            res = self.s.get(self.fullUrl(resource), params = params)
            if res.status_code == requests.codes.ok:
                return res.json()
            else: 
                return None
        except requests.exceptions.RequestException as err:
            print('request failed:', err)
            return None

    def downloadZip(self, resource, fp):
        '''
        download the zipfile into the given file (fp)

        :param resource: (str) download URL
        :param fp: (Path) filepath 
        :returns: None or status_code ok (200)
        '''
        res = self.s.get(self.fullUrl(resource), stream = True)
        if res.ok:
            with fp.open('wb') as f:
                shutil.copyfileobj(res.raw, f) 
            return res.status_code
        else:
            return None


    def removeLinks(self, resource):
        '''removes all related item from an object '''

        obj = self.getObject(resource)
        if obj.linkedObjectRelations:
            for link in obj.linkedObjectRelations:
                self.delRequest(link["selfUrl"])
        else:
            print('nothing to delete, no links available')

    def getAllPaginated(self, resource, itemlist):
        '''
        returns all items as list 

        :param resource: (str) resource path
        :param itemlist: (list) of items
        :returns: list of items
        '''
        res = self.getRequest(resource)
        if res:
            page = APIPagination()
            page.set(obj = res)
            for item in page.items:
                itemlist.append(item)
            if page.nextPageUrl:
                return self.getAllPaginated(page.nextPageUrl, itemlist = itemlist)
            else:
                return itemlist
        else: 
            return itemlist

    def getOID(self, selfURL):
        ''' 
        extracts the last part of the selfURL, tests if it is a number

        :param selfURL: (str) url to the object
        :returns: either None if not an ID or the object ID (int)
        :raises: ValueError
        '''
        selfURL_path = urllib.parse.urlsplit(selfURL).path
        if PYTHON3:
            oID = Path(selfURL_path).name
        else:
            oID = os.path.basename(selfURL_path)

        try: 
            r = int(oID)
        except ValueError as err:
            print('no object ID in the selfUrl {0}. Reason: {1}'.format(selfURL,err))
            r = None
        return r
    
    def getObject(self, resource):
        '''retrieve an object based on the objectID

        :param resource: (str) selfUrl of the object or the (int) object ID
        :returns: the object (APIObject) 
        '''
        if isinstance(resource, int):
            resource = 'objects/' + str(resource)

        res = self.getRequest(resource)
        if res:
            obj = self.getAPIObjectType(res)
            obj.set(obj = res)
            return obj
        else:
            return res

    def putObject(self, obj):
        '''update an objects information
    
        :param obj: (APIObject) an API Object
        :returns: (APIObject) the updated object
        '''
        res = self.putRequest(obj.selfUrl, data = obj.get())
        if res:
            obj = self.getAPIObjectType(res)
            obj.set(obj = res)
            return obj
        else:
            return res

    def getFolder(self, resource):
        '''retrieve an folder based on the folderID

        :param resource: (str) selfUrl of the folder or the (int) folder ID
        :returns: the folder (APIFolder) 
        '''
        if isinstance(resource, int):
            resource = 'folders/' + str(resource)

        res = self.getRequest(resource)
        if res:
            folder = APIFolder()
            folder.set(obj = res)
            return folder
        else:
            return res

        
    def optionsRequest(self, resource):
        '''get list of available OPTIONs for a resource'''
        req = self.s.options(self.fullUrl(resource))
        return req.json()        

    def postRequest(self, resource, data):
        '''add data to an object

        :param resource: (str) relative path of the resource or selfUrl
        :param data: (json) data to be added to the resource
        :returns: the resource object (json)
        '''
        try:    
            req = self.s.post(self.fullUrl(resource), json = data)
            if req.status_code == requests.codes.created:
                return req.json()
            else: 
                return None
        except requests.exceptions.RequestException as err:
            print('request failed:',err)
            return None
  

    def putRequest(self, resource, data):
        ''' update data of an object 

        :param resource: (str) defines the relative path to the api resource
        :param data: (json) data to be added to the object
        :returns: the updated object (json)
        '''
        try:    
            req = self.s.put(self.fullUrl(resource), json = data)
            if req.status_code == requests.codes.ok:
                return req.json()
            else: 
                return None
        except requests.exceptions.RequestException as err:
            print('request failed:',err)
            return None
       

    def postRequestSimple(self, resource):
        '''get an empty resource 

        :param resource: (str) resource path
        :returns: the resource object (json)
        '''
        req = self.s.post(self.fullUrl(resource))
        return req.json()

    def putRequestSimple(self, resource):
        req = self.s.put(self.fullUrl(resource))
        return req.json()

    def delRequest(self, resource):
        ''' generic delete request

        :param resource: (str) resource path
        :returns: status_code (int)
        '''
        try: 
            req = self.s.delete(self.fullUrl(resource))
            if req.status_code == requests.codes.ok:
                print('resource {0} deleted, 200'.format(self.fullUrl(resource)))
                return req.status_code
            elif req.status_code == requests.codes.no_content:
                print('resource {0} deleted, 204'.format(self.fullUrl(resource)))
                return req.status_code
            else:
                print('resource {0} NOT (not existing or other problem) deleted'.format(self.fullUrl(resource)))
                return req.status_code

        except requests.exceptions.RequestException as err:
            print('del request failed:',err)
            return 

    def delObject(self, obj):
        '''
        delete an unvalidated object 

        :param obj: (APIObject) to object to delete
        :returns: status_code
        '''
        try: 
            req = self.s.delete(obj.selfUrl)
            if req.status_code == requests.codes.ok:
                print('object {0} deleted'.format(obj.id))
                return req.status_code

        except requests.exceptions.RequestException as err:
            print('del request failed:',err)
            req = None

    def publishObject(self, obj):
        '''
        publisch an unvalidated object 

        :param obj: (APIObject) to object to publish
        :returns: (APIObject) returns the object
        '''
        try: 
            req = self.s.put(obj.selfUrl + '/publish')
            if req.status_code == requests.codes.ok:
                print('object {0} published'.format(obj.id))
                return self.getObject(obj.selfUrl)


        except requests.exceptions.RequestException as err:
            print('del request failed:',err)
            req = None
        

    def searchTerm(self, resource, search ,mode = 'default'):
        ''' search a resource using oAuths
    
        :param resouce: (str) resource path
        :param search: (str) term to search for 
        :param mode: (str) search for partial match ('default') or exact match ('exact')
        :returns: list of folder objects (json)
        '''

        search = urlparse_quote(search)
        if mode == 'exact':
            url = self.fullUrl(resource) + '?$filter=Term%20eq%20%27{0}%27'.format(search) 
        else:
            url = self.fullUrl(resource) + '?$filter=startswith(Term,%27{0}%27)%20eq%20true'.format(search)

        req = self.s.get(url)
        return req.json()



    def uploadFile(self, filename):
        ''' 
        push (post) a file to the server

        :param filename: (Path) the file to be uploaded
        :returns: the file object containing the related object selfUrl
        :returns: file object (APIObject)
        '''
        try:
            data = filename.open(mode = 'rb').read()
            files  = { 'file' : (str(filename.name), data)}
        except:
            print ("opening file", filename, "failed, aborting")
            return

        res = self.s.post(self.url + 'upload', files = files)  
        if res.status_code == requests.codes.created:
            obj = self.getAPIObjectType(res)
            obj.set(obj = res)
            return obj
        else: 
            return res.status_code


    def chunkedread(self, fp, chunksize):
        '''
        breaks the file into chunks of chunksize

        :param fp: (Path) file
        :param chunksize: (int) size in bytes of the chunk parts
        :yields: chunk
        '''

        with fp.open('rb') as f:
            while True:
                chunk = f.read(chunksize)
                if not chunk:
                    break
                yield(chunk)

    def chunkFileUpload(self, fp, chunksize = 1024*4096):
        ''' 
        upload large files in chunks of max 100 MB size

        :param fp: (Path) file
        :param chunksize: (int) size in bytes of the chunk parts, default is 4MB
        :returns: the generated API Object
        '''
        parts = math.ceil(fp.stat().st_size/chunksize)
        part = 0
        err = False
        maxchunksize = 1024 * 1024 * 100
        if chunksize < maxchunksize:
            for chunk in self.chunkedread(fp, chunksize):
                part = part + 1
                print('uploading part {0} of {1}'.format(part,parts))
                files  = { 'file' : (str(fp.name), chunk)}
                res = self.s.post(self.url + 'chunked_upload?chunk={0}'.format(part), files = files)
                if res.status_code == requests.codes.ok:
                    print('uploaded part {0} of {1}'.format(part,parts))
                else:
                    err = True
        
            if not err:
                resource = 'chunked_upload/commit?filename={0}'.format(fp.name)
                res = self.postRequestSimple(resource)
                relObj = res['relatedObject']
                obj = self.getObject(relObj['selfUrl'])
              
                return obj
            else:
                return None
        else:
            print('no uploaded: defined chunksize {0} is bigger than the allowed maximum {1}'.format(chunksize, method))
            return None
 


    def getFile(self, resource):
        '''return a APIFile object
        
        :param resource: (str) resource path
        :returns: api file object (APIFile) or status code
        '''  
        if isinstance(resource, int):
            resource = 'files/' + str(resource)

        res = self.getRequest(resource)

        if not isinstance(res, int):
            fObj = APIFile()
            fObj.set(res)
            return fObj
        else: 
            return res
  


    def getObjectFiles(self, obj):
        '''return a list of file objects contained in an object

        :param obj: (APIObject) object 
        :returns: list of files(APIFiles)
        '''
        filelist = list()
        for of in obj.files:
            res = self.getFile(of['selfUrl'])
            if not isinstance(res, int):
                filelist.append(res)
        return filelist

    def fileObjectVersion(self,data):
        ''' 
        Extract VSDID and selfUrl of the related Object Version of the file after file upload

        :param data: (json) file object data
        :results: returns the id and the selfUrl of the Object Version
        '''
        #data = json.loads(data)
        f = data['file']
        obj = data['relatedObject']
        fSelfUrl = f['selfUrl']
        return obj['selfUrl'], self.getOID(obj['selfUrl'])

    def getLatestUnpublishedObject(self):
        ''' searches the list of unpublished objects and returns the newest object  '''
        res = self.getRequest('objects/unpublished')

        obj = self.getObject(res['items'][0].get('selfUrl'))
        return obj

   
                

    def getFolderByName(self, search, mode = 'default'):
        '''
        get a list of folder(s) based on a search string

        :param search: (str) term to search for 
        :param mode: (str) search for partial match ('default') or exact match ('exact')
        :returns: list of folder objects (APIFolders)
        '''   
        search = urlparse_quote(search)
        if mode == 'exact':
            url = self.url + "folders?$filter=Name%20eq%20%27{0}%27".format(search) 
        else:
            url = self.url + "folders?$filter=startswith(Name,%27{0}%27)%20eq%20true".format(search)

        res = self.s.get(url)
        if res.status_code == requests.codes.ok:
            result = list()
            res = res.json()
            for item in iter(res['items']):
                f = APIFolder()
                f.set(item)
                result.append(f)
            return result
        else:
            return res.status_code

    def getFileListInFolder(self, ID):
        ''' not implemented yet '''
        req = self.s.get(self.url+"folders/"+str(ID))
        return req.json()
       

    def searchOntologyTerm(self, search, oType = '0', mode = 'default'):
        '''
        Search ontology term in a single ontology resource. Two modes are available to either find the exact term or based on a partial match

        :param search: (str) string to be searched
        :param oType: (int) ontlogy resouce code, default is FMA (0)
        :param mode: (str) find exact term (exact) or partial match (default)
        :returns: ontology term entries (json)
        '''
        search = urlparse_quote(search)
        if mode == 'exact':
            url = self.url+"ontologies/{0}?$filter=Term%20eq%20%27{1}%27".format(oType,search) 
        else:
            url = self.url+"ontologies/{0}?$filter=startswith(Term,%27{1}%27)%20eq%20true".format(oType,search)

        res = self.s.get(url)
        if res.status_code == requests.codes.ok:
            result = list()
            res = res.json()
            for item in iter(res['items']):
                onto = APIOntology()
                onto.set(item)
                result.append(onto)
            return result
        else:
            return res.status_code


        
    def getOntologyTermByID(self, oid, oType = "0"):
        '''
        Retrieve an ontology entry based on the IRI

        :param oid: (int) Identifier of the entry
        :param oType: (int) Resource type, available resources can be found using the OPTIONS on /api/ontologies). Default resouce is FMA (0)
        :returns: ontology term entry (json)
        '''

        url = self.url + "ontologies/{0}/{1}".format(oType,oid)
        req = self.s.get(url)
        return req.json()


    def getLicenseList(self):
        ''' retrieve a list of the available licenses (APILicense)'''
        res = self.getRequest('licenses')
        license = list()
        if res:
            for item in iter(res['items']):
                lic = APILicense()
                lic.set(obj = item)
                license.append(lic)
        return license

    def getObjectRightList(self):
        ''' retrieve a list of the available base object rights (APIObjectRights) '''
        res = self.getRequest('object_rights')
        permission = list()
        if res:
            for item in iter(res['items']):
                perm = APIPermission()
                perm.set(obj = item)
                permission.append(lic)
        
        return permission

    def getModalityList(self):
        ''' retrieve a list of modalities objects (APIModality)'''

        modalities = list()
        items = self.getAllPaginated('modalities', itemlist = list())
        if items:
            for item in items:
                modality = APIModality()
                modality.set(obj = item)
                modalities.append(modality)
            return modalities
        else:
            return items

    def readFolders(self,folderList):
    #first pass: create one entry for each folder:
        folderHash={}
        for folder in folderList['items']:
            ID=folder['id']
            folderHash[ID]=Folder()
            folderHash[ID].ID=ID
            folderHash[ID].name=folder['name']
            folderHash[ID].childFolders=[]
       
    #second pass: create references to parent and child folders
        for folder in folderList['items']:
            ID=folder['id']
            if (folder['childFolders']!=None):
            #print (folder['childFolders'],ID)
                for child in folder['childFolders']:
                    childID=int(child['selfUrl'].split("/")[-1])
                    if (folderHash.has_key(childID)):
                        folderHash[ID].childFolders.append(folderHash[childID])
            if (folder['parentFolder']!=None):
                parentID=int(folder['parentFolder']['selfUrl'].split("/")[-1])
                if (folderHash.has_key(parentID)):
                    folderHash[ID].parentFolder=folderHash[parentID]
            if (not folder['containedObjects']==None):
                folderHash[ID].containedObjects={}
                for obj in folder['containedObjects']:
                    objID=obj['selfUrl'].split("/")[-1]
                    folderHash[ID].containedObjects[objID]=obj['selfUrl']

        #third pass: gett full path names in folder hierarchy
        for key, folder in folderHash.iteritems():
            folder.getFullName()

        return folderHash

            
    def addLink(self, obj1, obj2):
        ''' add a object link 

        :param obj1: (APIBasic) an link object with selfUrl 
        :param obj2: (APIBasic) an link object with selfUrl
        :returns: the created object-link (json)
        '''
        link = APIObjectLink()
        link.object1 = dict([('selfUrl', obj1.selfUrl)])
        link.object2 = dict([('selfUrl', obj2.selfUrl)])
        
        return  self.postRequest('object-links', data = link.get())





    
    def createFolderStructure(self, rootfolder, filepath, parents):
        ''' 
        creates the folders based on the filepath if not already existing, 
        starting from the rootfolder

        :param rootfolder: (APIFolder) the root folder
        :param filepath: (Path) file path of the file
        :param parents: (int) number of partent levels to create from file folder 
        :returns: (APIFolder) the last folder in the tree
        '''
         
        fp = filepath.resolve()
        folders = list(fp.parts)
        folders.reverse()

        ##remove file from list
        if fp.is_file():
           folders.remove(folders[0])
            
        for i in range (parents, len(folders)):
            folders.remove(folders[i])

        folders.reverse()
        fparent = rootfolder

        if fparent:
            for fname in folders:
                fchild = None
                if fparent:
                    if fparent.childFolders:
                        for child in fparent.childFolders:
                            fold = self.getFolder(child['selfUrl'])
                            if fold.name == fname:
                                fchild = APIFolder()
                                #fchild.set(obj = fold.get())
                                fchild = fold
                if not fchild:
                    f = APIFolder()
                    f.name = fname
                    f.parentFolder = dict([('selfUrl',fparent.selfUrl)])
                   # f.toJson()
                    res = self.postRequest('folders', f.get())
                    fparent.set(obj = res)
                    
                else:
                    fparent = fchild
                   
            return fparent
        else: 
            print('Root folder does not exist', rootfolder)
            #jData = jFolder(folder)
            return None



    def addObjectToFolder(self, target, obj):
        '''
        add an object to the folder
    
        :param target: (APIFolder) the target folder 
        :param obj: (APIObject) the object to copy
        :returns: updated folder (APIFolder)
        '''    
        objSelfUrl = dict([('selfUrl',obj.selfUrl,)])
        objects = target.containedObjects
        if not objects:
            objects = list()
        if objects.count(objSelfUrl) == 0:
            objects.append(objSelfUrl)
            target.containedObjects = objects
            res = self.putRequest('folders/', data = target.get())
            if not isinstance(res, int):
                target = APIFolder()
                target.set(obj = res)
                return target
            else:
                return res
        else:
            return target



        
class APIBasic(object):
    """docstring for APIBasic"""


    oKeys = list([
        'id',
        'selfUrl',
        ])

    def __init__(self, oKeys = oKeys):
        for v in oKeys:
                setattr(self, v, None)
        
    def set(self, obj = None):
        ''' sets class variable for each key in the object to the keyname and its value'''
        if  obj:
            for v in self.oKeys:
                if v in obj: 
                    setattr(self, v, obj[v])              
        else:
            for v in self.oKeys:
                setattr(self, v, None)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return self.__dict__


class APIObject(APIBasic):
    '''
    API Object
    ''' 
    oKeys = list([
        'name',
        'type',
        'description',
        'objectGroupRights',
        'objectUserRights',
        'objectPreviews',
        'createdDate',
        'modality',
        'ontologyItems',
        'ontologyItemRelations',
        'ontologyCount',
        'license',
        'files',
        'linkedObjects',
        'linkedObjectRelations',
        'downloadUrl'
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self, ):
        super(APIObject, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObject, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObject, self).get()


class APIObjectRaw(APIObject):
    """docstring for APIObjectRaw"""
    oKeys = list([
        'sliceThickness',
        'spaceBetweenSlices',
        'kilovoltPeak'
        ])

    for i in APIObject.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObject, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObject, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObject, self).get()

class APIObjectSeg(APIObject):
    """docstring for APIObjectSeg"""
    oKeys = list([
        'SegmentationMethod',
        'SegmentationMethodDescription'
        ])
    

    for i in APIObject.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObject, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObject, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObject, self).get()

class APIObjectSm(APIObject):
    """docstring for APIObjectSm"""
    oKeys = list()

    for i in APIObject.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObject, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObject, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObject, self).get()

class APIObjectCtDef(APIObject):
    """docstring for APIObjectCtDef"""
    oKeys = list()

    for i in APIObject.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObject, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObject, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObject, self).get()

class APIObjectCtData(APIObject):
    """docstring for APIObjectCtData"""
    oKeys = list()

    for i in APIObject.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObject, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObject, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObject, self).get()



class APIFolder(APIBasic):
    '''
    Folder API Object
    '''
    oKeys = list([
        'name',
        'level',
        'parentFolder',
        'childFolders',
        'folderGroupRights',
        'folderUserRights',
        'containedObjects'
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIFolder, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIFolder, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIFolder, self).get()
  
class APIOntology(APIBasic):
    '''
    API class for ontology entries
    '''
    oKeys = list([
        'term',
        'type',
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIOntology, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIOntology, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIOntology, self).get()

class APIObjectOntology(APIBasic):
    '''
    API class for object-ontology entries
    '''
    oKeys = list([
        'type',
        'object',
        'ontologyItem',
        'position'
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObjectOntology, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObjectOntology, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObjectOntology, self).get()

class APIFile(APIBasic):
    '''
    API class for files
    '''
    oKeys = list([
        'createdDate',
        'downloadUrl',
        'originalFileName',
        'anonymizedFileHashCode',
        'size',
        'fileHashCode'
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIFile, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIFile, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIFile, self).get()



class APILicense(APIBasic):
    '''
    API class for licenses
    '''
    oKeys = list([
        'description',
        'name',
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APILicense, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APILicense, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APILicense, self).get()

class APIObjecRight(APIBasic):
    '''
    API class for object rights
    '''
    oKeys = list([
        'description',
        'name',
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObjecRight, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObjecRight, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObjecRight, self).get()
   

class APIObjectLink(APIBasic):
    '''
    API class for object links
    '''
    oKeys = list([
        'description',
        'object1',
        'object2',
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIObjectLink, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIObjectLink, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIObjectLink, self).get()

class APIModality(APIBasic):
    '''
    API class for modalities
    '''
    oKeys = list([
        'description',
        'name'
        ])

    for i in APIBasic.oKeys:
        oKeys.append(i)

    def __init__(self):
        super(APIModality, self).__init__(self.oKeys) 

    def set(self, obj = None):
        super(APIModality, self).set(obj = obj)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return super(APIModality, self).get()

class APIPagination(object):
    '''
    API class for Pagination results
    '''
    oKeys = list([
        'totalCount',
        'pagination',
        'items',
        'nextPageUrl'
        ])

    def __init__(self, oKeys = oKeys):
        for v in oKeys:
                setattr(self, v, None)
        
    def set(self, obj = None):
        ''' sets class variable for each key in the object to the keyname and its value'''
        if  obj:
            for v in self.oKeys:
                if v in obj: 
                    setattr(self, v, obj[v])              
        else:
            for v in self.oKeys:
                setattr(self, v, None)

    def get(self):
        '''transforms the class object into a json readable dict'''
        return self.__dict__
                                           
                                         
