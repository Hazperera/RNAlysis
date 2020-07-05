import os
import warnings
from pathlib import Path
from typing import List, Set, Union, Iterable, Tuple
import requests
import pandas as pd
import json
from itertools import chain

from rnalysis.utils import parsing, validation, __path__


def load_csv(filename: str, idx_col: int = None, drop_columns: Union[str, List[str]] = False, squeeze=False,
             comment: str = None):
    """
    loads a csv df into a pandas dataframe.

    :type filename: str or pathlib.Path
    :param filename: name of the csv file to be loaded
    :type idx_col: int, default None
    :param idx_col: number of column to be used as index. default is None, meaning no column will be used as index.
    :type drop_columns: str, list of str, or False (default False)
    :param drop_columns: if a string or list of strings are specified, \
    the columns of the same name/s will be dropped from the loaded DataFrame.
    :type squeeze: bool, default False
    :param squeeze: If the parsed data only contains one column then return a Series.
    :type comment: str (optional)
    :param comment: Indicates remainder of line should not be parsed. \
    If found at the beginning of a line, the line will be ignored altogether. This parameter must be a single character.
    :return: a pandas dataframe of the csv file
    """
    assert isinstance(filename,
                      (str, Path)), f"Filename must be of type str or pathlib.Path, is instead {type(filename)}."
    encoding = 'ISO-8859-1'
    if idx_col is not None:
        df = pd.read_csv(filename, index_col=idx_col, encoding=encoding, squeeze=squeeze, comment=comment)
    else:
        df = pd.read_csv(filename, encoding=encoding, squeeze=squeeze, comment=comment)
    if drop_columns:
        if isinstance(drop_columns, str):
            drop_columns = [drop_columns]
        assert isinstance(drop_columns,
                          list), f"'drop_columns' must be str, list, or False; is instead {type(drop_columns)}."
        for col in drop_columns:
            assert isinstance(col, str), f"'drop_columns' must contain strings only. " \
                                         f"Member {col} is of type {type(col)}."
            if col in df:
                df.drop(col, axis=1, inplace=True)
            else:
                raise IndexError(f"The argument {col} in 'drop_columns' is not a column in the loaded csv file!")
    return df


def save_csv(df: pd.DataFrame, filename: str, suffix: str = None, index: bool = True):
    """
    save a pandas DataFrame to csv.

    :param df: pandas DataFrame to be saved
    :param filename: a string or pathlib.Path object stating the original name of the file
    :type suffix: str, default None
    :param suffix: A suffix to be added to the original name of the file. If None, no suffix will be added.
    :param index: if True, saves the DataFrame with the indices. If false, ignores the index.
    """
    fname = Path(filename)
    if suffix is None:
        suffix = ''
    else:
        assert isinstance(suffix, str), "'suffix' must be either str or None!"
    new_fname = os.path.join(fname.parent.absolute(), f"{fname.stem}{suffix}{fname.suffix}")
    df.to_csv(new_fname, header=True, index=index)


source = "ftp://ftp.ncbi.nih.gov/gene/DATA/gene2go.gz"


def fetch_gaf_file(taxon_id: int, aspects: Union[str, List[str]] = 'all',
                   evidence_codes: Union[str, List[str]] = 'all', databases: Union[str, List[str]] = 'all',
                   qualifiers: Union[str, List[str]] = None):
    url = "https://www.ebi.ac.uk/QuickGO/services/annotation/search?"

    legal_aspects = {'biological_process', 'molecular_function', 'cellular_component'}
    aspects = ",".join(legal_aspects) if aspects is 'all' else ",".join(parsing.data_to_list(aspects))

    params = {
        'taxonId': taxon_id,
        'aspect': aspects,
        'taxonUsage': 'descendants',
        'limit': 100,
        'page': 25
    }
    if not evidence_codes == 'all':
        params['evidenceCodeUsage'] = 'descendants'
        params['evidenceCode'] = ",".join(parsing.data_to_list(evidence_codes))
    if not databases == 'all':
        params['assignedBy'] = ",".join(parsing.data_to_list(databases))
    if qualifiers is not None:
        params['qualifier'] = ",".join(parsing.data_to_list(qualifiers))
    req = requests.get(url, params=params, headers={"Accept": "application/json"})
    if not req.ok:
        req.raise_for_status()
    data = json.loads(req.text)

    return data


