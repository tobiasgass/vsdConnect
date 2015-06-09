# README #

This library implements a client for the REST API of the virtualskeletondatabase (www.virtualskeleton.ch). It supports authentication, general queries, and specific requests such as image upload/download, object linking and right management. Examples are provided in the examples directory. Please use 'demo.virtualskeleton.ch' for testing purposes.

## What is different in this Fork
- Pyhton 3 (3.4.3)
- usage of **requests** package instead of urllib2
- usage of **pathlib** instead of os.path
- support file poster.py removed (no needed with requests)
- introduction of API classes
- Added SAML auth 
- Added chunk Upload (upload files > 500 MB) 
 

### What is this repository for? ###

* Quick summary: connect to vsd
* Version: 0.1

### How do I get set up? ###

Just add the source directory to your PYTHONPATH

### Contribution guidelines ###

* Write exception handling
* Writing tests
* Code review
* Adding sockets/timeouts/retries
* Adding more stable support for pagination
* Add general file upload
* Write some sort of GUI example

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact