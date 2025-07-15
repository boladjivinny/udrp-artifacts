# Data and source code used for our empirical analysis of UDRP decisions published between December 1999 and August 2024
This repository contains the raw and curated UDRP proceedings data used in our paper "Repairing Trust in Domain Name Disputes Practices: Insights from a Quarter-Century’s Worth of Squabbles" to appear in the proceedings of the Network and Distributed Systems Security Symposium (NDSS) 2026.
In addition to the data, we share the reference named entity recognition model (NER) used in the paper and code to self-train a model, and run the experiments described in the paper.
The user of this repository should be able to:

1. [Train a custom NER model](#1-train-a-custom-ner-model)
2. [Extract information from UDRP proceedings](#2-extract-information-from-udrp-proceedings)
3. [Assess the prevalence of forum shopping](#3-assess-the-prevalence-of-forum-shopping)
4. [Estimate delays observed in UDRP disputes](#4-estimate-delays-observed-in-udrp-disputes)

## Requirements
### Hardware requirements
Though not required, we advise running these experiments using a machine powered with a modern GPU.

### Software requirements
- Python 3.7+ (tested with Python 3.10.12)
- The Python libraries specified in `requirements.txt`
- A functional spaCy installation. Follow the instructions on the [official website](https://spacy.io/usage) to configure your installation command. For the options, make the following selections:
    - For *Configuration*, select both "virtual env" and "train models".
    - For *Trained pipelines*, select English.
    - For *Select for pipeline*, select accuracy. 
- **Note**: The trained pipeline only works with spaCy 3.7.6 which you can install by adding `==3.7.6` at the end of the relevant installation command. For example, with pip, the new command could be `pip install -U spacy==3.7.6` or `pip install -U 'spacy[cuda11x]==3.7.6'`

## Installation
- Download the repository content from [repo] and uncompress the ZIP archive.
- Create a Python virtual environment and activate it.
- Install spaCy following the instructions above.
- Install [gdown](https://pypi.org/project/gdown/)

## Directory structure (important elements)
```
+ chatgpt_prompts                           : Dumps of the prompts used on ChatGPT for de-duplicating some extracted details
+ code/                                     : Python source codes
+ data/                                     : relevant data for the analysis
+ model/                                    : folder to save user's trained NER model to
+ packages/                                 : folder containing the installable Python packages
+ resources/                                : files used for generating transformations, and training the models
    + model_best/                           : checkpoint of the trained NER model used for the paper
+ results/                                  : Destination folder for the results from the experiments
```

## Using the artifact
### 1. Train a custom NER model
- First download the dataset of UDRP decisions using the commands below
```bash
gdown https://drive.google.com/file/d/1gKPtr7qzL3JM6RDUmR3Ch54qOlqz4TMf/view?usp=drive_link
mv disputes-content.jsonl.gz data/
```
- Create random training and testing data sets using the command below
> python3 code/e1.sample-ner-datasets.py data/disputes-content.jsonl.gz data/annotated-udrp-corpus.jsonl.gz data/

The script uses the corpus of proceedings and the annotated subset to generate training, and testing *.spacy files for each provider individually and as a whole. The files are saved under the `data` folder.

- Train the model using the command below. Note that the GPU option is optional and only applies to GPU-powered machines. By default, spaCy trains the model on the CPU.
>spacy train data/ner-config.cfg --paths.train data/train-ALL.spacy --paths.dev data/test-ALL.spacy [--gpu-id 0]

- Evaluate the model's performance per provider by running the commands below

```bash
spacy evaluate model/model-best resources/test-WIPO.spacy --output results/models-performance/WIPO.json
spacy evaluate model/model-best resources/test-FORUM.spacy --output results/models-performance/FORUM.json
spacy evaluate model/model-best resources/test-CAC.spacy --output results/models-performance/CAC.json
spacy evaluate model/model-best resources/test-ADNDRC.spacy --output results/models-performance/ADNDRC.json
spacy evaluate model/model-best resources/test-CIIDRC.spacy --output results/models-performance/CIIDRC.json
```

- You can run the notebook [code/e1.model-performance.ipynb](code/e1.model-performance.ipynb) to visualize the model's performance
- To use the model for prediction, first create an installable package using the command `spacy package model/model-best packages --name udrp_extractor --version 0.0.1` and install it using the command `pip install packages/en_udrp_extractor-0.0.1/dist/en_udrp_extractor-0.0.1.tar.gz`. You can subsequently, use the model as described in [code/e1.extract-data.ipynb](code/e1.extract-data.ipynb) to see how to annotate any UDRP proceeding.


### 2. Extract information from UDRP proceedings
This section uses our trained NER model. Given that the file is large, we saved the model to Google Drive. Download the model to your local copy using the commands below:

```bash
gdown https://drive.google.com/file/d/1jI42clvi5iRbX0AiSQ6iRyWW2OCBvMo8/view?usp=drive_link
mv model resources/model-best/transformer/model
```
After downloading the file, create a Python package for the repository and install it to your Python environment using the following commands:

```bash
spacy package resources/model-best/ packages/ --name udrp_extractor_baseline --version 0.0.1

pip install packages/en_udrp_extractor_baseline-0.0.1/dist/en_udrp_extractor_baseline-0.0.1.tar.gz
```

By following the instructions in the notebook [code/e2.extract-and-clean-details.ipynb](code/e2.extract-and-clean-details.ipynb), extract details from a file containing UDRP proceedings and dump the results to a file. By default, the notebook uses a subset of disputes submitted between January 2023 and August 2024.

### 3. Assess the prevalence of forum shopping
Follow the instructions in [code/e3.analysis-forum-shopping.ipynb](code/e3.analysis-forum-shopping.ipynb) to assess the prevalence of forum shopping using our curated dataset.

### 4. Estimate delays observed in UDRP disputes
Follow the instructions in [code/e4.analysis-efficiency.ipynb](code/e4.analysis-efficiency.ipynb) to measure the delays from providers, registrars, and panelists observed in our curated UDRP dataset.

## Citation
If you use this artifact, please cite our work as below:

```bibtex
@InProceedings{Adjibi2026,
  author    = {Adjibi, {Boladji Vinny} and Avgetidis, Athanasios and Antonakakis, Manos and Dainotti, Alberto and Bailey, Michael and Monrose, Fabian},
  booktitle = {Proceedings of the 33nd Annual Network and Distributed System Security Symposium},
  title     = {Repairing Trust in Domain Name Disputes Practices: Insights from a Quarter-Century’s Worth of Squabbles},
  year      = {2026 (to appear)},
  month     = feb,
  series    = {NDSS 2026}
}
```

## E2
1. Create the package for the model
spacy package resources/model-best/ packages/ --name udrp_extractor_baseline --version 0.0.1

2. Install the package
pip install packages/en_udrp_extractor_baseline-0.0.1/dist/en_udrp_extractor_baseline-0.0.1.tar.gz

3. Now use it to extract the information from the files