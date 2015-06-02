#How to upload files



1.Import libs

    from pathlib import Path, PurePath, WindowsPath
    import connectVSD

2.connect to demo, or use username and password and url parameters

    api=connectVSD.VSDConnecter()

3.define filepath

    fp = Path('C:' + os.sep, 'test', 'test.nii')

## Files < 1 GB

4.upload using the uploadFile

    obj = api.uploadFile(fp)

5.check the object

    print(obj.selfUrl)
    https://demo.virtualskeleton.ch/api/objects/1


## Files > 1 GB 

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