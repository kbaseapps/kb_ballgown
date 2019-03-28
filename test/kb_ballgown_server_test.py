# -*- coding: utf-8 -*-
import os  # noqa: F401
import shutil
import time
import unittest
from configparser import ConfigParser  # py3
from os import environ
from pprint import pprint  # noqa: F401

import requests
from nose.tools import raises

from installed_clients.AbstractHandleClient import AbstractHandle as HandleService
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.ExpressionUtilsClient import ExpressionUtils
from installed_clients.GenomeFileUtilClient import GenomeFileUtil
from installed_clients.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from installed_clients.ReadsUtilsClient import ReadsUtils
from installed_clients.SetAPIClient import SetAPI
from installed_clients.WorkspaceClient import Workspace as workspaceService
from kb_ballgown.authclient import KBaseAuth as _KBaseAuth
from kb_ballgown.core.ballgown_util import BallgownUtil
from kb_ballgown.kb_ballgownImpl import kb_ballgown
from kb_ballgown.kb_ballgownServer import MethodContext


class kb_ballgownTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_ballgown'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(cls.token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': cls.token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_ballgown',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
        cls.shockURL = cls.cfg['shock-url']
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL, token=cls.token)
        cls.serviceImpl = kb_ballgown(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

        cls.gfu = GenomeFileUtil(cls.callback_url)
        cls.dfu = DataFileUtil(cls.callback_url)
        cls.ru = ReadsUtils(cls.callback_url)
        cls.rau = ReadsAlignmentUtils(cls.callback_url, service_ver='dev')
        cls.eu = ExpressionUtils(cls.callback_url, service_ver='dev')
        cls.set_api = SetAPI(cls.callback_url)

        suffix = int(time.time() * 1000)
        cls.wsName = "test_kb_ballgown_" + str(suffix)
        #cls.wsName = "test_kb_ballgown_1004"
        cls.wsClient.create_workspace({'workspace': cls.wsName})

        cls.nodes_to_delete = []
        cls.handles_to_delete = []

        cls.prepare_data()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

        if hasattr(cls, 'nodes_to_delete'):
            for node in cls.nodes_to_delete:
                cls.delete_shock_node(node)
        if hasattr(cls, 'handles_to_delete') and len(cls.handles_to_delete):
            cls.hs.delete_handles(cls.hs.ids_to_handles(cls.handles_to_delete))
            print('Deleted handles ' + str(cls.handles_to_delete))

    def getWsClient(self):
        return self.__class__.wsClient

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    @classmethod
    def delete_shock_node(cls, node_id):
        header = {'Authorization': 'Oauth {0}'.format(cls.token)}
        requests.delete(cls.shockURL + '/node/' + node_id, headers=header,
                        allow_redirects=True)
        print('Deleted shock node ' + node_id)

    @classmethod
    def make_ref(cls, objinfo):
        return str(objinfo[6]) + '/' + str(objinfo[0]) + '/' + str(objinfo[4])

    @classmethod
    def save_ws_obj(cls, obj, objname, objtype):

        return cls.wsClient.save_objects({
            'workspace': cls.wsName,
            'objects': [{'type': objtype,
                         'data': obj,
                         'name': objname
                         }]
        })[0]

    @classmethod
    def upload_file_to_shock(cls, file_path):
        """
        Use HTTP multi-part POST to save a file to a SHOCK instance.
        """
        header = dict()
        header["Authorization"] = "Oauth {0}".format(cls.token)

        if file_path is None:
            raise Exception("No file given for upload to SHOCK!")

        with open(os.path.abspath(file_path), 'rb') as dataFile:
            files = {'upload': dataFile}
            print('POSTing data')
            response = requests.post(
                cls.shockURL + '/node', headers=header, files=files,
                stream=True, allow_redirects=True)
            print('got response')

        if not response.ok:
            response.raise_for_status()

        result = response.json()

        if result['error']:
            raise Exception(result['error'][0])
        else:
            return result["data"]

    @classmethod
    def upload_file_to_shock_and_get_handle(cls, test_file):
        """
        Uploads the file in test_file to shock and returns the node and a
        handle to the node.
        """
        print('loading file to shock: ' + test_file)
        node = cls.upload_file_to_shock(test_file)
        pprint(node)
        cls.nodes_to_delete.append(node['id'])

        print('creating handle for shock id ' + node['id'])
        handle_id = cls.hs.persist_handle({'id': node['id'],
                                           'type': 'shock',
                                           'url': cls.shockURL
                                           })
        cls.handles_to_delete.append(handle_id)

        md5 = node['file']['checksum']['md5']
        return node['id'], handle_id, md5, node['file']['size']

    @classmethod
    def upload_annotation(cls, wsobjname, file_name):

        gtf_path = os.path.join(cls.scratch, file_name)
        shutil.copy(os.path.join('data', file_name), gtf_path)
        id, handle_id, md5, size = cls.upload_file_to_shock_and_get_handle(gtf_path)

        a_handle = {
            'hid': handle_id,
            'file_name': file_name,
            'id': id,
            "type": "KBaseRNASeq.GFFAnnotation",
            'url': cls.shockURL,
            'type': 'shock',
            'remote_md5': md5
        }
        obj = {
            "size": size,
            "handle": a_handle,
            "genome_id": "test_genome_GTF_Annotation",
            "genome_scientific_name": "scientific name"
        }
        res = cls.save_ws_obj(obj, wsobjname, "KBaseRNASeq.GFFAnnotation")
        return cls.make_ref(res)

    @classmethod
    def prepare_data(cls):
        # upload genome object
        genbank_file_name = 'at_chrom1_section.gbk'
        genbank_file_path = os.path.join(cls.scratch, genbank_file_name)
        shutil.copy(os.path.join('data', genbank_file_name), genbank_file_path)

        genome_object_name = genbank_file_name
        genome_ref = cls.gfu.genbank_to_genome({'file': {'path': genbank_file_path},
                                                'workspace_name': cls.wsName,
                                                'genome_name': genome_object_name,
                                                'source': 'Ensembl',
                                                'generate_ids_if_needed': 1,
                                                'generate_missing_genes': 1
                                                })['genome_ref']

        # upload annotation
        annotation_ref = cls.upload_annotation('at_chrom1_section', 'at_chrom1_section.gtf')

        # upload a dummy reads object2 (used in all expression objects)
        reads_file_name = 'Sample1.fastq'
        reads_file_path = os.path.join(cls.scratch, reads_file_name)
        shutil.copy(os.path.join('data', reads_file_name), reads_file_path)

        reads_object_name_1 = 'test_Reads_1'
        dummy_reads_ref_1 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                                 'wsname': cls.wsName,
                                                 'sequencing_tech': 'Unknown',
                                                 'interleaved': 0,
                                                 'name': reads_object_name_1
                                                 })['obj_ref']

        reads_object_name_2 = 'test_Reads_2'
        dummy_reads_ref_2 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                                 'wsname': cls.wsName,
                                                 'sequencing_tech': 'Unknown',
                                                 'interleaved': 0,
                                                 'name': reads_object_name_2
                                                 })['obj_ref']

        reads_object_name_3 = 'test_Reads_3'
        dummy_reads_ref_3 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                                 'wsname': cls.wsName,
                                                 'sequencing_tech': 'Unknown',
                                                 'interleaved': 0,
                                                 'name': reads_object_name_3
                                                 })['obj_ref']

        reads_object_name_4 = 'test_Reads_4'
        dummy_reads_ref_4 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                                 'wsname': cls.wsName,
                                                 'sequencing_tech': 'Unknown',
                                                 'interleaved': 0,
                                                 'name': reads_object_name_4
                                                 })['obj_ref']
        ###########################################################################################
        reads_object_name_5 = 'test_Reads_5'
        dummy_reads_ref_5 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                                 'wsname': cls.wsName,
                                                 'sequencing_tech': 'Unknown',
                                                 'interleaved': 0,
                                                 'name': reads_object_name_5
                                                 })['obj_ref']

        reads_object_name_6 = 'test_Reads_6'
        dummy_reads_ref_6 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                                 'wsname': cls.wsName,
                                                 'sequencing_tech': 'Unknown',
                                                 'interleaved': 0,
                                                 'name': reads_object_name_6
                                                 })['obj_ref']
        ###########################################################################################

        # upload hy5_rep1 alignment
        alignment_object_name_hy5_rep1 = 'extracted_hy5_rep1_hisat2_alignment'
        alignment_file_name = 'accepted_hits.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data/extracted_hy5_rep1_hisat2_alignment/',
                                 alignment_file_name), alignment_file_path)

        alignment_ref_hy5_rep1 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_hy5_rep1,
             'read_library_ref': dummy_reads_ref_1,
             'condition': 'hy5',
             'library_type': 'single_end',
             'assembly_or_genome_ref': genome_ref
             })['obj_ref']

        # upload hy5_rep1 expression
        source_dir = 'data/extracted_hy5_rep1_hisat2_stringtie_expression'
        expression_name_hy5_rep1 = source_dir
        copy_to_dir = os.path.join(cls.scratch, source_dir + str(int(time.time() * 1000)))
        shutil.copytree(source_dir, copy_to_dir)

        expression_params_hy5_rep1 = {
            'destination_ref': cls.wsName + '/extracted_hy5_rep1_hisat2_stringtie_expression',
            'source_dir': copy_to_dir,
            'alignment_ref': alignment_ref_hy5_rep1,
            'genome_ref': genome_ref}
        expression_ref_hy5_rep1 = cls.eu.upload_expression(expression_params_hy5_rep1)

        # upload hy5_rep2 alignment
        alignment_object_name_hy5_rep2 = 'extracted_hy5_rep2_hisat2_alignment'
        alignment_file_name = 'accepted_hits.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data/extracted_hy5_rep2_hisat2_alignment/',
                                 alignment_file_name), alignment_file_path)

        alignment_ref_hy5_rep2 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_hy5_rep2,
             'read_library_ref': dummy_reads_ref_2,
             'condition': 'hy5',
             'library_type': 'single_end',
             'assembly_or_genome_ref': genome_ref
             })['obj_ref']

        # upload hy5_rep2 expression
        source_dir = 'data/extracted_hy5_rep2_hisat2_stringtie_expression'
        expression_name_hy5_rep2 = source_dir
        copy_to_dir = os.path.join(cls.scratch, source_dir + str(int(time.time() * 1000)))
        shutil.copytree(source_dir, copy_to_dir)

        expression_params_hy5_rep2 = {
            'destination_ref': cls.wsName + '/extracted_hy5_rep2_hisat2_stringtie_expression',
            'source_dir': copy_to_dir,
            'alignment_ref': alignment_ref_hy5_rep2,
            'genome_ref': genome_ref}
        expression_ref_hy5_rep2 = cls.eu.upload_expression(expression_params_hy5_rep2)

        # upload WT_rep1 alignment
        alignment_object_name_WT_rep1 = 'extracted_WT_rep1_hisat2_alignment'
        alignment_file_name = 'accepted_hits.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data/extracted_WT_rep1_hisat2_alignment/',
                                 alignment_file_name), alignment_file_path)

        alignment_ref_WT_rep1 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_WT_rep1,
             'read_library_ref': dummy_reads_ref_3,
             'condition': 'WT',
             'library_type': 'single_end',
             'assembly_or_genome_ref': genome_ref
             })['obj_ref']

        # upload WT_rep1 expression
        source_dir = 'data/extracted_WT_rep1_hisat2_stringtie_expression'
        expression_name_WT_rep1 = source_dir
        copy_to_dir = os.path.join(cls.scratch, source_dir + str(int(time.time() * 1000)))
        shutil.copytree(source_dir, copy_to_dir)

        expression_params_WT_rep1 = {
            'destination_ref': cls.wsName + '/extracted_WT_rep1_hisat2_stringtie_expression',
            'source_dir': copy_to_dir,
            'alignment_ref': alignment_ref_WT_rep1,
            'genome_ref': genome_ref}
        expression_ref_WT_rep1 = cls.eu.upload_expression(expression_params_WT_rep1)

        # upload WT_rep2 alignment
        alignment_object_name_WT_rep2 = 'extracted_WT_rep2_hisat2_alignment'
        alignment_file_name = 'accepted_hits.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data/extracted_WT_rep2_hisat2_alignment/',
                                 alignment_file_name), alignment_file_path)

        alignment_ref_WT_rep2 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_WT_rep2,
             'read_library_ref': dummy_reads_ref_4,
             'condition': 'WT',
             'library_type': 'single_end',
             'assembly_or_genome_ref': genome_ref
             })['obj_ref']

        # upload WT_rep1 expression
        source_dir = 'data/extracted_WT_rep2_hisat2_stringtie_expression'
        expression_name_WT_rep2 = source_dir
        copy_to_dir = os.path.join(cls.scratch, source_dir + str(int(time.time() * 1000)))
        shutil.copytree(source_dir, copy_to_dir)

        expression_params_WT_rep2 = {
            'destination_ref': cls.wsName + '/extracted_WT_rep2_hisat2_stringtie_expression',
            'source_dir': copy_to_dir,
            'alignment_ref': alignment_ref_WT_rep2,
            'genome_ref': genome_ref}
        expression_ref_WT_rep2 = cls.eu.upload_expression(expression_params_WT_rep2)

        ############################################################################################
        # upload GT_rep1 alignment
        alignment_object_name_GT_rep1 = 'extracted_GT_rep1_hisat2_alignment'
        alignment_file_name = 'accepted_hits.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data/extracted_GT_rep1_hisat2_alignment/',
                                 alignment_file_name), alignment_file_path)

        alignment_ref_GT_rep1 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_GT_rep1,
             'read_library_ref': dummy_reads_ref_3,
             'condition': 'GT',
             'library_type': 'single_end',
             'assembly_or_genome_ref': genome_ref
             })['obj_ref']

        # upload GT_rep1 expression
        source_dir = 'data/extracted_GT_rep1_hisat2_stringtie_expression'
        expression_name_GT_rep1 = source_dir
        copy_to_dir = os.path.join(cls.scratch, source_dir + str(int(time.time() * 1000)))
        shutil.copytree(source_dir, copy_to_dir)

        expression_params_GT_rep1 = {
            'destination_ref': cls.wsName + '/extracted_GT_rep1_hisat2_stringtie_expression',
            'source_dir': copy_to_dir,
            'alignment_ref': alignment_ref_GT_rep1,
            'genome_ref': genome_ref}
        expression_ref_GT_rep1 = cls.eu.upload_expression(expression_params_GT_rep1)

        # upload GT_rep2 alignment
        alignment_object_name_GT_rep2 = 'extracted_GT_rep2_hisat2_alignment'
        alignment_file_name = 'accepted_hits.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data/extracted_GT_rep2_hisat2_alignment/',
                                 alignment_file_name), alignment_file_path)

        alignment_ref_GT_rep2 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_GT_rep2,
             'read_library_ref': dummy_reads_ref_4,
             'condition': 'GT',
             'library_type': 'single_end',
             'assembly_or_genome_ref': genome_ref
             })['obj_ref']

        # upload GT_rep1 expression
        source_dir = 'data/extracted_GT_rep2_hisat2_stringtie_expression'
        expression_name_GT_rep2 = source_dir
        copy_to_dir = os.path.join(cls.scratch, source_dir + str(int(time.time() * 1000)))
        shutil.copytree(source_dir, copy_to_dir)

        expression_params_GT_rep2 = {
            'destination_ref': cls.wsName + '/extracted_GT_rep2_hisat2_stringtie_expression',
            'source_dir': copy_to_dir,
            'alignment_ref': alignment_ref_GT_rep2,
            'genome_ref': genome_ref}
        expression_ref_GT_rep2 = cls.eu.upload_expression(expression_params_GT_rep2)
        ############################################################################################

        # upload dummy sample_set object
        workspace_id = cls.dfu.ws_name_to_id(cls.wsName)
        sample_set_object_name = 'test_Sample_Set'
        sample_set_data = {
            'sampleset_id': sample_set_object_name,
            'sampleset_desc': 'test sampleset object',
            'Library_type': 'SingleEnd',
            'condition': ['hy5', 'hy5', 'WT', 'WT', 'GT', 'GT'],
            'sample_ids': [dummy_reads_ref_1, dummy_reads_ref_2, dummy_reads_ref_3,
                           dummy_reads_ref_4, dummy_reads_ref_5, dummy_reads_ref_6],
            'domain': 'Eukaryotes',
            'num_samples': 3,
            'platform': 'Unknown'}
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                'type': 'KBaseRNASeq.RNASeqSampleSet',
                'data': sample_set_data,
                'name': sample_set_object_name
            }]
        }
        dfu_oi = cls.dfu.save_objects(save_object_params)[0]
        sample_set_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])

        # upload alignment_set object
        object_type = 'KBaseRNASeq.RNASeqAlignmentSet'
        alignment_set_object_name = 'test_Alignment_Set'
        alignment_set_data = {
            'genome_id': genome_ref,
            'read_sample_ids': [dummy_reads_ref_1,
                                dummy_reads_ref_2],
            'mapped_rnaseq_alignments': [{reads_object_name_1: alignment_object_name_hy5_rep1},
                                         {reads_object_name_2: alignment_object_name_hy5_rep2},
                                         {reads_object_name_3: alignment_object_name_WT_rep1},
                                         {reads_object_name_4: alignment_object_name_WT_rep2},
                                         {reads_object_name_5: alignment_object_name_GT_rep1},
                                         {reads_object_name_6: alignment_object_name_GT_rep2}],
            'mapped_alignments_ids': [{reads_object_name_1: alignment_ref_hy5_rep1},
                                      {reads_object_name_2: alignment_ref_hy5_rep2},
                                      {reads_object_name_3: alignment_ref_WT_rep1},
                                      {reads_object_name_4: alignment_ref_WT_rep2},
                                      {reads_object_name_5: alignment_ref_GT_rep1},
                                      {reads_object_name_6: alignment_ref_GT_rep2}],
            'sample_alignments': [alignment_ref_hy5_rep1,
                                  alignment_ref_hy5_rep2,
                                  alignment_ref_WT_rep1,
                                  alignment_ref_WT_rep2,
                                  alignment_ref_GT_rep1,
                                  alignment_ref_GT_rep2
                                  ],
            'sampleset_id': sample_set_ref}
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                'type': object_type,
                'data': alignment_set_data,
                'name': alignment_set_object_name
            }]
        }

        dfu_oi = cls.dfu.save_objects(save_object_params)[0]
        alignment_set_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])

        # upload RNASeq.ExpressionSet object
        expression_set_data = {
            "alignmentSet_id": alignment_set_ref,
            "genome_id": genome_ref,
            "id": "test_expression_set",
            "mapped_expression_ids": [
                {
                    alignment_ref_hy5_rep1: expression_ref_hy5_rep1['obj_ref']
                },
                {
                    alignment_ref_hy5_rep2: expression_ref_hy5_rep2['obj_ref']
                },
                {
                    alignment_ref_WT_rep1: expression_ref_WT_rep1['obj_ref']
                },
                {
                    alignment_ref_WT_rep2: expression_ref_WT_rep2['obj_ref']
                },
                {
                    alignment_ref_GT_rep1: expression_ref_GT_rep1['obj_ref']
                },
                {
                    alignment_ref_GT_rep2: expression_ref_GT_rep2['obj_ref']
                }
            ],
            "mapped_expression_objects": [
                {
                    alignment_object_name_hy5_rep1: expression_name_hy5_rep1
                },
                {
                    alignment_object_name_hy5_rep2: expression_name_hy5_rep2
                },
                {
                    alignment_object_name_WT_rep1: expression_name_WT_rep1
                },
                {
                    alignment_object_name_WT_rep2: expression_name_WT_rep2
                },
                {
                    alignment_object_name_GT_rep1: expression_name_GT_rep1
                },
                {
                    alignment_object_name_GT_rep2: expression_name_GT_rep2
                }
            ],
            "sample_expression_ids": [
                expression_ref_hy5_rep1['obj_ref'],
                expression_ref_hy5_rep2['obj_ref'],
                expression_ref_WT_rep1['obj_ref'],
                expression_ref_WT_rep2['obj_ref'],
                expression_ref_GT_rep1['obj_ref'],
                expression_ref_GT_rep2['obj_ref']
            ],
            "sampleset_id": sample_set_ref,
            "tool_used": "StringTie",
            "tool_version": "1.3.3b"
        }

        object_type = 'KBaseRNASeq.RNASeqExpressionSet'
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                'type': object_type,
                'data': expression_set_data,
                'name': 'test_expression_set'
            }]
        }

        dfu_oi = cls.dfu.save_objects(save_object_params)[0]
        cls.rnaseq_expression_set_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])

        print('RNASeqExpressionSet: ')
        pprint(cls.rnaseq_expression_set_ref)

        # upload KbaseSets.ExpressionSet object
        kbaseseets_expression_set_name = "test_expression_set"
        expression_items = list()

        expression_items.append({
            "label": "hy5",
            "ref": expression_ref_hy5_rep1['obj_ref']
        })
        expression_items.append({
            "label": "hy5",
            "ref": expression_ref_hy5_rep2['obj_ref']
        })
        expression_items.append({
            "label": "WT",
            "ref": expression_ref_WT_rep1['obj_ref']
        })
        expression_items.append({
            "label": "WT",
            "ref": expression_ref_WT_rep2['obj_ref']
        })
        expression_items.append({
            "label": "GT",
            "ref": expression_ref_GT_rep1['obj_ref']
        })
        expression_items.append({
            "label": "GT",
            "ref": expression_ref_GT_rep2['obj_ref']
        })

        kbasesets_expression_set = {
            "description": "test_expressions",
            "items": expression_items
        }
        expression_set_info = cls.set_api.save_expression_set_v1({
            "workspace": cls.wsName,
            "output_object_name": kbaseseets_expression_set_name,
            "data": kbasesets_expression_set
        })

        cls.kbasesets_expression_set_ref = expression_set_info['set_ref']

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_run_all_combinations_rnaseq_ballgown(self):

        input_params = {
            #'expressionset_ref': "30996/40/1",
            'expressionset_ref': self.__class__.rnaseq_expression_set_ref,
            'diff_expression_matrix_set_name': 'all_combinations_rnaseq',
            'workspace_name': self.wsName,
            "run_all_combinations": 1,
            "condition_pair_subset": [],
            'input_type': "genes"
        }

        result = self.getImpl().run_ballgown_app(self.getContext(), input_params)[0]

        self.assertEqual(4, len(result))
        print('Results: ' + str(result))

    def test_run_all_combinations_transcripts_ballgown(self):

        input_params = {
            'expressionset_ref': "30996/40/1",
            #'expressionset_ref': self.__class__.rnaseq_expression_set_ref,
            'diff_expression_matrix_set_name': 'all_combinations_transcripts',
            'workspace_name': self.wsName,
            "run_all_combinations": 1,
            "condition_pair_subset": [],
            'input_type': "transcripts"
        }

        result = self.getImpl().run_ballgown_app(self.getContext(), input_params)[0]

        self.assertEqual(4, len(result))
        print('Results: ' + str(result))

    def test_run_all_combinations_kbasesets_ballgown(self):

        input_params = {
            #"expressionset_ref": "23192/112/1",
            "expressionset_ref": self.kbasesets_expression_set_ref,
            'diff_expression_matrix_set_name': 'all_combinations_kbasesets',
            #"workspace_name": "arfath:narrative_1498151834637",
            'workspace_name': self.wsName,
            "run_all_combinations": 1,
            "condition_pair_subset": [],
            'input_type': "genes"
        }

        result = self.getImpl().run_ballgown_app(self.getContext(), input_params)[0]

        self.assertEqual(4, len(result))
        print('Results: ' + str(result))

    def test_run_subset_combinations_kbasesets_ballgown(self):

        input_params = {
            #"expressionset_ref": "23192/112/1",
            "expressionset_ref": self.__class__.kbasesets_expression_set_ref,
            "diff_expression_matrix_set_name":
                "downsized_KBaseSets_AT_differential_expression_object",
            #"workspace_name": "arfath:narrative_1498151834637",
            'workspace_name': self.wsName,
            "run_all_combinations": 0,
            "condition_pair_subset": [
                {
                    "condition": "hy5"
                },
                {
                    "condition": "WT"
                }
            ]
        }

        result = self.getImpl().run_ballgown_app(self.getContext(), input_params)[0]

        self.assertEqual(4, len(result))
        print('Results: ' + str(result))

    @raises(Exception)
    def test_prokaryote_empty_intron_measurement_error(self):
        """
        Ballgown will fail if intron level measurement comes up empty. So catch
        this case and report as error.
        :return:
        """
        bg_util = BallgownUtil(self.__class__.cfg)
        bg_util._check_intron_measurements('data/prokaryote/sample_dir_group_file')

    def test_same_condition_specified_twice(self):

        input_params = {
            #'expressionset_ref': "23748/19/1",
            'expressionset_ref': self.__class__.rnaseq_expression_set_ref,
            'diff_expression_matrix_set_name': 'MyDiffExpression',
            'workspace_name': self.wsName,
            'run_all_combinations': 0,
            "condition_pair_subset": [{'condition': 'hy5'},
                                      {'condition': 'hy5'}]
        }

        with self.assertRaisesRegex(ValueError, "At least two unique conditions must be specified."):
            self.getImpl().run_ballgown_app(self.getContext(), input_params)

    def test_no_condition_pair_ballgown(self):

        input_params = {
            #"expressionset_ref": "23192/112/1",
            "expressionset_ref": self.kbasesets_expression_set_ref,
            "diff_expression_matrix_set_name": "no_condition_pair",
            #"workspace_name": "arfath:narrative_1498151834637",
            'workspace_name': self.wsName,
            "run_all_combinations": 0,
            "condition_pair_subset": []
        }

        with self.assertRaisesRegex(ValueError, "'Run All Paired Condition Combinations' or "
                                                "provide subset of condition pairs."):
            self.getImpl().run_ballgown_app(self.getContext(), input_params)

    def test_both_condition_options_ballgown(self):

        # both run_all_combinations and condition_pair_subset are specified
        input_params = {
            #"expressionset_ref": "23192/112/1",
            "expressionset_ref": self.kbasesets_expression_set_ref,
            "diff_expression_matrix_set_name": "both_condition_options",
            #"workspace_name": "arfath:narrative_1498151834637",
            'workspace_name': self.wsName,
            "run_all_combinations": 1,
            "condition_pair_subset": [
                {
                    "condition": "hy5"
                },
                {
                    "condition": "WT"
                }
            ]
        }

        with self.assertRaisesRegex(ValueError, "'Run All Paired Condition Combinations' or "
                                                "provide subset of condition pairs."):
            self.getImpl().run_ballgown_app(self.getContext(), input_params)

    def test_single_condition_ballgown(self):

        # only a single condition is specified (min should be two for condition pairs)
        input_params = {
            #"expressionset_ref": "23192/112/1",
            "expressionset_ref": self.kbasesets_expression_set_ref,
            "diff_expression_matrix_set_name": "single_condition_ballgown",
            #"workspace_name": "arfath:narrative_1498151834637",
            'workspace_name': self.wsName,
            "run_all_combinations": 0,
            "condition_pair_subset": [
                {
                    "condition": "hy5"
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "At least two unique conditions must be specified."):
            self.getImpl().run_ballgown_app(self.getContext(), input_params)

    def test_invalid_condition_ballgown(self):

        # invalid condition names
        input_params = {
            #"expressionset_ref": "23192/112/1",
            "expressionset_ref": self.kbasesets_expression_set_ref,
            "diff_expression_matrix_set_name": "invalid_condition",
            #"workspace_name": "arfath:narrative_1498151834637",
            'workspace_name': self.wsName,
            "run_all_combinations": 0,
            "condition_pair_subset": [
                {
                    "condition": "dummy1"
                },
                {
                    "condition": "dummy2"
                }
            ]
        }

        with self.assertRaisesRegex(ValueError, "is not a valid condition. Must be one of"):
            self.getImpl().run_ballgown_app(self.getContext(), input_params)
