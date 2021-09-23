# NASA Lunar Mission Coregistration Tool (LMCT) :crescent_moon:
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)


The Lunar Mission Coregistration Tool (LMCT) processes publicly available imagery files from past lunar missions and enables manual comparison to imagery from the Lunar Reconnaissance Orbiter (LRO) mission. The imagery processed by this tool can be used in existing citizen science applications to identify long lost spacecraft components -- such as The Eagle, the lunar module that returned Buzz and Neil back to the command module on the first Lunar Mission and has since been lost to time. It can also be used to identify and examine recent natural impact features on the lunar surface by comparing the old images against the new images. This is known as image (co)-registration in the field of computer vision. The LMCT and its use will allow us to better understand what’s been going on on the moon for the past sixty years (maybe now is when we’ll discover if it’s really made of cheese).

This application has both a command line interface (CLI) and graphical user itnerface (GUI).

**Valid Inputs:**
- ISIS Cubes
- GeoTIFFs
- JPEG2000
- **Note:** images that do not include valid metadata that specify the Lunar projection, extent, resolution, and bits/pixel will be rejected by the application

**Output:** The application software outputs the co-registered images in GeoTiff format with the associated metadata and high-quality graphics.

####


## Installation and Build Procedure
This tool runs on Linux environments, according to [ISIS3 prerequisites]( https://github.com/USGS-Astrogeology/ISIS3#operating-system-requirements).


### ISIS Installation 
General ISIS installation described [here](https://github.com/USGS-Astrogeology/ISIS3#isis-installation-with-conda).

### Download ISIS Data 
After ISIS library installation is complete it’s necessary to download some data to ensure ISIS works correctly. Note that each line is it's own command.

```
python $CONDA_PREFIX/scripts/isis3VarInit.py
conda activate isis
cd $ISISDATA
rsync -azv --delete --partial isisdist.astrogeology.usgs.gov::isisdata/data/base .
rsync -azv --delete --partial isisdist.astrogeology.usgs.gov::isisdata/data/apollo15 .
rsync -azv --delete --partial isisdist.astrogeology.usgs.gov::isisdata/data/apollo16 .
rsync -azv --delete --partial isisdist.astrogeology.usgs.gov::isisdata/data/apollo17 .
mkdir -p lro
cd $ISISDATA\lro
rsync -azv --delete --partial isisdist.astrogeology.usgs.gov::isisdata/data/lro/calibration .
```

### Increasing The Maximum Size of ISIS Cube
Apollo panoramic images are huge and importing them into ISIS exceeds default cube maximum size. The default value is 12 GB, so it’s necessary to set the cube size to at least 30.

In the $ISISROOT/IsisPreferences file:
```
Group = CubeCustomization
  #MaximumSize = 12
  MaximumSize = 100
EndGroup
```
### Fix to Support Apollo Panoramic Images By findimageoverlaps Command
It seems the current ISIS version has a small bug and includes the wrong instrument specification for Apollo panoramic images. This causes `findimageoverlaps` command to fail. To fix this issue, it’s necessary to change  `$ISISROOT/appdata/translations/Instruments.trn` file as shown below:

```
Group = InstrumentName
  # Apollo
  #Translation   = (Panoramic, PAN)
  Translation   = (Panoramic, APOLLO_PAN)
```

### Install Python Libraries
Install Python libraries used by solution. Mamba’s installation is optional but speed up the process.
```
conda activate base
conda config --env --add channels conda-forge
conda install mamba
conda activate isis
conda install kalasiris click pandas flask WTForms Flask-WTF
conda install notebook
```

## Using the CLI
Before any tool usage it’s necessary to activate “isis” Anaconda environment:
```
conda activate isis
``` 
Run `cli.py` to perform images co-registration; two missions must be declared in the command line between Apollo15 (16, 17), LO and LROC. For example:

```
python cli.py --apollo15 </path/to/folder/with/apollo15/images> --lro </path/to/folder/with/lroc/images> --output_folder /path/to/empty/folder
``` 
- For details regarding the meaning of parameters please check CLI Parameters
- Passed images must overlaps, for example if an Apollo15 image does not overlaps with a LROC image, the tool terminates with a message for the user
- The folder containing Apollo15 images must also contain their label files (.lbl extension)

### CLI Parameters
`cli.py` arguments:
- `--apollo15 TEXT` - Path to the folder containing LBL files associated to Apollo15 images (_optional_)
-  `--lro TEXT` - Path to the folder containing LROC image files (_optional_)
-  `--lo TEXT` - Path to the folder containing LO image files (_optional_)
-  `--output_folder TEXT` - Folder used to save co-registration resources (_optional_)
-  `--help` - Outputs information on all other commands/parameters

