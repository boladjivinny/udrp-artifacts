import spacy
import gzip
import json
from geopy.geocoders import Nominatim
from tqdm import tqdm
from openai import OpenAI
import time
import sys

def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n): 
        yield l[i:i + n]

outfile = sys.argv[1]
errfile = sys.argv[2]

spacy.prefer_gpu()
nlp = spacy.load('en_core_web_trf', disable = ["tagger", "parser", "attribute_ruler", "lemmatizer"])

geolocator = Nominatim(user_agent="Geopy Library", timeout=2)

# addyToCountry = {}
infile = '../data/parsed_proceedings_data_extraction.jsonl.gz'

with gzip.open(infile, 'r') as fin:
    all_addresses = set().union(*[json.loads(line)['COMP_LOC'] + json.loads(line)['RESP_LOC'] for line in fin])

valsToGPE = {}
for doc in tqdm(nlp.pipe(all_addresses)):
    address = ", ".join([ent.text for ent in doc.ents if ent.label_ == "GPE"])
    if address:
        valsToGPE[doc.text] = address

# let's get the values from Nominatim
addressToCountry = {}
failed = set()


assistant_id = "<YOUR ChatGPT assistant ID>"
"""The prompt for the GPT-assistant is 

You are a diplomat who respects standards. 
You are provided with a list of addresses and tasked with identifying the countries those addresses relate to. 
You must produce your output as a JSON object with the input values serving as keys and a list of countries serving as values, rendered in proper JSON format parsable by the `json` module in Python. 
For the names of the countries, you must use the official names registered with the United Nations. 
Please enclose your output between the <OUTPUT> and </OUTPUT> tags.

"""
inVals = list(set(valsToGPE.values()))

with OpenAI() as client, open(outfile, 'w') as fout, open(errfile, 'w') as eout:
    for address in tqdm(inVals):
        try:
            location = geolocator.geocode(address, language='en', addressdetails=True)
            time.sleep(0.01)
            assert location
            addressToCountry[address] = [location.raw['address']['country']]
        except:
            failed.add(address)
    inRemVals = list(failed)

    finalFailed = set()
    chunk_size = 100
    for idx, subset in tqdm(enumerate(divide_chunks(inRemVals, chunk_size)), total = 1 + len(inVals) // chunk_size):
        try:
            text = '\n'.join(subset)
            stream =  client.beta.threads.create_and_run(
                assistant_id = assistant_id,
                thread = {
                    "messages": [
                        {"role": "user", "content": f'```json\n{text}\n```'}
                    ],
                },
                stream = True
            )
            for event in stream:
                if event.event == 'thread.message.completed':
                    response = event.data.content[0].text.value
                    response = response.split('<OUTPUT>')[1].split('</OUTPUT>')[0].strip()
                    json_response = json.loads(response)
                    addressToCountry.update(json_response)
                    break
        except KeyboardInterrupt:
            break
        except:
            finalFailed.update(subset)

    addyToCountry = {
        addy: addressToCountry[address]
        for addy, address in valsToGPE.items() if address in addressToCountry
    }

    json.dump(addyToCountry, fout, indent = 0)
    json.dump({addy: address for addy, address in valsToGPE.items() if address in finalFailed}, eout, indent = 0)