def main(fn):
    import os
    from reportlab.lib.utils import open_and_read
    from reportlab.lib.pdfencrypt import encryptPdfInMemory
    pdf_bytes = open_and_read(fn)
    ofn = os.path.splitext(os.path.basename(fn))[0]
    with open(ofn+'-encrypted.pdf','wb') as f:
        f.write(encryptPdfInMemory(pdf_bytes, 'master', 'user', canModify=0, canCopy=0, strength=128))

if __name__=='__main__':
    import sys
    main(sys.argv[1])
