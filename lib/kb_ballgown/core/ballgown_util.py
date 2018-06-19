import glob
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

from pprint import pprint

from DataFileUtil.DataFileUtilClient import DataFileUtil
from Workspace.WorkspaceClient import Workspace as Workspace
from KBaseReport.KBaseReportClient import KBaseReport
from ReadsAlignmentUtils.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from KBaseFeatureValues.KBaseFeatureValuesClient import KBaseFeatureValues
from DifferentialExpressionUtils.DifferentialExpressionUtilsClient import \
    DifferentialExpressionUtils
from kb_ballgown.core.multi_group import MultiGroup


def log(message, prefix_newline=False):
    """Logging function, provides a hook to suppress or redirect log messages."""
    print(('\n' if prefix_newline else '') + '{0:.2f}'.format(time.time()) + ': ' + str(message))


TOOL_NAME = 'Ballgown'
TOOL_VERSION = '2.8.0'


class BallgownUtil:

    def __init__(self, config):
        self.ws_url = config["workspace-url"]
        self.callback_url = config['SDK_CALLBACK_URL']
        self.token = config['KB_AUTH_TOKEN']
        self.shock_url = config['shock-url']
        self.dfu = DataFileUtil(self.callback_url)
        self.rau = ReadsAlignmentUtils(self.callback_url)
        self.fv = KBaseFeatureValues(self.callback_url)
        self.deu = DifferentialExpressionUtils(self.callback_url)
        self.ws = Workspace(self.ws_url, token=self.token)
        self.scratch = config['scratch']
        self.config = config

    def _xor(self, a, b):
        return bool(a) != bool(b)

    def _validate_run_ballgown_app_params(self, params):
        """
        _validate_run_ballgown_app_params:
                validates params passed to run_ballgown_app method
        """

        log('start validating run_ballgown_app params')

        # check for required parameters
        for p in ['expressionset_ref', 'diff_expression_matrix_set_suffix',
                  'workspace_name']:
            if p not in params:
                raise ValueError('"{}" parameter is required, but missing'.format(p))

        run_all_combinations = params.get('run_all_combinations')
        condition_pair_subset = params.get('condition_pair_subset')

        if not self._xor(run_all_combinations, condition_pair_subset):
            error_msg = "Invalid input:\nselect 'Run All Paired Condition Combinations' "
            error_msg += "or provide subset of condition pairs. Don't provide both, or neither."
            raise ValueError(error_msg)

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

        for file in glob.glob(os.path.join(result_directory, '*.tsv')):
            shutil.copy(file, output_directory)

        # volcano_plot exists only if there are two condition groups
        for file in glob.glob(os.path.join(result_directory, '*.png')):
            shutil.copy(file, output_directory)

        diff_expr_set = self.ws.get_objects2({'objects':
                                              [{'ref':
                                                diff_expression_matrix_set_ref[
                                                    'diffExprMatrixSet_ref']}]})['data'][0]
        diff_expr_set_data = diff_expr_set['data']
        diff_expr_set_info = diff_expr_set['info']
        diff_expr_set_name = diff_expr_set_info[1]

        overview_content = ''
        overview_content += '<br/><table><tr><th>Generated DifferentialExpressionMatrixSet'
        overview_content += ' Object</th></tr>'
        overview_content += '<tr><td>{} ({})'.format(diff_expr_set_name,
                                                     diff_expression_matrix_set_ref[
                                                         'diffExprMatrixSet_ref'])
        overview_content += '</td></tr></table>'

        overview_content += '<p><br/></p>'

        overview_content += '<br/><table><tr><th>Generated DifferentialExpressionMatrix'
        overview_content += ' Object</th><th></th><th></th><th></th></tr>'
        overview_content += '<tr><th>Differential Expression Matrix Name</th>'
        overview_content += '<th>Condition 1</th>'
        overview_content += '<th>Condition 2</th>'
        overview_content += '</tr>'

        for item in diff_expr_set_data['items']:
            item_diffexprmatrix_object = self.ws.get_objects2({'objects':
                                                               [{'ref': item['ref']}]})[
                'data'][0]
            item_diffexprmatrix_info = item_diffexprmatrix_object['info']
            item_diffexprmatrix_data = item_diffexprmatrix_object['data']
            diffexprmatrix_name = item_diffexprmatrix_info[1]

            overview_content += '<tr><td>{} ({})</td>'.format(diffexprmatrix_name,
                                                              item['ref'])
            overview_content += '<td>{}</td>'.format(item_diffexprmatrix_data.
                                                     get('condition_mapping').keys()[0])
            overview_content += '<td>{}</td>'.format(item_diffexprmatrix_data.
                                                     get('condition_mapping').values()[0])
            overview_content += '</tr>'
        overview_content += '</table>'

        # visualization
        image_content = ''
        for image in glob.glob(output_directory + "/*.png"):
            image = image.replace(output_directory + '/', '')
            caption = image.replace(output_directory + '/', '').replace('.png', '')
            image_content += '<p style="text-align:center"><img align="center" src="{}" ' \
                             'width="600" height="400"></a><a target="_blank"><br>' \
                             '<p align="center">{}</p></p>'.format(
                                 image, caption)

        with open(result_file_path, 'w') as result_file:
            with open(os.path.join(os.path.dirname(__file__), 'report_template.html'),
                      'r') as report_template_file:
                report_template = report_template_file.read()
                report_template = report_template.replace('<p>Overview_Content</p>',
                                                          overview_content)
                report_template = report_template.replace('<p>Image Gallery</p>',
                                                          image_content)
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

        output_html_files = self._generate_html_report(
            result_directory, params, diff_expression_matrix_set_ref)

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

    def get_sample_dir_group_file(self, mapped_expression_ids, condition_labels):

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
            raise Exception("At least two condition groups are needed for this analysis. ")
        for group in condition_labels:
            if group_counts[group] < 2:
                raise Exception(
                    "Condition group {0} has less than 2 members; ballgown will not run. "
                    "At least two condition groups are needed for this analysis. ".format(group))

        group_file_dir = os.path.join(self.scratch, str(uuid.uuid4()))
        self._mkdir_p(group_file_dir)

        try:
            condition_labels_uniqued = list(set(condition_labels))
            sgf_name = os.path.join(group_file_dir, 'sample_dir_group_file_' +
                                    condition_labels_uniqued[0] + '_' +
                                    condition_labels_uniqued[1])
            sgf = open(sgf_name, "w")
        except Exception:
            raise Exception(
                "Can't open file {0} for writing {1}".format(
                    sgf_name, traceback.format_exc()))

        index = 0  # condition label index
        for ii in mapped_expression_ids:
            for alignment_id, expression_id in ii.items():
                expression_object = self.ws.get_objects2(
                    {'objects':
                     [{'ref': expression_id}]})['data'][0]
                handle_id = expression_object['data']['file']['hid']
                expression_name = expression_object['info'][1]

                expression_dir = os.path.join(group_file_dir, expression_name)
                self._mkdir_p(expression_dir)

                print('expression_name: ' + str(expression_dir) + ' ' +
                      str(group_name_indices[condition_labels[index]]))
                sgf.write("{0}  {1}\n".format(expression_dir,
                                              group_name_indices[condition_labels[index]]))

                self.dfu.shock_to_file({'handle_id': handle_id,
                                        'file_path': expression_dir,
                                        'unpack': 'unpack'})

                required_files = [
                    'e2t.ctab',
                    'e_data.ctab',
                    'i2t.ctab',
                    'i_data.ctab',
                    't_data.ctab']
                for file in glob.glob(expression_dir + '/*'):
                    if not os.path.basename(file) in required_files:
                        os.remove(file)

            index += 1

        return sgf_name

    def _cleanup(self, directory=None):
        """
        Clean up after the job.  At the moment this just means removing the working
        directory, but later could mean other things.
        """

        try:
            # it would not delete if fold is not empty
            shutil.rmtree(directory, ignore_errors=True)
            # need to iterate each entry
        except IOError as e:
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

    def _check_intron_measurements(self, sample_dir_group_table_file):
        """
        Check if intron measurements files are non-empty
        :param sample_dir_group_table_file:
        :return:
        """
        log('checking for intron level measurements... ')
        file = open(sample_dir_group_table_file, 'r')
        textFileLines = file.readlines()
        for line in textFileLines:
            expr_dir = line.split()[0]
            log(expr_dir)
            i2t_file = open(os.path.join(expr_dir, 'i2t.ctab'), 'r')
            if len(i2t_file.readlines()) <= 1:  # only header line exists
                raise Exception("No intron measurements found! Input expressions are possibly "
                                "from a prokaryote. Ballgown functions only on eukaryotic data."
                                " Consider using DeSeq2 or CuffDiff instead of BallGown.")
            idata_file = open(os.path.join(expr_dir, 'i_data.ctab'), 'r')
            if len(idata_file.readlines()) <= 1:  # only header line exists
                raise Exception("No intron measurements found! Input expressions are possibly "
                                "from a prokaryote. Ballgown functions only on eukaryotic data."
                                " Consider using DeSeq2 or CuffDiff instead of BallGown")

    def run_ballgown_diff_exp(self, rscripts_dir, sample_dir_group_table_file, ballgown_output_dir,
                              output_csv, volcano_plot_file, data_type):
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
        # check if intron-level expression measurements are present
        self._check_intron_measurements(sample_dir_group_table_file)

        rcmd_list = ['Rscript', os.path.join(rscripts_dir, 'ballgown_fpkmgenematrix.R'),
                     '--sample_dir_group_table', sample_dir_group_table_file,
                     '--output_dir', ballgown_output_dir,
                     '--output_csvfile', output_csv,
                     '--volcano_plot_file', volcano_plot_file,
                     '--variance_cutoff', 1 
                     ]
        if data_type == 'transcripts':
            rcmd_list.append('--transcripts')
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
        with open(diff_matrix_file, "r") as csv_file:
            csv_rows = csv.reader(csv_file, delimiter="\t", quotechar='"')
            for row in csv_rows:
                n = n + 1
                if (n == 1):
                    if (row != ['id', 'fc', 'pval', 'qval']):
                        raise Exception(
                            "did not get expected column heading from {0}".format(
                                diff_matrix_file))
                else:
                    if (len(row) != 4):
                        raise Exception(
                            "did not get 4 elements in row {0} of csv file {1} ".format(
                                n, diff_matrix_file))
                    key = row[0]
                    # put in checks for NA or numeric for row[1] through 4
                    if (key in dm):
                        raise Exception(
                            "duplicate key {0} in row {1} of csv file {2} ".format(
                                key, n, diff_matrix_file))
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
            mapped_expression_ids.append({alignment_ref: expression_ref})
        transform['mapped_expression_ids'] = mapped_expression_ids

        return transform

    def _build_condition_label_list(self, mapped_expression_ids):
        """
        Extracts the condition labels from each expression in the specified expression set data
        and builds a list of condition labels
        :param expression_set_data: expression set data
        :return: list of condition labels whose order resembles the expression order in
        the expression data
        """
        condition_labels = list()

        for ii in mapped_expression_ids:
            for alignment_id, expression_id in ii.items():
                expression_object = self.ws.get_objects2(
                    {'objects':
                     [{'ref': expression_id}]})['data'][0]
                condition_labels.append(expression_object['data']['condition'])

        return condition_labels

    def _update_output_file_header(self, output_file):
        """
        Modify header of output file (required by DifferentialExpressionUtils)
        :param output_file:
        :return:
        """
        f = open(output_file, 'r')
        filedata = f.read()
        f.close()

        modified_output = filedata.replace(
            '"id"\t"fc"\t"pval"\t"qval"',
            'gene_id\tlog2_fold_change\tp_value\tq_value')

        f = open(output_file, 'w')
        f.write(modified_output)
        f.close()

    def _check_input_labels(self, condition_pair_subset, available_condition_labels):
        """
        _check_input_labels: check input condition pairs
        """
        checked = True
        # example struct: [{u'condition': u'hy5'}, {u'condition': u'WT'}]
        condition_values = set()
        for condition in condition_pair_subset:
            condition_values.add(condition['condition'])

        if len(condition_values) < 2:
            error_msg = 'At least two unique conditions must be specified. '
            raise ValueError(error_msg)

        for condition in condition_pair_subset:

            label = condition['condition'].strip()
            if label not in available_condition_labels:
                error_msg = 'Condition label "{}" is not a valid condition. '.format(label)
                error_msg += 'Must be one of "{}"'.format(available_condition_labels)
                raise ValueError(error_msg)

        return checked

    def run_ballgown_app(self, params):
        """
        run_ballgown_app: run Ballgown app
        (https://www.bioconductor.org/packages/release/bioc/html/ballgown.html)

        required params:
            expressionset_ref: ExpressionSet object reference
            diff_expression_matrix_set_suffix: suffix to KBaseSets.DifferetialExpressionMatrixSet
            name
            condition_labels: conditions for expression set object
            alpha_cutoff: q value cutoff
            fold_change_cutoff: fold change cutoff
            workspace_name: the name of the workspace it gets saved to

        optional params:
            fold_scale_type: one of ["linear", "log2+1", "log10+1"]

        return:
            result_directory: folder path that holds all files generated by run_deseq2_app
            diff_expression_matrix_set_ref: generated KBaseSets.DifferetialExpressionMatrixSet
            object reference
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
        """differential_expression_suffix = params['diff_expression_matrix_set_suffix']
        expression_name = expression_set_info[1]
        if re.match('.*_[Ee]xpression$', expression_name):
            params['diff_expression_matrix_set_name'] = re.sub(
                '_[Ee]xpression$', differential_expression_suffix, expression_name)
        if re.match('.*_[Ee]xpression_[Ss]et$', expression_name):
            params['diff_expression_matrix_set_name'] = re.sub(
                '_[Ee]xpression_[Ss]et$', differential_expression_suffix, expression_name)
        else:
            params['diff_expression_matrix_set_name'] = expression_name + \
                differential_expression_suffix

        log('--->\nexpression object type: \n' +
            '{}'.format(expression_object_type))"""

        if re.match('KBaseRNASeq.RNASeqExpressionSet-\d.\d', expression_object_type):
            expression_set_data = self.ws.get_objects2(
                {'objects':
                 [{'ref': expressionset_ref}]})['data'][0]['data']

        elif re.match('KBaseSets.ExpressionSet-\d.\d', expression_object_type):
            expression_set_data = self.ws.get_objects2(
                {'objects':
                 [{'ref': expressionset_ref}]})['data'][0]['data']

            expression_set_data = self._transform_expression_set_data(expression_set_data)

        mgroup = MultiGroup(self.ws)
        pairwise_mapped_expression_ids = mgroup.build_pairwise_groups(
            expression_set_data['mapped_expression_ids'])

        ballgown_output_dir = os.path.join(self.scratch, "ballgown_out")
        log("ballgown output dir is {0}".format(ballgown_output_dir))
        self._setupWorkingDir(ballgown_output_dir)

        # get set of all condition labels
        available_condition_labels = \
            self._build_condition_label_list(expression_set_data['mapped_expression_ids'])

        if params.get('run_all_combinations'):
            requested_condition_labels = available_condition_labels
        else:
            # get set of user specified condition labels
            condition_pair_subset = params.get('condition_pair_subset')
            if self._check_input_labels(condition_pair_subset, available_condition_labels):
                requested_condition_labels = list()
                # example: [{u'condition': u'hy5'}, {u'condition': u'WT'}]
                for condition in condition_pair_subset:
                    if condition.get('condition').strip() not in requested_condition_labels:
                        requested_condition_labels.append(condition.get('condition').strip())

        log("User requested pairwise combinations from condition label list : " +
            str(requested_condition_labels))

        diff_expr_files = list()

        for mapped_expression_ids in pairwise_mapped_expression_ids:
            print('processing pairwise combination: ')
            pprint(mapped_expression_ids)
            print('with condtion labels: ')
            condition_labels = self._build_condition_label_list(mapped_expression_ids)
            pprint(condition_labels)

            # skip if condition labels in this pairwise combination don't exist in
            # set of user requested condition labels
            skip = False
            for condition in condition_labels:
                if condition not in requested_condition_labels:
                    log("skipping " + str(condition_labels))
                    skip = True
            if skip:
                continue

            sample_dir_group_file = self.get_sample_dir_group_file(mapped_expression_ids,
                                                                   condition_labels)

            log("about to run_ballgown_diff_exp")
            rscripts_dir = '/kb/module/rscripts'

            condition_labels_uniqued = list()
            for condition in condition_labels:
                if condition not in condition_labels_uniqued:
                    condition_labels_uniqued.append(condition)

            output_csv = 'ballgown_diffexp_' + \
                condition_labels_uniqued[0] + '_' + condition_labels_uniqued[1] + '.tsv'
            volcano_plot_file = 'volcano_plot_' + \
                condition_labels_uniqued[0] + '_' + condition_labels_uniqued[1] + '.png'

            self.run_ballgown_diff_exp(rscripts_dir,
                                       sample_dir_group_file,
                                       ballgown_output_dir,
                                       output_csv,
                                       volcano_plot_file,
                                       params.get('input_type', 'genes'))

            log("back from run_ballgown_diff_exp, about to load diff exp matrix file")
            # diff_expr_matrix = self.load_diff_expr_matrix(ballgown_output_dir,
            # output_csv)  # read file before its zipped

            self._update_output_file_header(os.path.join(ballgown_output_dir, output_csv))

            diff_expr_file = dict()
            diff_expr_file.update({'condition_mapping':
                                   {condition_labels_uniqued[0]: condition_labels_uniqued[1]}})
            diff_expr_file.update(
                {'diffexpr_filepath': os.path.join(ballgown_output_dir, output_csv)})
            diff_expr_files.append(diff_expr_file)

        deu_param = {
            'destination_ref': params['workspace_name'] + '/' +
            params['diff_expression_matrix_set_name'],
            'diffexpr_data': diff_expr_files,
            'tool_used': TOOL_NAME,
            'tool_version': TOOL_VERSION,
            'genome_ref': expression_set_data.get('genome_id'),
        }

        diff_expression_matrix_set_ref = self.deu.save_differential_expression_matrix_set(
            deu_param)

        returnVal = {'result_directory': ballgown_output_dir,
                     'diff_expression_matrix_set_ref':
                         diff_expression_matrix_set_ref['diffExprMatrixSet_ref']}

        report_output = self._generate_report(params,
                                              ballgown_output_dir, diff_expression_matrix_set_ref)
        returnVal.update(report_output)

        return returnVal
