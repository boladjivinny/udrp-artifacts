import click
import json
import gzip
import spacy

import pandas as pd

from math import ceil
from random import sample
from spacy.tokens import DocBin


@click.command()
@click.option('-mr', '--min-train-size', type = int, default = 10)
@click.option('-Mr', '--max-train-size', type = int, default = 100)
@click.option('-mt', '--min-test-size', type = int, default = 3)
@click.option('-mT', '--max-test-size', type = int, default = 25)

@click.argument('disputes-infile', type = click.Path(exists = True))
@click.argument('annotations-infile', type = click.Path(exists = True))
@click.argument('outfolder', type = click.Path(writable = True))

def generate(
    min_train_size: int,
    max_train_size: int,
    min_test_size: int,
    max_test_size: int,

    disputes_infile: str,
    annotations_infile: str,
    outfolder: str
):
    nlp = spacy.blank('en')
    # get the count of cases per (sub)provider
    df = pd.read_json(disputes_infile, lines = True)
    casesPerProvider = df.groupby('source').agg({'number': 'nunique'}).number.to_dict()
    urlToSource = df[df.language == 'en'].set_index('url').source.to_dict()

    # estimate the number of proceedings to use per provider
    trainSizes = {
        provider: max(
            min_train_size,
            ceil(max_train_size * (count - min(casesPerProvider.values())) / (max(casesPerProvider.values()) - min(casesPerProvider.values())))
        )
        for provider, count in casesPerProvider.items()
    }

    testSizes = {
        provider: max(
            min_test_size,
            ceil(max_test_size * (count - min(casesPerProvider.values())) / (max(casesPerProvider.values()) - min(casesPerProvider.values())))
        )
        for provider, count in casesPerProvider.items()
    }

    # load the annotated data, mapping the providers to their URLs
    annotatedDocs = {}
    providerUrls = {}
    with gzip.open(annotations_infile, 'rb') as fin:
        for line in fin:
            data = json.loads(line)
            if urlToSource[data['url']] not in providerUrls:
                providerUrls[urlToSource[data['url']]] = []
            providerUrls[urlToSource[data['url']]].append(data['url'])
            annotatedDocs[data['url']] = {
                'text': data['text'],
                'label': data['label']
            }
    
    # generate the samples
    trainLinks = {
        source: sample(providerUrls[source], k = count)
        for source, count in trainSizes.items()
    }

    # make sure there is no overlap
    testLinks = {
        source: sample([
            url for url in providerUrls[source] if url not in trainLinks[source]
        ], k = count)
        for source, count in testSizes.items()
    }

    # get the overall list of training list
    trainLinks['ALL'] = sum(trainLinks.values(), start = [])
    testLinks['ALL'] = sum(testLinks.values(), start = [])
    # fix the data for ADNDRC
    trainLinks['ADNDRC'] = trainLinks.pop('AIAC') + trainLinks.pop('CIETAC-ODRC') + trainLinks.pop('HKIAC') + trainLinks.pop('IDRC')
    testLinks['ADNDRC'] = testLinks.pop('AIAC') + testLinks.pop('CIETAC-ODRC') + testLinks.pop('HKIAC') + testLinks.pop('IDRC')

    # generate the spacy files and save them to the output directory
    for source in trainLinks:
        for context, urls in {
            'train': trainLinks[source],
            'test': testLinks[source]
        }.items():
            # we only want the training data for all providers
            if context == 'train' and source != "ALL":
                continue
            db = DocBin()
            for url in urls:
                doc = nlp(text = annotatedDocs[url]['text'])
                ents = [doc.char_span(start, end, label = label) for start, end, label in annotatedDocs[url]['label']]
                if ents:
                    doc.ents = [ent for ent in ents if ent]
                    db.add(doc)
            db.to_disk(f'{outfolder}/{context}-{source}.spacy')

if __name__ == '__main__':
    generate()