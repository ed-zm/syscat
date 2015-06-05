
"encrypt example 1 to demonstrate the encryption feature"

def test(filename="example_1.rml"):
    from rlextra.utils import pdfencrypt
    from rlextra.rml2pdf import rml2pdf
    encryption = pdfencrypt.StandardEncryption("User", None, canPrint=1, canModify=0, canCopy=0, canAnnotate=0)
    text = open(filename).read()
    result = rml2pdf.go(text, encryption=encryption)
    print(result.filename, "encrypted with user password User and no Owner password")

if __name__=="__main__":
    import sys
    try:
        filename = sys.argv[1]
    except:
        print("processing example_1.rml to process another file provide a filename argument")
        test()
    else:
        test(filename)

        
    
	