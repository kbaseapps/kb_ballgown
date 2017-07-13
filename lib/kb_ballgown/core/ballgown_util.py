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
        for p in ['expressionset_ref', 'diff_expression_obj_name',
                  'filtered_expression_matrix_name', 'condition_labels', 'workspace_name',
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

    def _run_command(self, command):
        """
        _run_command: run command and print result
        """
        log('Start executing command:\n{}'.format(command))
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output = pipe.communicate()[0]
        exitCode = pipe.returncode

        if (exitCode == 0):
            log('Executed commend:\n{}\n'.format(command) +
                'Exit Code: {}\nOutput:\n{}'.format(exitCode, output))
        else:
            error_msg = 'Error running commend:\n{}\n'.format(command)
            error_msg += 'Exit Code: {}\nOutput:\n{}'.format(exitCode, output)
            raise ValueError(error_msg)

    def _generate_html_report(self, result_directory, params):
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
        shutil.copy2(os.path.join(result_directory, 'volcano_plot.png'),
                     os.path.join(output_directory, 'volcano_plot.png'))

        overview_content = ''
        overview_content += '<p>Generated Differential Expression Object:</p><p>{}</p>'.format(
                                                    params.get('diff_expression_obj_name'))
        overview_content += '<p>Differential Expression Matrix Object:</p><p>{}</p>'.format(
            params.get('filtered_expression_matrix_name'))

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
        plot_file = os.path.join(output_directory, 'ballgown_plot.zip')

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

        with zipfile.ZipFile(plot_file, 'w',
                             zipfile.ZIP_DEFLATED,
                             allowZip64=True) as zip_file:
            for root, dirs, files in os.walk(result_directory):
                for file in files:
                    if file.endswith('.png'):
                        zip_file.write(os.path.join(root, file), file)

        output_files.append({'path': plot_file,
                             'name': os.path.basename(plot_file),
                             'label': os.path.basename(plot_file),
                             'description': 'Visualization plots by Ballgown App'})

        return output_files

    def _generate_report(self, params, result_directory):
        """
        _generate_report: generate summary report
        """
        log('creating report')

        output_files = self._generate_output_file_list(result_directory)

        output_html_files = self._generate_html_report(result_directory, params)

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


    def _generate_diff_expression_data(self, result_directory, expressionset_ref,
                                       diff_expression_obj_name, workspace_name, alpha_cutoff,
                                       fold_change_cutoff, condition_string):
        """
        _generate_diff_expression_data: generate RNASeqDifferentialExpression object data
        """

        diff_expression_data = {
                'tool_used': TOOL_NAME,
                'tool_version': TOOL_VERSION,
                'expressionSet_id': expressionset_ref,
                'genome_id': self.expression_set_data.get('genome_id'),
                'alignmentSet_id': self.expression_set_data.get('alignmentSet_id'),
                'sampleset_id': self.expression_set_data.get('sampleset_id')
        }


        handle = self.dfu.file_to_shock({'file_path': result_directory,
                                         'pack': 'zip',
                                         'make_handle': True})['handle']
        diff_expression_data.update({'file': handle})

        condition = []
        mapped_expr_ids = self.expression_set_data.get('mapped_expression_ids')
        for i in mapped_expr_ids:
            for alignment_id, expression_id in i.items():
                expression_data = self.ws.get_objects2(
                                                {'objects':
                                                 [{'ref': expression_id}]})['data'][0]['data']
                condition.append(expression_data.get('condition'))
        diff_expression_data.update({'condition': condition})

        return diff_expression_data



    def _save_diff_expression(self, result_directory, params):
        """
        _save_diff_expression: save DifferentialExpression object to workspace
        """
        log('start saving RNASeqDifferentialExpression object')

        workspace_name = params.get('workspace_name')
        diff_expression_obj_name = params.get('diff_expression_obj_name')

        if isinstance(workspace_name, int) or workspace_name.isdigit():
            workspace_id = workspace_name
        else:
            workspace_id = self.dfu.ws_name_to_id(workspace_name)

        diff_expression_data = self._generate_diff_expression_data(result_directory,
                                                                   params.get('expressionset_ref'),
                                                                   diff_expression_obj_name,
                                                                   workspace_name,
                                                                   params.get('alpha_cutoff'),
                                                                   params.get('fold_change_cutoff'),
                                                                   params['condition_labels'])

        object_type = 'KBaseRNASeq.RNASeqDifferentialExpression'
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                            'type': object_type,
                            'data': diff_expression_data,
                            'name': diff_expression_obj_name
                        }]
        }

        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        diff_expression_obj_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])

        return diff_expression_obj_ref



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

    def _save_diff_expression(self, result_directory, params):
        """
        _save_diff_expression: save DifferentialExpression object to workspace
        """
        log('start saving RNASeqDifferentialExpression object')

        workspace_name = params.get('workspace_name')
        diff_expression_obj_name = params.get('diff_expression_obj_name')

        if isinstance(workspace_name, int) or workspace_name.isdigit():
            workspace_id = workspace_name
        else:
            workspace_id = self.dfu.ws_name_to_id(workspace_name)

        diff_expression_data = self._generate_diff_expression_data(result_directory,
                                                                   params.get('expressionset_ref'),
                                                                   diff_expression_obj_name,
                                                                   workspace_name,
                                                                   params.get('alpha_cutoff'),
                                                                   params.get('fold_change_cutoff'),
                                                                   params['condition_labels'])

        object_type = 'KBaseRNASeq.RNASeqDifferentialExpression'
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                            'type': object_type,
                            'data': diff_expression_data,
                            'name': diff_expression_obj_name
                        }]
        }

        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        diff_expression_obj_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])

        return diff_expression_obj_ref

    def run_ballgown_diff_exp(self,
                              rscripts_dir,
                              sample_dir_group_table_file,
                              ballgown_output_dir,
                              output_csv,
                              volcano_plot_file
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
                     '--output_csvfile', output_csv,
                     '--volcano_plot_file', volcano_plot_file
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



    def _make_numeric(self, x, msg):
        """
        Convert string to float.
        If x is a float already, no huhu
        :param msg: error message 
        :return: 
        """
        try:
            res = float(x)
        except ValueError:
            raise Exception("illegal non-numeric, {0}".format(msg))
        return res

    def _convert_NA_low(self, x):
        if (x == 'NA' or x == 'Nan'):
            return (-sys.maxint)
        else:
            return (self._make_numeric(x, "convert_NA_low"))

    def filter_genes_diff_expr_matrix(self, diff_expr_matrix,
                                      scale_type,  # "linear", "log2+1", "log10+1"
                                      qval_cutoff,
                                      fold_change_cutoff,
                                      # says this is log2 but we should make it match scale_type
                                      max_genes):
        """
        Returns a list of gene names from the keys of diff_expr_matrix 
        assumed AND logic between all the tests.   The gene_names are 
        ordered by decreasing fold-change
        :param scale_type: 
        :param qval_cutoff: 
        :param fold_change_cutoff: 
        :param max_genes: 
        :return: 
        """

        # verify that qval_cutoff, fold change cutoff is None or numeric.
        # verify scale_type is an allowed value

        # !!!!! figure out what to do with scale conversion

        if max_genes == None:
            max_genes = sys.maxint

        selected = []
        ngenes = 0

        logbase = 0  # by default this indicates linear
        if (scale_type.lower()[0:4] == "log2"):
            logbase = 2
        elif (scale_type.lower()[0:5] == "log10"):
            logbase = 10

        # iterate through keys (genes) in the diff_expr_matrix, sorted by the first value of each row (fc)
        # (decreasing)

        for gene, v in sorted(diff_expr_matrix.iteritems(),
                              key=lambda (k, v): (self._convert_NA_low(v[0]), k), reverse=True):

            fc, pval, qval = diff_expr_matrix[gene]

            if logbase > 0 and fc != 'NA' and fc != 'Nan':
                fc = self._make_numeric(fc, "fc, gene {0}, about to take log{1}".format(gene, logbase))
                try:
                    fc = math.log(fc + 1, logbase)
                except:
                    raise Exception(
                        "unable to take log{0} of fold change value {1}".format(logbase, fc))

            # should NA, NaN fc, qval automatically cause exclusion?

            if (qval_cutoff != None):  # user wants to apply qval_cutoff
                if qval == 'NA' or qval == "Nan":  # bad values automatically excluded
                    continue
                q = self._make_numeric(qval, "qval, gene {0}".format(gene))
                if (q < qval_cutoff):
                    continue

            if (fold_change_cutoff != None):  # user wants to apply fold_change_cutoff
                if fc == 'NA' or fc == "Nan":  # bad values automatically excluded
                    continue
                f = self._make_numeric(fc, "fc, gene {0}".format(gene))
                if (f < fold_change_cutoff):
                    continue

            ngenes = ngenes + 1
            if ngenes > max_genes:
                break

            # if we got here, it made the cut, so add the gene to the list
            selected.append(gene)

        return selected

    def _ws_get_obj_info(self, ws_id, obj_id):
        """
        Workspace helper function
        ws_id is default ws_id and it will be ignored obj_id is ws reference type 
        "ws/obj/ver"
        :param ws_id: 
        :param obj_id: 
        :return: 
        """
        if '/' in obj_id:
            return self.ws.get_object_info_new({"objects": [{'ref': obj_id}]})
        else:
            return self.ws.get_object_info_new(
                {"objects": [{'name': obj_id, 'workspace': ws_id}]})


    def filter_expr_matrix_object(self, emo, selected_list):
        """
        This weeds out all the data (rows, mappings) in given expression matrix object
        for genes not in the given selected_list, and returns a new expression matrix object
        The rows and values presevere the order of the input selected_list
        :param selected_list: 
        :return: 
        """

        fmo = {}
        fmo["type"] = emo["type"]
        fmo["scale"] = emo["scale"]
        fmo["genome_ref"] = emo["genome_ref"]

        fmo["data"] = {}
        fmo["data"]["col_ids"] = emo["data"]["col_ids"]
        fmo["data"]["row_ids"] = []
        fmo["data"]["values"] = []
        fmo["feature_mapping"] = {}

        nrows = len(emo["data"]["row_ids"])
        if nrows != len(emo["data"]["values"]):
            raise Exception("filtering expression matrix:  row count mismatch in expression matrix")

        # make index from gene to row
        gindex = {}
        for i in xrange(nrows):
            gindex[emo["data"]["row_ids"][i]] = i

        for gene in selected_list:
            try:
                i = gindex[gene]
            except:
                raise Exception(
                    "gene {0} from differential expression not found in expression matrix")
            fmo["data"]["row_ids"].append(emo["data"]["row_ids"][i])
            fmo["data"]["values"].append(emo["data"]["values"][i])
            fmo["feature_mapping"][gene] = emo["feature_mapping"][gene]

        return fmo

    def run_ballgown_app(self, params):
        """
        run_ballgown_app: run Ballgown app
        (https://www.bioconductor.org/packages/release/bioc/html/ballgown.html)

        required params:
            expressionset_ref: ExpressionSet object reference
            diff_expression_obj_name: RNASeqDifferetialExpression object name
            filtered_expression_matrix_name: name of output object filtered expression matrix
            condition_labels: conditions for expression set object
            alpha_cutoff: q value cutoff
            fold_change_cutoff: fold change cutoff
            workspace_name: the name of the workspace it gets saved to

        optional params:
            fold_scale_type: one of ["linear", "log2+1", "log10+1"]

        return:
            result_directory: folder path that holds all files generated by run_deseq2_app
            diff_expression_obj_ref: generated RNASeqDifferetialExpression object reference
            filtered_expression_matrix_ref: generated ExpressionMatrix object reference
            report_name: report name generated by KBaseReport
            report_ref: report reference generated by KBaseReport
        """
        log('--->\nrunning BallgownUtil.run_ballgown_app\n' +
            'params:\n{}'.format(json.dumps(params, indent=1)))

        self._validate_run_ballgown_app_params(params)

        expressionset_ref = params.get('expressionset_ref')
        self.expression_set_data = self.ws.get_objects2(
                                                {'objects':
                                                 [{'ref': expressionset_ref}]})['data'][0]['data']

        from pprint import pprint
        print('>>>>>>>>>>expression_set_data: ')
        pprint(self.expression_set_data)

        sample_dir_group_file = self.get_sample_dir_group_file(
            self.expression_set_data, params['condition_labels'])

        ballgown_output_dir = os.path.join(self.scratch, "ballgown_out")
        log("ballgown output dir is {0}".format(ballgown_output_dir))
        self._setupWorkingDir(ballgown_output_dir)

        log("about to run_ballgown_diff_exp")
        rscripts_dir = '/kb/module/rscripts'

        output_csv = "ballgown_diffexp.tsv"

        volcano_plot_file = "volcano_plot.png"

        self.run_ballgown_diff_exp(rscripts_dir,
                                   sample_dir_group_file,
                                   ballgown_output_dir,
                                   output_csv,
                                   volcano_plot_file)

        log("back from run_ballgown_diff_exp, about to load diff exp matrix file")
        diff_expr_matrix = self.load_diff_expr_matrix(ballgown_output_dir,
                                                             output_csv)  # read file before its zipped

        diff_expression_obj_ref = self._save_diff_expression(ballgown_output_dir, params)

        print('>>>>>>>>>>>>>>>matrix: ' + str(diff_expression_obj_ref))

        deu_param = {
            'destination_ref': params['workspace_name'] + '/' + params['filtered_expression_matrix_name'],
            'genome_ref': self.expression_set_data.get('genome_id'),
            'tool_used': TOOL_NAME,
            'tool_version': TOOL_VERSION,
            'diffexpr_filepath': os.path.join(ballgown_output_dir, output_csv)
        }

        diffExprMatrixSet_ref = self.deu.upload_differentialExpression(deu_param)

        returnVal = {'result_directory': ballgown_output_dir,
                     'diff_expression_obj_ref': diff_expression_obj_ref,
                     'diffExprMatrixSet_ref': diffExprMatrixSet_ref}

        print ('>>>>>>>>>>>>>>>>>>diffExprMatrix_ref')
        pprint(diffExprMatrixSet_ref)

        report_output = self._generate_report(params,
                                              ballgown_output_dir)
        returnVal.update(report_output)


        '''
        TODO: This bit of code works but not sure if it belongs here. 
        max_num_genes = sys.maxint  # default
        if 'maximum_num_genes' in params:
            if (params['maximum_num_genes'] != None):
                max_num_genes = params['maximum_num_genes']

        # this returns a list of gene ids passing the specified cuts, ordered by
        # descending fold_change
        if 'fold_change_cutoff' in params:
            fold_change_cutoff = params['fold_change_cutoff']
        else:
            fold_change_cutoff = None

        if len(params['condition_labels']) > 2:  # no fold change for 3 or more conditions
            fold_change_cutoff = None

        selected_gene_list = self.filter_genes_diff_expr_matrix(diff_expr_matrix,
                                                                params['fold_scale_type'],
                                                                params['alpha_cutoff'],
                                                                fold_change_cutoff,
                                                                max_num_genes)

        '''

        return returnVal
