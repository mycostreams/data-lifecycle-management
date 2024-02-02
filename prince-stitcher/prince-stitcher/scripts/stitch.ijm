macro StitchingLoop40even{

    ///////////////////////////////////////////////////////////////////////////////////
    //Asking for the directory where are the folders with the images to be stitched
    mainDirectory = '/opt/fiji/data';
    folderName = getArgument();

    fileNames       = "Img_r{yy}_c{xx}.tif";
    outputFile      = "imageStitch.txt";
    registeredOutputFile = outputFile + ".registered";

    overlap         = "20";  

    gridSizeX       = "15"
    gridSizeY       = "10"
    gridSizeZ       = "1"

    startX          = "1"
    startY          = "1"

    fal             = "1";
    rth             = "0.1";
    mdt             = "6";
    adt             = "6";


    ///////////////////////////////////////////////////////////////////////////////////////

    root = folderName + File.separator + "Img"

    inputDirectory = mainDirectory + File.separator + "input" + File.separator + root;
    outputDirectory = mainDirectory + File.separator + "output" + File.separator + folderName;
    tmpDirectory =  "/tmp" + File.separator + folderName;

    // Resize images
    File.makeDirectory(tmpDirectory);

    fileList = getFileList(inputDirectory);
    for (j=0; j<=fileList.length-1; j++){
        if(startsWith(fileList[j],"Img_r")){
            open(inputDirectory + File.separator + fileList[j]);
            run("Size...", "width=1024 depth=1 constrain average interpolation=Bilinear");
            saveAs("Tiff", tmpDirectory + File.separator + fileList[j]);
            close();
        }
    }

    // Stitch the resized images
    srcDirectory = tmpDirectory;
    File.makeDirectory(outputDirectory);

    cmd =  "grid_size_x=" + gridSizeX + " grid_size_y=" + gridSizeY + " grid_size_z=" + gridSizeZ + " overlap=" + overlap + " input=" + srcDirectory + " file_names=" + fileNames + " rgb_order=rgb output_file_name=" + outputFile + " output=" + outputDirectory + " start_x=" + startX + " start_y=" + startY + " start_z=1 start_i=1 channels_for_registration=[Red, Green and Blue] fusion_method=[Linear Blending] fusion_alpha=" + fal + " regression_threshold=" + rth + " max/avg_displacement_threshold=" + mdt + " absolute_displacement_threshold=" + adt + " compute_overlap";

    run("Stitch Sequence of Grids of Images", cmd);

    // Move image products ...
    File.rename(srcDirectory + File.separator + outputFile, outputDirectory + File.separator + outputFile);
    File.rename(srcDirectory + File.separator + registeredOutputFile, outputDirectory + File.separator + registeredOutputFile);

}