def golr_annotations_iterator(taxon_id: int, aspects: Union[str, Iterable[str]] = 'all',
                              evidence_types: Union[str, Iterable[str]] = 'any',
                              excluded_evidence_types: Union[str, Iterable[str]] = (),
                              databases: Union[str, List[str], Set[str]] = 'any',
                              excluded_databases: Union[str, List[str], Set[str]] = 'any',
                              qualifiers: Union[str, Iterable[str]] = 'any',
                              excluded_qualifiers: Union[str, Iterable[str]] = (),
                              iter_size: int = 10000):
    url = 'http://golr-aux.geneontology.io/solr/select?'
    legal_aspects = {'P', 'F', 'C'}
    legal_evidence = {'EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP', 'HTP', 'HDA', 'HMP', 'HGI', 'HEP', 'IBA', 'IBD', 'IKR',
                      'IRD', 'ISS', 'ISO', 'ISA', 'ISM', 'IGC', 'RCA', 'TAS', 'NAS', 'IC', 'ND', 'IEA'}
    experimental_evidence = {'EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP', 'HTP', 'HDA', 'HMP', 'HGI', 'HEP'}
    legal_qualifiers = {'not', 'contributes_to', 'colocalizes_with'}

    aspects = legal_aspects if aspects == 'all' else parsing.data_to_set(aspects)
    databases = parsing.data_to_set(databases)
    qualifiers = () if qualifiers == 'any' else parsing.data_to_set(qualifiers)
    excluded_qualifiers = parsing.data_to_set(excluded_qualifiers)
    excluded_databases = parsing.data_to_set(excluded_databases)

    if evidence_types == 'any':
        evidence_types = legal_evidence
    elif evidence_types == 'experimental':
        evidence_types = experimental_evidence
    else:
        evidence_types = parsing.data_to_set(evidence_types)

    if excluded_evidence_types == 'any':
        excluded_evidence_types = legal_evidence
    elif excluded_evidence_types == 'experimental':
        excluded_evidence_types = experimental_evidence
    else:
        excluded_evidence_types = parsing.data_to_set(excluded_evidence_types)
    # assert legality of inputs
    for field, legals in zip((aspects, chain(evidence_types, excluded_evidence_types),
                              chain(qualifiers, excluded_qualifiers)),
                             (legal_aspects, legal_evidence, legal_qualifiers)):
        for item in field:
            assert item in legals, f"Illegal item {item}. Legal items are {legals}.."
    # add fields with known legal inputs and cardinality >= 1 to query (taxon ID, aspect, evidence type)
    query = [f'document_category:"annotation"',
             f'taxon:"NCBITaxon:{taxon_id}"',
             ' OR '.join([f'aspect:"{aspect}"' for aspect in aspects]),
             ' OR '.join([f'evidence_type:"{evidence_type}"' for evidence_type in evidence_types])]
    # exclude all 'excluded' items from query
    query.extend([f'-evidence_type:"{evidence_type}"' for evidence_type in excluded_evidence_types])
    query.extend([f'-source:"{db}"' for db in excluded_databases])
    query.extend([f'-qualifier:"{qual}"' for qual in excluded_qualifiers])
    # add union of all requested databases to query
    if not databases == {'any'}:
        query.append(' OR '.join(f'source:"{db}"' for db in databases))
    # add union of all requested qualifiers to query
    if len(qualifiers) > 0:
        query.append(' OR '.join([f'qualifier:"{qual}"' for qual in qualifiers]))

    params = {
        "q": "*:*",
        "wt": "json",
        "rows": 0,
        "start": None,
        "fq": query,
        "fl": "source,bioentity_internal_id,annotation_class,annotation_class_label"
    }
    # get number of annotations found in the query
    req = requests.get(url, params=params)
    if not req.ok:
        req.raise_for_status()
    n_annotations = json.loads(req.text)['response']['numFound']

    print(f"Fetching {n_annotations} annotations...")

    # fetch all annotations in batches of size iter_size, and yield them one-by-one
    start = 0
    max_iters = n_annotations // iter_size + 1
    for i in range(max_iters):
        params['start'] = start
        start += iter_size
        params['rows'] = iter_size if i < max_iters - 1 else n_annotations % iter_size
        req = requests.get(url, params=params)
        if not req.ok:
            req.raise_for_status()
        for record in json.loads(req.text)['response']['docs']:
            yield record


def map_taxon_id(taxon_name: str) -> Tuple[int, str]:
    url = 'https://www.uniprot.org/taxonomy/?'

    params = {
        'format': 'tab',
        'query': taxon_name,
        'sort': 'score'
    }
    req = requests.get(url, params=params)
    if not req.ok:
        req.raise_for_status()
    res = req.text.splitlines()
    header = res[0].split('\t')
    if len(res) > 2:
        warnings.warn(
            f"Found {len(res) - 1} taxons matching the search term '{taxon_name}'. "
            f"Picking the match with the highest score.")
    matched_taxon = res[1].split('\t')
    taxon_id = int(matched_taxon[header.index('Taxon')])
    scientific_name = matched_taxon[header.index('Scientific name')]

    return taxon_id, scientific_name


def map_gene_ids(ids: Union[str, Set[str], List[str]], map_from: str, map_to: str = 'UniProtKB AC'):
    url = 'https://www.uniprot.org/uploadlists/'
    id_dict = _load_id_abbreviation_dict()
    validation.validate_uniprot_dataset_name(id_dict, map_to, map_from)

    params = {
        'from': id_dict[map_from],
        'to': id_dict[map_to],
        'format': 'tab',
        'query': _format_ids(ids),
    }
    n_queries = len(params['query'].split(" "))
    print(f"Mapping {n_queries} entries from '{map_from}' to '{map_to}'...")
    req = requests.get(url, params=params)
    if not req.ok:
        req.raise_for_status()

    output = parsing.uniprot_tab_to_dict(req.text)
    if len(output) < n_queries:
        warnings.warn(f"Failed to map {len(output) - n_queries} entries from '{map_from}' to '{map_to}'. "
                      f"Returning the remaining {len(output)} entries.")
    return output


def _format_ids(ids: Union[str, int, list, set]):
    if isinstance(ids, str):
        return ids
    elif isinstance(ids, int):
        return str(ids)
    return " ".join((str(item) for item in ids))


def _load_id_abbreviation_dict(dict_path: str = os.path.join(__path__[0], 'uniprot_dataset_abbreviation_dict.json')):
    with open(dict_path) as f:
        return json.load(f)
