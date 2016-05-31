#!/usr/bin/env python
import sys, os.path, glob
sys.path.append(os.path.dirname(__file__))
import meloDOCmatic

PROJDIR = os.path.join(os.path.dirname(__file__), '..')
DOCDIR = os.path.join(PROJDIR, 'doc')
OUTDIR = os.path.join(PROJDIR, 'doc', 'html')
TEMPLATEFN = os.path.join(OUTDIR, 'template.html')

for docfn in glob.glob(DOCDIR+'/*.melodomatic'):
    print docfn
    h = meloDOCmatic.document(TEMPLATEFN, docfn)
    bn, ext = os.path.splitext(os.path.basename(docfn))
    outfp = open(os.path.join(OUTDIR, bn+'.html'), 'w')
    outfp.write(h)
    outfp.close()

