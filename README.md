# Yeezy-Taught-Me

## Required dependencies

### System libraries

#### HD5F client binary (Linux)

**Download and copy the compiled headers and files:**

    wget http://www.hdfgroup.org/ftp/HDF5/current/bin/linux-x86_64/hdf5-1.8.12-linux-x86_64-shared.tar.gz
    tar xvfz hdf5-1.8.12-linux-x86_64-shared.tar.gz
    cd hdf5-1.8.12-linux-x86_64-shared
    cd bin
    sudo cp * /usr/bin
    cd ..
    cd lib
    sudo cp * /usr/lib
    cd ..
    cd include
    sudo cp * /usr/include
    cd ..
    cd share
    sudo cp -a * /usr/share
    cd /usr/lib

**Edit ~/.bashrc:**

    export LD_LIBRARY_PATH="/usr/lib/"

**Source .bashrc:**

    . ~/.bashrc

### Python libraries

- Of course: pandas, numpy, maplotlib, seaborn, etc.
- h5py
- tables
- plotly

### The Million Song Susbet

Download and uncompress the tar ball:

- `wget http://static.echonest.com/millionsongsubset_full.tar.gz`
- `mkdir assets`
- `mkdir data`
- `tar -xf millionsongsubset_full.tar.gz -C assets/data/`

## Create datasets
`make data`

## Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.testrun.org
