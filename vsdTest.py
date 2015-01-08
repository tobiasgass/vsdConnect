#!/usr/bin/python

import connectVSD
import sys


#con=connectVSD.VSDConnecter("username","password")
#con=connectVSD.VSDConnecter()
con=connectVSD.VSDConnecter("Z2Fzc3RAdmlzaW9uLmVlLmV0aHouY2g6VGgxbktiVj0=")
con.downloadFile(56738)
