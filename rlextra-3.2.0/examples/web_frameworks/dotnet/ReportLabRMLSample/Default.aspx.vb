Partial Public Class _Default
    Inherits System.Web.UI.Page

    Protected Sub Page_Load(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.Load

    End Sub

    Protected Sub Button1_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles Button1.Click

        'create strings containing the relevant paths
        Dim rmlDir As String = "C:\code\rlextra\rml2pdf\"   'change this to your rml2pdf directory
        Dim rmlExe As String = "rml2pdf.pyc"                'the rml2pdf python module
        Dim rmlFile As String = "hello.rml"                 'the name of our RML template
        Dim rmlFilePath = System.AppDomain.CurrentDomain.BaseDirectory

        ' When the web form button is clicked, a 'process' object is created to run Python,
        ' and the relevant command line arguments are passed to it.
        Dim pythonProcess As Process
        Dim pythonPSI As ProcessStartInfo
        pythonPSI = New ProcessStartInfo("python")
        pythonPSI.WorkingDirectory = rmlDir
        pythonPSI.UseShellExecute = False
        pythonPSI.CreateNoWindow = True
        pythonPSI.RedirectStandardOutput = True
        pythonPSI.RedirectStandardError = True

        'Now the RML template is merged with the data in the web form, creating a temporary RML file,
        'and a command line is constructed to pass to the Python executable.  
        'The result is a command line in the format:
        ' <path>rml2pdf.pyc <path>rmlfile.txt
        'which returns the path to the resulting pdf document.
        pythonPSI.Arguments = rmlDir & rmlExe & " " & """" & CreateDynamicRML(rmlFilePath, rmlFile, TextBox1.Text) & """"

        pythonProcess = New Process()
        pythonProcess.StartInfo = pythonPSI
        pythonProcess.Start()

        If pythonProcess.StandardError.ReadLine() = "" Then

            'rml2pdf returns the name of the created pdf document.
            Dim outputPDF As String = System.IO.Path.GetTempPath & pythonProcess.StandardOutput.ReadLine()
            'convert the file into a byte stream
            Dim input As New IO.FileStream(outputPDF, IO.FileMode.Open)
            Dim reader As New IO.BinaryReader(input)
            Dim bytes() As Byte
            bytes = reader.ReadBytes(CInt(input.Length))
            input.Close()

            'send the byte stream to the http response object
            Response.Clear()
            Response.Buffer = True
            Response.Expires = 0
            Response.AddHeader("Content-Disposition", "attachment;filename=ReportLabRMLSample.pdf")
            Response.BinaryWrite(bytes)
            Response.End()

        Else

            'send the error to the http response object
            Response.Clear()
            Response.Write(pythonProcess.StandardError.ReadToEnd())
            Response.End()

        End If

    End Sub

    'function to copy the rml template to the temp directory and return the full path to it
    Private Function CreateRML() As String
        Dim filename As String

        System.IO.File.Copy(System.AppDomain.CurrentDomain.BaseDirectory & "hello.rml", System.IO.Path.GetTempPath & "hello.tmp.rml", True)
        filename = """" & System.IO.Path.GetTempPath & "hello.tmp.rml" & """"

        Return filename

    End Function

    'Function to substitute a variable in the RML template, and write out a temporary RML file for conversion to PDF.
    'The point is to dynamically replace parts of the template;  this could be done in any number of ways 
    'but for the sake of simplicity we've chosen a simple text search and replace on one field.  A more advanced approach
    'would use a dedicated templating engine to construct the RML
    Private Function CreateDynamicRML(ByVal rmlTemplatePath As String, ByVal rmlTemplateName As String, ByVal name As String) As String
        Dim tmpFileName As String = System.IO.Path.GetTempPath & rmlTemplateName & ".tmp"
        Dim sr As IO.StreamReader = New IO.StreamReader("" & rmlTemplatePath & rmlTemplateName & "")
        Dim sw As IO.StreamWriter = New IO.StreamWriter(tmpFileName)
        Dim txt As String

        txt = sr.ReadToEnd
        txt = txt.Replace("##NAME##", name)
        sw.Write(txt)
        sw.Close()

        Return tmpFileName

    End Function

End Class