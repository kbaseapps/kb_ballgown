import time
import json
import os
import uuid
import errno
import subprocess
import zipfile
import shutil
import csv
import numpy

from DataFileUtil.DataFileUtilClient import DataFileUtil
from Workspace.WorkspaceClient import Workspace as Workspace
from KBaseReport.KBaseReportClient import KBaseReport
from ReadsAlignmentUtils.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from KBaseFeatureValues.KBaseFeatureValuesClient import KBaseFeatureValues


def log(message, prefix_newline=False):
    """Logging function, provides a hook to suppress or redirect log messages."""
    print(('\n' if prefix_newline else '') + '{0:.2f}'.format(time.time()) + ': ' + str(message))


class BallgownUtil:

    PREPDE_TOOLKIT_PATH = '/kb/deployment/bin/prepDE'

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

    def _generate_html_report(self, result_directory, diff_expression_obj_ref,
                              filtered_expression_matrix_ref, params):
        """
        _generate_html_report: generate html summary report
        """

        log('start generating html report')
        html_report = list()

        output_directory = os.path.join(self.scratch, str(uuid.uuid4()))
        self._mkdir_p(output_directory)
        result_file_path = os.path.join(output_directory, 'report.html')

        shutil.copy2(os.path.join(result_directory, 'ballgown_MAplot.png'),
                     os.path.join(output_directory, 'dispersion_plots.png'))
        shutil.copy2(os.path.join(result_directory, 'PCA_MAplot.png'),
                     os.path.join(output_directory, 'PCA_plots.png'))
        shutil.copy2(os.path.join(result_directory, 'pvaluesPlot.png'),
                     os.path.join(output_directory, 'pvalues_plots.png'))
        shutil.copy2(os.path.join(result_directory, 'qvaluesPlot.png'),
                     os.path.join(output_directory, 'qvalues_plots.png'))

        overview_content = ''
        overview_content += '<p>Generated Differential Expression Object:</p><p>{}</p>'.format(
                                                    params.get('diff_expression_obj_name'))
        overview_content += '<br><p>Generated Expression Matrix Object:</p><p>{}</p>'.format(
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

    def _generate_report(self, diff_expression_obj_ref, filtered_expression_matrix_ref,
                         params, result_directory):
        """
        _generate_report: generate summary report
        """
        log('creating report')

        output_files = self._generate_output_file_list(result_directory)

        output_html_files = self._generate_html_report(result_directory,
                                                       diff_expression_obj_ref,
                                                       filtered_expression_matrix_ref,
                                                       params)

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

    def _generate_diff_expression_csv(self, result_directory, alpha_cutoff, fold_change_cutoff,
                                      condition_string):
        """
        _generate_diff_expression_csv: get different expression matrix with Ballgown
        """
        result_files = os.listdir(result_directory)
        if 'gene_count_matrix.csv' not in result_files:
            raise ValueError('Missing gene_count_matrix.csv, available files: {}'.format(
                                                                                    result_files))

        rcmd_list = ['Rscript', os.path.join(os.path.dirname(__file__), 'run_DESeq.R')]
        rcmd_list.extend(['--result_directory', result_directory])
        rcmd_list.extend(['--alpha_cutoff', alpha_cutoff])
        rcmd_list.extend(['--fold_change_cutoff', fold_change_cutoff])
        rcmd_list.extend(['--condition_string', condition_string])

        rcmd_str = " ".join(str(x) for x in rcmd_list)

        self._run_command(rcmd_str)

    def _generate_diff_expression_data(self, result_directory, expressionset_ref,
                                       diff_expression_obj_name, workspace_name, alpha_cutoff,
                                       fold_change_cutoff, condition_string):
        """
        _generate_diff_expression_data: generate RNASeqDifferentialExpression object data
        """

        diff_expression_data = {
                'tool_used': 'Ballgown',
                'tool_version': '2.8.0',
                'expressionSet_id': expressionset_ref,
                'genome_id': self.expression_set_data.get('genome_id'),
                'alignmentSet_id': self.expression_set_data.get('alignmentSet_id'),
                'sampleset_id': self.expression_set_data.get('sampleset_id')
        }

        self._generate_diff_expression_csv(result_directory, alpha_cutoff,
                                           fold_change_cutoff, condition_string)

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

    def _generate_expression_matrix_file(self, result_directory):
        """
        _generate_expression_matrix_file: generate expression matrix file
        """

        expression_matrix_csv_file = os.path.join(result_directory, 'sig_genes_results.csv')
        expression_matrix_tsv_file = os.path.join(result_directory, 'sig_genes_results.tsv')
        with open(expression_matrix_csv_file, 'rb') as source:
            rdr = csv.reader(source)
            with open(expression_matrix_tsv_file, 'wb') as result:
                for r in rdr:
                    result.write('\t'.join(r) + '\n')

        return expression_matrix_tsv_file

    def _get_condition_string(self, result_directory, condition_labels):
        """
        _get_condition_string: get condition string corresponding to givin condition_labels
        """

        count_matrix_file = os.path.join(result_directory, 'gene_count_matrix.csv')
        tmp_count_matrix_file = os.path.join(result_directory, 'tmp_gene_count_matrix.csv')

        with open(count_matrix_file, "rb") as f:
            reader = csv.reader(f)
            columns = reader.next()[1:]

        condition_list = [None] * len(columns)

        sample_expression_ids = self.expression_set_data.get('sample_expression_ids')
        expr_name_condition_mapping = {}
        for sample_expression_id in sample_expression_ids:
            expr_data = self.ws.get_objects2(
                                    {'objects':
                                     [{'ref': sample_expression_id}]})['data'][0]['data']
            expr_name = expr_data['id']
            expr_condition = expr_data['condition']
            expr_name_list = expr_name_condition_mapping.get(expr_condition)
            if expr_name_list:
                expr_name_list.append(expr_name)
                expr_name_condition_mapping.update({expr_condition: expr_name_list})
            else:
                expr_name_condition_mapping.update({expr_condition: [expr_name]})

        for condition_label in condition_labels:
            if condition_label in expr_name_condition_mapping.keys():
                expression_names = expr_name_condition_mapping.get(condition_label)
                for expression_name in expression_names:
                    pos = columns.index(expression_name)
                    condition_list[pos] = condition_label
            else:
                error_msg = 'Condition: {} is not availalbe. '.format(condition_label)
                error_msg += 'Available conditions: {}'.format(expr_name_condition_mapping.keys())
                raise ValueError(error_msg)

        if None in condition_list:
            filtered_pos = [0]
            filtered_condition_list = []
            for condition in condition_list:
                if condition:
                    pos = [i + 1 for i, val in enumerate(condition_list) if val == condition]
                    filtered_pos += pos
                    filtered_condition_list.append(condition)
            filtered_pos = list(set(filtered_pos))
            with open(count_matrix_file, "rb") as source:
                rdr = csv.reader(source)
                with open(tmp_count_matrix_file, "wb") as result:
                    wtr = csv.writer(result)
                    for r in rdr:
                        wtr.writerow(tuple(list(numpy.array(r)[filtered_pos])))
            os.rename(tmp_count_matrix_file, count_matrix_file)
            condition_string = ','.join(filtered_condition_list)
        else:
            condition_string = ','.join(condition_list)

        return condition_string

    def _save_diff_expression(self, result_directory, params):
        """
        _save_diff_expression: save DifferentialExpression object to workspace
        """
        log('start saving RNASeqDifferentialExpression object')

        workspace_name = params.get('workspace_name')
        diff_expression_obj_name = params.get('diff_expression_obj_name')

        condition_string = self._get_condition_string(result_directory,
                                                      params.get('condition_labels'))

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
                                                                   condition_string)

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

    def _save_expression_matrix(self, result_directory, filtered_expression_matrix_name,
                                workspace_name):
        """
        _save_expression_matrix: save ExpressionMatrix object to workspace
        """
        log('start saving ExpressionMatrix object')

        expression_matrix_file = self._generate_expression_matrix_file(result_directory)

        tsv_file_to_matrix_params = {'input_file_path': expression_matrix_file,
                                     'genome_ref': self.expression_set_data.get('genome_id'),
                                     'data_type': 'log2_level',
                                     'data_scale': '1.0',
                                     'output_ws_name': workspace_name,
                                     'output_obj_name': filtered_expression_matrix_name}

        matrix_ref = self.fv.tsv_file_to_matrix(tsv_file_to_matrix_params)['output_matrix_ref']

        return matrix_ref

    def __init__(self, config):
        self.ws_url = config["workspace-url"]
        self.callback_url = config['SDK_CALLBACK_URL']
        self.token = config['KB_AUTH_TOKEN']
        self.shock_url = config['shock-url']
        self.dfu = DataFileUtil(self.callback_url)
        self.rau = ReadsAlignmentUtils(self.callback_url)
        self.fv = KBaseFeatureValues(self.callback_url)
        self.ws = Workspace(self.ws_url, token=self.token)
        self.scratch = config['scratch']

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

        result_directory = os.path.join(self.scratch, str(uuid.uuid4()))
        self._mkdir_p(result_directory)

        expressionset_ref = params.get('expressionset_ref')
        self.expression_set_data = self.ws.get_objects2(
                                                {'objects':
                                                 [{'ref': expressionset_ref}]})['data'][0]['data']

        '''
        diff_expression_obj_ref = self._save_diff_expression(
                                                    result_directory,
                                                    params)

        filtered_expression_matrix_ref = self._save_expression_matrix(
                                                    result_directory,
                                                    params.get('filtered_expression_matrix_name'),
                                                    params.get('workspace_name'))

        returnVal = {'result_directory': result_directory,
                     'diff_expression_obj_ref': diff_expression_obj_ref,
                     'filtered_expression_matrix_ref': filtered_expression_matrix_ref}

        report_output = self._generate_report(diff_expression_obj_ref,
                                              filtered_expression_matrix_ref,
                                              params,
                                              result_directory)
        returnVal.update(report_output)
        '''
        returnVal = {'myReturnVal':'0'}

        return returnVal
