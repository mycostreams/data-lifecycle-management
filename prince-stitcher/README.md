# Description

Dockerized image stiticher using FIJI for Prince Images.

The stitcher takes images from `/opt/fiji/input/<FOLDER>` and creates a stitched output in `/opt/fiji/output/<FOLDER>`.
`<FOLDER>` is provided into the docker image as an environment variable. These directories can be mounted as volumes in the docker image.

The folder structure in the input directory is assumed to have the form:

```
|- <FOLDER>
|  |- Img
|     |- Img_r01_c01.tif
      |- ...
```

The resulting structure in the output directory has the form
```
|- <INPUT FOLDER>
|  |- Image stitch1.tif
|  |- imageStitch.txt
|  |- imageStitch.txt.registered
```

The stitcher first resizes the images, then applies the stitching.

To run:
```bash
docker compose run --rm fiji-stitcher
```