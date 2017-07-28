import re
import time
import json
import os
import traceback
import uuid
import errno
import subprocess
import zipfile
import shutil
import csv
import math

import sys
from pprint import pformat
from pprint import pprint

from DataFileUtil.DataFileUtilClient import DataFileUtil
from Workspace.WorkspaceClient import Workspace as Workspace
from KBaseReport.KBaseReportClient import KBaseReport
from ReadsAlignmentUtils.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from KBaseFeatureValues.KBaseFeatureValuesClient import KBaseFeatureValues
from DifferentialExpressionUtils.DifferentialExpressionUtilsClient import DifferentialExpressionUtils
from os.path import isfile, join


def log(message, prefix_newline=False):
    """Logging function, provides a hook to suppress or redirect log messages."""
    print(('\n' if prefix_newline else '') + '{0:.2f}'.format(time.time()) + ': ' + str(message))

TOOL_NAME = 'Ballgown'
TOOL_VERSION = '2.8.0'

class BallgownUtil:


    def _validate_run_ballgown_app_params(self, params):
        """
        _validate_run_ballgown_app_params:
                validates params passed to run_ballgown_app method
        """

        log('start validating run_ballgown_app params')

        # check for required parameters
        for p in ['expressionset_ref', 'diff_expression_matrix_set_name',
                  'condition_labels', 'workspace_name',
                  'alpha_cutoff', 'fold_change_cutoff']:
            if p not in params:
                raise ValueError('"{}" parameter is required, but missing'.format(p))

    def _mkdir_p(self, path):
        """
        _mkdir_p: make directory for given path
        """
        if not path:
            return
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


    def _generate_html_report(self, result_directory, params, diff_expression_matrix_set_ref):
        """
        _generate_html_report: generate html summary report
        """

        log('start generating html report')
        html_report = list()

        output_directory = os.path.join(self.scratch, str(uuid.uuid4()))
        self._mkdir_p(output_directory)
        result_file_path = os.path.join(output_directory, 'report.html')

        shutil.copy2(os.path.join(result_directory, 'ballgown_diffexp.tsv'),
                     os.path.join(output_directory, 'ballgown_diffexp.tsv'))

        overview_content = ''
        overview_content += '<p>Differential Expression Matrix Set:</p><p>{}</p>'.format(
            params.get('diff_expression_matrix_set_name'))

        data_ref = self.ws.get_objects2({'objects':
                          [{'ref': diff_expression_matrix_set_ref['diffExprMatrixSet_ref']}]})
        data_url = self.config['workspace-url']
        data_url = re.sub('/services/ws$', '#jsonview/'+data_ref['data'][0]['refs'][0], data_url)
        overview_content += '<p><a href="{}" target="_blank"> JSON view </a></p>'.format(
            data_url)


        with open(result_file_path, 'w') as result_file:
            with open(os.path.join(os.path.dirname(__file__), 'report_template.html'),
                      'r') as report_template_file:
                report_template = report_template_file.read()
                report_template = report_template.replace('<p>Overview_Content</p>',
                                                          overview_content)
                result_file.write(report_template)

        report_shock_id = self.dfu.file_to_shock({'file_path': output_directory,
                                                  'pack': 'zip'})['shock_id']

        html_report.append({'shock_id': report_shock_id,
                            'name': os.path.basename(result_file_path),
                            'label': os.path.basename(result_file_path),
                            'description': 'HTML summary report for Ballgown App'})
        return html_report

    def _generate_output_file_list(self, result_directory):
        """
        _generate_output_file_list: zip result files and generate file_links for report
        """
        log('Start packing result files')
        output_files = list()

        output_directory = os.path.join(self.scratch, str(uuid.uuid4()))
        self._mkdir_p(output_directory)
        result_file = os.path.join(output_directory, 'ballgown_result.zip')

        with zipfile.ZipFile(result_file, 'w',
                             zipfile.ZIP_DEFLATED,
                             allowZip64=True) as zip_file:
            for root, dirs, files in os.walk(result_directory):
                for file in files:
                    if not (file.endswith('.zip') or
                            file.endswith('.png') or
                            file.endswith('.DS_Store')):
                        zip_file.write(os.path.join(root, file), file)

        output_files.append({'path': result_file,
                             'name': os.path.basename(result_file),
                             'label': os.path.basename(result_file),
                             'description': 'File(s) generated by Ballgown App'})

        return output_files

    def _generate_report(self, params, result_directory, diff_expression_matrix_set_ref):
        """
        _generate_report: generate summary report
        """
        log('creating report')

        output_files = self._generate_output_file_list(result_directory)

        output_html_files = self._generate_html_report(result_directory, params, diff_expression_matrix_set_ref)

        report_params = {
              'message': '',
              'workspace_name': params.get('workspace_name'),
              'file_links': output_files,
              'html_links': output_html_files,
              'direct_html_link_index': 0,
              'html_window_height': 333,
              'report_object_name': 'kb_ballgown_report_' + str(uuid.uuid4())}

        kbase_report_client = KBaseReport(self.callback_url)
        output = kbase_report_client.create_extended_report(report_params)

        report_output = {'report_name': output['name'], 'report_ref': output['ref']}

        return report_output





    def __init__(self, config):
        self.ws_url = config["workspace-url"]
        self.callback_url = config['SDK_CALLBACK_URL']
        self.token = config['KB_AUTH_TOKEN']
        self.shock_url = config['shock-url']
        self.dfu = DataFileUtil(self.callback_url)
        self.rau = ReadsAlignmentUtils(self.callback_url)
        self.fv = KBaseFeatureValues(self.callback_url)
        self.deu = DifferentialExpressionUtils(self.callback_url, service_ver='dev')
        self.ws = Workspace(self.ws_url, token=self.token)
        self.scratch = config['scratch']
        self.config = config

    def get_sample_dir_group_file(self, expression_set_data, condition_labels):

        ngroups = 0
        group_name_indices = {}
        group_counts = {}

        for group in condition_labels:
            if not group in group_name_indices:
                group_name_indices[group] = ngroups
                ngroups = ngroups + 1
            if not group in group_counts:
                group_counts[group] = 1
            else:
                group_counts[group] = group_counts[group] + 1

        # checks for proper ballgown execution:
        if ngroups < 2:
            raise Exception("At least two condition groups are needed for this analysis")
        for group in condition_labels:
            if group_counts[group] < 2:
                raise Exception(
                    "condition group {0} has less than 2 members; ballgown will not run".format(group))

        group_file_dir = os.path.join(self.scratch, str(uuid.uuid4()))
        self._mkdir_p(group_file_dir)

        try:
            sgf_name = os.path.join(group_file_dir,'sample_dir_group_file')
            sgf = open( sgf_name, "w" )
        except Exception:
            raise Exception( "Can't open file {0} for writing {1}".format( sgf_name, traceback.format_exc() ) )


        mapped_expr_ids = expression_set_data.get('mapped_expression_ids')

        index = 0  # condition label index
        for ii in mapped_expr_ids:
            for alignment_id, expression_id in ii.items():
                expression_data = self.ws.get_objects2(
                                                {'objects':
                                                 [{'ref': expression_id}]})['data'][0]['data']
                handle_id = expression_data.get('file').get('hid')
                expression_name = expression_data.get('id')

                expression_dir = os.path.join(group_file_dir, expression_name)
                self._mkdir_p(expression_dir)

                print('expression_name: '+str(expression_dir)+' '+str(group_name_indices[condition_labels[index]]))
                sgf.write("{0}  {1}\n".format(expression_dir, group_name_indices[condition_labels[index]]))

                self.dfu.shock_to_file({'handle_id': handle_id,
                                        'file_path': expression_dir,
                                        'unpack': 'unpack'})
            index += 1

        return sgf_name

    def _cleanup(self, directory=None):
        """
        Clean up after the job.  At the moment this just means removing the working
        directory, but later could mean other things.
        """

        try:
            shutil.rmtree(directory, ignore_errors=True)  # it would not delete if fold is not empty
            # need to iterate each entry
        except IOError, e:
            log("Unable to remove working directory {0}".format(directory))
            raise

    def _setupWorkingDir(self, directory=None):
        """
    	Clean up an existing workingdir and create a new one
        """
        try:
            if os.path.exists(directory):
                self._cleanup(directory)
            os.mkdir(directory)
        except IOError:
            log("Unable to setup working dir {0}".format(directory))
            raise


    def run_ballgown_diff_exp(self,
                              rscripts_dir,
                              sample_dir_group_table_file,
                              ballgown_output_dir,
                              output_csv
                              ):
        """ Make R call to execute the system
        
        :param rscripts_dir: 
        :param sample_dir_group_table_file: 
        
        :param ballgown_output_dir:
          sample_group_table is a listing of output Stringtie subdirectories,
         (full path specification) paired with group label (0 or 1), ie
            /path/WT_rep1_stringtie    0
            /path/WT_rep2_stringtie    0
            /path/EXP_rep1_stringtie   1
            /path/EXP_rep2_stringtie   1
          (order doesn't matter, but the directory-group correspondance does)

        :param output_csv: 
        :param volcano_plot_file: 
        :return: 
        """
        rcmd_list = ['Rscript', os.path.join(rscripts_dir, 'ballgown_fpkmgenematrix.R'),
                     '--sample_dir_group_table', sample_dir_group_table_file,
                     '--output_dir', ballgown_output_dir,
                     '--output_csvfile', output_csv
                     ]
        rcmd_str = " ".join(str(x) for x in rcmd_list)
        log("rcmd_string is {0}".format(rcmd_str))
        openedprocess = subprocess.Popen(rcmd_str, shell=True)
        openedprocess.wait()
        # Make sure the openedprocess.returncode is zero (0)
        if openedprocess.returncode != 0:
            log("R script did not return normally, return code - "
                        + str(openedprocess.returncode))
            raise Exception("Rscript failure")


    def load_diff_expr_matrix(self, ballgown_output_dir, output_csv):
        """
        Reads csv diff expr matrix file from Ballgown and returns as a 
        dictionary of rows with the gene as key.  Each key gives a row of
        length three corresponding to fold_change, pval and qval in string form
        - can include 'NA'
        :param ballgown_output_dir
        :param output_csv: 
        :return: 
        """

        diff_matrix_file = os.path.join(ballgown_output_dir, output_csv)

        if not os.path.isfile(diff_matrix_file):
            raise Exception("differential expression matrix csvfile {0} doesn't exist!".format(
                diff_matrix_file))

        n = 0
        dm = {}
        with  open(diff_matrix_file, "r") as csv_file:
            csv_rows = csv.reader(csv_file, delimiter="\t", quotechar='"')
            for row in csv_rows:
                n = n + 1
                if (n == 1):
                    if (row != ['id', 'fc', 'pval', 'qval']):
                        raise Exception(
                            "did not get expected column heading from {0}".format(diff_matrix_file))
                else:
                    if (len(row) != 4):
                        raise Exception(
                            "did not get 4 elements in row {0} of csv file {1} ".format(n,
                                                                                        diff_matrix_file))
                    key = row[0]
                    # put in checks for NA or numeric for row[1] through 4
                    if (key in dm):
                        raise Exception(
                            "duplicate key {0} in row {1} of csv file {2} ".format(key, n,
                                                                                   diff_matrix_file))
                    dm[key] = row[1:5]

        return dm


    def _transform_expression_set_data(self, expression_set_data):
        """
        The stitch to connect KBaseSets.ExpressionSet-2.0 type data to 
        the older KBaseRNASeq.RNASeqExpressionSet-3.0 that the implementation 
        depends on. This is done by doing a dive into the nested alignment
        object ref and getting the required data
        :param expression_set_data: 
        :return: transformed expression_set_data
        """
        transform = dict()
        # get genome id
        expression_ref = expression_set_data['items'][0]['ref']
        wsid, objid, ver = expression_ref.split('/')
        expression_obj = self.ws.get_objects([{'objid': objid, 'wsid': wsid}])
        transform['genome_id'] = expression_obj[0]['data']['genome_id']

        # get sampleset_id
        #alignment_ref = expression_obj[0]['data']['mapped_rnaseq_alignment'].values()[0]
        #wsid, objid, ver = alignment_ref.split('/')
        #alignment_obj = self.ws.get_objects([{'objid': objid, 'wsid': wsid}])
        #transform['sampleset_id'] = alignment_obj[0]['data']['sampleset_id']

        # build mapped_expression_ids
        mapped_expression_ids = list()
        for item in expression_set_data['items']:
            expression_ref = item['ref']
            wsid, objid, ver = expression_ref.split('/')
            expression_obj = self.ws.get_objects([{'objid': objid, 'wsid': wsid}])
            alignment_ref = expression_obj[0]['data']['mapped_rnaseq_alignment'].values()[0]
            mapped_expression_ids.append({alignment_ref:expression_ref})
        transform['mapped_expression_ids'] = mapped_expression_ids

        return transform


    def run_ballgown_app(self, params):
        """
        run_ballgown_app: run Ballgown app
        (https://www.bioconductor.org/packages/release/bioc/html/ballgown.html)

        required params:
            expressionset_ref: ExpressionSet object reference
            diff_expression_matrix_set_name: KBaseSets.DifferetialExpressionMatrixSet name
            condition_labels: conditions for expression set object
            alpha_cutoff: q value cutoff
            fold_change_cutoff: fold change cutoff
            workspace_name: the name of the workspace it gets saved to

        optional params:
            fold_scale_type: one of ["linear", "log2+1", "log10+1"]

        return:
            result_directory: folder path that holds all files generated by run_deseq2_app
            diff_expression_matrix_set_ref: generated KBaseSets.DifferetialExpressionMatrixSet object reference
            report_name: report name generated by KBaseReport
            report_ref: report reference generated by KBaseReport
        """
        log('--->\nrunning BallgownUtil.run_ballgown_app\n' +
            'params:\n{}'.format(json.dumps(params, indent=1)))

        self._validate_run_ballgown_app_params(params)

        expressionset_ref = params.get('expressionset_ref')

        expression_set_info = self.ws.get_object_info3({
            "objects": [{"ref": expressionset_ref}]})['infos'][0]
        expression_object_type = expression_set_info[2]

        # set output object name
        differential_expression_suffix = '_DifferentialExpression'
        expression_name = expression_set_info[1]
        if re.match('.*_[Ee]xpression$', expression_name):
            params['diff_expression_matrix_set_name'] = re.sub('_[Ee]xpression$', differential_expression_suffix, expression_name)
        else:
            params['diff_expression_matrix_set_name'] = expression_name + differential_expression_suffix

        log('--->\nexpression object type: \n' +
            '{}'.format(expression_object_type))

        if re.match('KBaseRNASeq.RNASeqExpressionSet-\d.\d', expression_object_type):
            expression_set_data = self.ws.get_objects2(
                                                    {'objects':
                                                     [{'ref': expressionset_ref}]})['data'][0]['data']


        elif re.match('KBaseSets.ExpressionSet-\d.\d', expression_object_type):
            expression_set_data = self.ws.get_objects2(
                {'objects':
                     [{'ref': expressionset_ref}]})['data'][0]['data']

            expression_set_data = self._transform_expression_set_data(expression_set_data)

        sample_dir_group_file = self.get_sample_dir_group_file(expression_set_data,
                                                               params['condition_labels'])

        ballgown_output_dir = os.path.join(self.scratch, "ballgown_out")
        log("ballgown output dir is {0}".format(ballgown_output_dir))
        self._setupWorkingDir(ballgown_output_dir)

        log("about to run_ballgown_diff_exp")
        rscripts_dir = '/kb/module/rscripts'

        output_csv = "ballgown_diffexp.tsv"

        self.run_ballgown_diff_exp(rscripts_dir,
                                   sample_dir_group_file,
                                   ballgown_output_dir,
                                   output_csv)

        log("back from run_ballgown_diff_exp, about to load diff exp matrix file")
        diff_expr_matrix = self.load_diff_expr_matrix(ballgown_output_dir,
                                                             output_csv)  # read file before its zipped

        print('differential_expression_matrix: ' + str(diff_expr_matrix))

        deu_param = {
            'destination_ref': params['workspace_name'] + '/' + params['diff_expression_matrix_set_name'],
            'genome_ref': expression_set_data.get('genome_id'),
            'tool_used': TOOL_NAME,
            'tool_version': TOOL_VERSION,
            'diffexpr_filepath': os.path.join(ballgown_output_dir, output_csv)
        }

        diff_expression_matrix_set_ref = self.deu.upload_differentialExpression(deu_param)

        returnVal = {'result_directory': ballgown_output_dir,
                     'diff_expression_matrix_set_ref': diff_expression_matrix_set_ref['diffExprMatrixSet_ref']}


        report_output = self._generate_report(params,
                                              ballgown_output_dir, diff_expression_matrix_set_ref)
        returnVal.update(report_output)

        return returnVal
