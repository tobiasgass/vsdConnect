#How to upload files
Chunk upload can be used on all files. Howevery, the limit for the standard upload is 1 GB. Additionally, upload of file >500 MB tend to be slower. Therefore, we recommend to use chunk upload for file > 500 MB


1.Import libs

    from pathlib import Path, PurePath, WindowsPath
    import connectVSD

2.connect to demo, or use username and password and url parameters

    api=connectVSD.VSDConnecter()

3.define filepath

    fp = Path('C:' + os.sep, 'test', 'test.nii')

## Files < 500 MB

4.upload using the uploadFile

    obj = api.uploadFile(fp)

5.check the object

    print(obj.selfUrl)
    https://demo.virtualskeleton.ch/api/objects/1


## Files > 500 MB 

4.define chunk size to eg. 8 MB if you dont want to use the default 4MB

    chunk = 1024 * 4096 * 2

5.upload using the chunkFileUpload
    
    obj = api.chunkFileUpload(fp, chunksize = chunk)

console output

    uploading part 1 of 3
    uploaded part 1 of 3
    uploading part 2 of 3
    uploaded part 2 of 3
    uploading part 3 of 3
    uploaded part 3 of 3

6.check the object

    print(obj.selfUrl)
    https://demo.virtualskeleton.ch/api/objects/1