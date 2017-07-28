# -*- coding: utf-8 -*-
import unittest
import os  # noqa: F401
import json  # noqa: F401
import time
import requests

from os import environ

import shutil
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
from DataFileUtil.DataFileUtilClient import DataFileUtil
from ReadsUtils.ReadsUtilsClient import ReadsUtils
from ReadsAlignmentUtils.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from kb_stringtie.kb_stringtieClient import kb_stringtie
from SetAPI.SetAPIClient import SetAPI

try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint  # noqa: F401

from biokbase.workspace.client import Workspace as workspaceService
from kb_ballgown.kb_ballgownImpl import kb_ballgown
from kb_ballgown.kb_ballgownServer import MethodContext
from kb_ballgown.authclient import KBaseAuth as _KBaseAuth


class kb_ballgownTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_ballgown'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_ballgown',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL)
        cls.serviceImpl = kb_ballgown(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

        cls.gfu = GenomeFileUtil(cls.callback_url)
        cls.dfu = DataFileUtil(cls.callback_url)
        cls.ru = ReadsUtils(cls.callback_url)
        cls.rau = ReadsAlignmentUtils(cls.callback_url, service_ver='dev')
        cls.stringtie = kb_stringtie(cls.callback_url, service_ver='dev')
        cls.set_api = SetAPI(cls.callback_url)

        suffix = int(time.time() * 1000)
        #cls.wsName = "test_kb_ballgown_" + str(suffix)
        cls.wsName = "test_kb_ballgown_1004"
        #cls.wsClient.create_workspace({'workspace': cls.wsName})

        #cls.prepare_data()

    @classmethod
    def tearDownClass(cls):
        pass
        #if hasattr(cls, 'wsName'):
        #    cls.wsClient.delete_workspace({'workspace': cls.wsName})
        #    print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_kb_ballgown_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})  # noqa
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    @classmethod
    def prepare_data(cls):
        # upload genome object
        genbank_file_name = 'minimal.gbff'
        genbank_file_path = os.path.join(cls.scratch, genbank_file_name)
        shutil.copy(os.path.join('data', genbank_file_name), genbank_file_path)

        genome_object_name = 'test_Genome'
        cls.genome_ref = cls.gfu.genbank_to_genome({'file': {'path': genbank_file_path},
                                                    'workspace_name': cls.wsName,
                                                    'genome_name': genome_object_name
                                                    })['genome_ref']

        # upload reads object
        reads_file_name = 'Sample1.fastq'
        reads_file_path = os.path.join(cls.scratch, reads_file_name)
        shutil.copy(os.path.join('data', reads_file_name), reads_file_path)

        reads_object_name_1 = 'test_Reads_1'
        cls.reads_ref_1 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                               'wsname': cls.wsName,
                                               'sequencing_tech': 'Unknown',
                                               'interleaved': 0,
                                               'name': reads_object_name_1
                                               })['obj_ref']

        reads_object_name_2 = 'test_Reads_2'
        cls.reads_ref_2 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                               'wsname': cls.wsName,
                                               'sequencing_tech': 'Unknown',
                                               'interleaved': 0,
                                               'name': reads_object_name_2
                                               })['obj_ref']

        reads_object_name_3 = 'test_Reads_3'
        cls.reads_ref_3 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                               'wsname': cls.wsName,
                                               'sequencing_tech': 'Unknown',
                                               'interleaved': 0,
                                               'name': reads_object_name_3
                                               })['obj_ref']

        reads_object_name_4 = 'test_Reads_4'
        cls.reads_ref_4 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                               'wsname': cls.wsName,
                                               'sequencing_tech': 'Unknown',
                                               'interleaved': 0,
                                               'name': reads_object_name_4
                                               })['obj_ref']

        # upload alignment object
        alignment_file_name = 'accepted_hits.bam'
        # alignment_file_name = 'Ath_WT_R1.fastq.sorted.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data', alignment_file_name), alignment_file_path)

        cls.condition_1 = 'test_condition_1'
        cls.condition_2 = 'test_condition_2'

        alignment_object_name_1 = 'test_Alignment_1'

        cls.alignment_ref_1 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_1,
             'read_library_ref': cls.reads_ref_1,
             'condition': cls.condition_1,
             'library_type': 'single_end',
             'assembly_or_genome_ref': cls.genome_ref
             })['obj_ref']

        alignment_object_name_2 = 'test_Alignment_2'

        cls.alignment_ref_2 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_2,
             'read_library_ref': cls.reads_ref_2,
             'condition': cls.condition_1,
             'library_type': 'single_end',
             'assembly_or_genome_ref': cls.genome_ref
             })['obj_ref']

        alignment_object_name_3 = 'test_Alignment_3'
        cls.alignment_ref_3 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_3,
             'read_library_ref': cls.reads_ref_3,
             'condition': cls.condition_2,
             'library_type': 'single_end',
             'assembly_or_genome_ref': cls.genome_ref,
             'library_type': 'single_end'
             })['obj_ref']

        alignment_object_name_4 = 'test_Alignment_4'
        cls.alignment_ref_4 = cls.rau.upload_alignment(
            {'file_path': alignment_file_path,
             'destination_ref': cls.wsName + '/' + alignment_object_name_4,
             'read_library_ref': cls.reads_ref_4,
             'condition': cls.condition_2,
             'library_type': 'single_end',
             'assembly_or_genome_ref': cls.genome_ref,
             'library_type': 'single_end'
             })['obj_ref']

        # upload sample_set object
        workspace_id = cls.dfu.ws_name_to_id(cls.wsName)
        sample_set_object_name = 'test_Sample_Set'
        sample_set_data = {
            'sampleset_id': sample_set_object_name,
            'sampleset_desc': 'test sampleset object',
            'Library_type': 'SingleEnd',
            'condition': [cls.condition_1, cls.condition_1, cls.condition_2, cls.condition_2],
            'domain': 'Unknown',
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
        cls.sample_set_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])

        # upload alignment_set object
        object_type = 'KBaseRNASeq.RNASeqAlignmentSet'
        alignment_set_object_name = 'test_Alignment_Set'
        alignment_set_data = {
            'genome_id': cls.genome_ref,
            'read_sample_ids': [reads_object_name_1,
                                reads_object_name_2,
                                reads_object_name_3,
                                reads_object_name_4,],
            'mapped_rnaseq_alignments': [{reads_object_name_1: alignment_object_name_1},
                                         {reads_object_name_2: alignment_object_name_2},
                                         {reads_object_name_3: alignment_object_name_3},
                                         {reads_object_name_4: alignment_object_name_4}],
            'mapped_alignments_ids': [{reads_object_name_1: cls.alignment_ref_1},
                                      {reads_object_name_2: cls.alignment_ref_2},
                                      {reads_object_name_3: cls.alignment_ref_3},
                                      {reads_object_name_4: cls.alignment_ref_4}],
            'sample_alignments': [cls.alignment_ref_1,
                                  cls.alignment_ref_2,
                                  cls.alignment_ref_3,
                                  cls.alignment_ref_4],
            'sampleset_id': cls.sample_set_ref}
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                'type': object_type,
                'data': alignment_set_data,
                'name': alignment_set_object_name
            }]
        }

        dfu_oi = cls.dfu.save_objects(save_object_params)[0]
        cls.alignment_set_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])

        # upload expression_set object
        cls.rnaseq_expressionset_ref = cls.stringtie.run_stringtie_app(
            {'alignment_object_ref': cls.alignment_set_ref,
             'workspace_name': cls.wsName,
             "min_read_coverage": 2.5,
             "junction_base": 10,
             "num_threads": 3,
             "min_isoform_abundance": 0.1,
             "min_length": 200,
             "skip_reads_with_no_ref": 1,
             "merge": 0,
             "junction_coverage": 1,
             "ballgown_mode": 1,
             "min_locus_gap_sep_value": 50,
             "disable_trimming": 1})['expression_obj_ref']

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa

    def test_rnaseq_ballgown(self):
        """
        input_params = {
            'expressionset_ref': "23748/19/1",
            #'expressionset_ref': self.expressionset_ref,
            'diff_expression_matrix_set_name': 'MyDiffExpression',
            'workspace_name': self.getWsName(),
            "alpha_cutoff": 0.05,
            "fold_change_cutoff": 1.5,
            'condition_labels': ['test_condition_1', 'test_condition_1', 'test_condition_2', 'test_condition_2'],
            "fold_scale_type": 'log2'
        }
        """

        input_params = {"workspace_name": "KBaseRNASeq_test_arfath_2",
         "expressionset_ref": "23594/26", # "downsized_AT_reads_hisat2_AlignmentSet_stringtie_ExpressionSet",
         "diff_expression_matrix_set_name": "downsized_AT_differential_expression_object_dup",
         "alpha_cutoff": 0.05,
         "fold_change_cutoff": 300,
         "fold_scale_type": "log2+1",
         'condition_labels': ['WT', 'WT', 'hy5', 'hy5']}


        result = self.getImpl().run_ballgown_app(self.getContext(), input_params)[0]


        print('>>>>>>>>>>>>>>>>>>got back results: '+str(result))
    '''
    '''
    def test_kbasesets_ballgown(self):
        expression_set_name = "test_expression_set"
        expression_items = list()

        expression_items.append({
            "label": "hy5",
            "ref": '23594/22/1'
        })
        expression_items.append({
            "label": "hy5",
            "ref": '23594/23/1'
        })
        expression_items.append({
            "label": "wt",
            "ref": '23594/24/1'
        })
        expression_items.append({
            "label": "wt",
            "ref": '23594/25/1'
        })

        expression_set = {
            "description": "test_expressions",
            "items": expression_items
        }
        expression_set_info = self.__class__.set_api.save_expression_set_v1({
            "workspace": self.__class__.wsName,
            "output_object_name": expression_set_name,
            "data": expression_set
        })

        expression_set_ref = expression_set_info['set_ref']


        input_params = {"workspace_name": "KBaseRNASeq_test_arfath_2",
        # "expressionset_ref": "23594/26", # "downsized_AT_reads_hisat2_AlignmentSet_stringtie_ExpressionSet",
        "expressionset_ref": expression_set_ref,
         "diff_expression_matrix_set_name": "downsized_AT_differential_expression_object_dup",
         "alpha_cutoff": 0.05,
         "fold_change_cutoff": 300,
         "fold_scale_type": "log2+1",
         'condition_labels': ['WT', 'WT', 'hy5', 'hy5']}


        result = self.getImpl().run_ballgown_app(self.getContext(), input_params)[0]


        print('>>>>>>>>>>>>>>>>>>got back results: '+str(result))

