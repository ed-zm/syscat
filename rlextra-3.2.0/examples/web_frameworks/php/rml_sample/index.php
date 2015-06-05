<?php

/*
This is a sample project which takes user input from an HTML form and generates a PDF containing what the user submitted. An RML file is read which contains the structure of the PDF document. A simple 'str_replace' replaces a variable name in the RML source with the value submitted by the user.

A similar principal could be used for generating personalised documents and mail merges by adding more fields such as address and post/zip code. For more advanced uses such as conditionals and for loops, users will probably want make use of a template engine such as Smarty or ReportLab's own Preppy.
*/

$PYTHON = "python";  # You can use a custom python build/version
$PYTHONPATH = "\$PYTHONPATH";  # Override PYTHONPATH if you installed somewhere unusual
$RML2PDF_DIR = "/path/to/rlextra/rml2pdf/";  # Where you installed rlextra
$RML2PDF_EXE = "rml2pdf.pyc";  # RML2PDF compiled python file
$RML_INPUT = "hello.rml";  # RML document source
$RML_OUTPUT = "output.rml";  # temporary location for RML after template processing


# If a GET parameter is supplied, generate and return a PDF, otherwise show a form where the user can fill in their name.
if ($_GET['q']) {
    # Call function that reads RML file and does templating replacements
    $rml_fn = getRML($RML_INPUT, $RML_OUTPUT, $_GET['q']);

    # Execute the python command with rml2pdf.pyc and relevant arguments 
    exec("PYTHONPATH=$PYTHONPATH $PYTHON $RML2PDF_DIR$RML2PDF_EXE $rml_fn");

    # Output file name
    $fn = str_replace(".rml", ".pdf", $RML_INPUT);

    # Check a PDF file was created
    $fh = fopen($RML_OUTPUT, 'r') or die("Can't open  PDF file $fn");
    fclose($fh);

    # Send PDF file to browser and appropriate headers
    header("Content-type: application/pdf");
    header("Content-disposition: attachment; filename=$fn");
    readfile($fn);
}
else { 
?>

<html>
<head>
    <title>Create a PDF</title>
</head>
<body>
    <h1>Create a dynamic PDF!</h1>
    <p>Enter your name:</p>
    <form action="." method="get">
        <input type="text" name="q" />
        <br />
        <input type="submit" value="Make a PDF" />
    </form>
</body>
</html>

<?php
}


function getRML($RML_INPUT, $RML_OUTPUT, $name) {
    # Get content of the RML file
    $rml = file_get_contents($RML_INPUT) or die("Can't open input RML file $RML_INPUT");

    # Replace special string '##NAME##' with the variable submitted as GET request
    # This is the simplest example of templating. You can use your preferred templating system here instead (e.g. Smarty or Preppy) for more control such as iteration loops.
    $rml = str_replace("##NAME##", $name, $rml);

    # Write the new RML string to a temporary file so it can be passed in as an argument to the RML2PDF script
    $fh = fopen($RML_OUTPUT, 'w') or die("Can't open output RML file $RML_OUTPUT");
    fwrite($fh, $rml);
    fclose($fh);

    return $RML_OUTPUT;
}

?>

