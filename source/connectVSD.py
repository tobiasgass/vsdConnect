#!/usr/bin/python

# connectVSD 0.1
# (c) Tobias Gass, 2015
# conncetVSD 0.1 python 3 @Michael Kistler 2015

import sys
import os
import urllib.request, urllib.error, urllib.parse, urllib
import json
import getpass
from pathlib import Path, PurePath, WindowsPath
import requests

requests.packages.urllib3.disable_warnings()


class VSDConnecter:
    APIURL='https://demo.virtualskeleton.ch/api/'

  
    
    def __init__(self,
        url = "https://demo.virtualskeleton.ch/api/",
        username = "demo@virtualskeleton.ch", 
        password = "demo", 
        version = ""):
        
        self.username = username
        self.password = password
        if version:
            version = str(version) + '/'
        self.url = url + version
        
        self.s = requests.Session()
        self.s.auth = (self.username, self.password)
        self.s.verify = False
        

 
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
        res = urllib.parse.urlparse(str(resource))

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
        
        

    def getOID(self, selfURL):
        ''' 
        extracts the last part of the selfURL, tests if it is a number

        :param selfURL: (str) url to the object
        :returns: either None if not an ID or the object ID (int)
        :raises: ValueError
        '''
        oID = Path(urllib.parse.urlsplit(selfURL).path).name
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
                print('resource {0} deleted'.format(self.fullUrl(resource)))
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

        search = urllib.parse.quote(search)
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
        search = urllib.parse.quote(search)
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
        search = urllib.parse.quote(search)
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
        res = self.s.getRequest('licenses')
        license = list()
        if res:
            for item in iter(res['items']):
                lic = APILicense()
                lic.set(obj = item)
                license.append(lic)
        return license

    def getObjectRightList(self):
        ''' retrieve a list of the available base object rights (APIObjectRights) '''
        res = self.s.getRequest('object_rights')
        permission = list()
        if res:
            for item in iter(res['items']):
                perm = APIPermission()
                perm.set(obj = item)
                permission.append(lic)
        
        return permission

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
                                    



