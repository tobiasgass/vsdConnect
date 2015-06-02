# How to connect to the chic data repo API (dev)

1. grab the xml file from the repo and add your credential (cdr-dev-chic.ics.forth.gr.xml)
2. download the [connectVSD](https://github.com/mrkistler/vsdConnect/)

## Coding
1.Import libs

    from pathlib import Path, PurePath, WindowsPath
    import connectVSD

2.load the xml with your credentials

    authfile = Path('cdr-dev-chic.ics.forth.gr.xml')

3.create the encoded token with the xml file

    enctoken = connectVSD.samltoken(authfile)

4.connect to the API using the token and authtype SAML

    api=connectVSD.VSDConnecter(authtype = "saml", url='https://cdr-dev-chic.ics.forth.gr/api/', token = enctoken)

5.create a generic request to query all available objects

    r = api.getRequest('objects')

6.result (here, no objects on the server)

    print(r)

    {'pagination': {'page': 0, 'rpp': 50}, 'totalCount': 0, 'nextPageUrl': None, 'items': []}
