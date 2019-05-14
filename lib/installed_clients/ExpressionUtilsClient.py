# -*- coding: utf-8 -*-
############################################################
#
# Autogenerated by the KBase type compiler -
# any changes made here will be overwritten
#
############################################################

from __future__ import print_function
# the following is a hack to get the baseclient to import whether we're in a
# package or not. This makes pep8 unhappy hence the annotations.
try:
    # baseclient and this client are in a package
    from .baseclient import BaseClient as _BaseClient  # @UnusedImport
except ImportError:
    # no they aren't
    from baseclient import BaseClient as _BaseClient  # @Reimport


class ExpressionUtils(object):

    def __init__(
            self, url=None, timeout=30 * 60, user_id=None,
            password=None, token=None, ignore_authrc=False,
            trust_all_ssl_certificates=False,
            auth_svc='https://ci.kbase.us/services/auth/api/legacy/KBase/Sessions/Login',
            service_ver='release',
            async_job_check_time_ms=100, async_job_check_time_scale_percent=150, 
            async_job_check_max_time_ms=300000):
        if url is None:
            raise ValueError('A url is required')
        self._service_ver = service_ver
        self._client = _BaseClient(
            url, timeout=timeout, user_id=user_id, password=password,
            token=token, ignore_authrc=ignore_authrc,
            trust_all_ssl_certificates=trust_all_ssl_certificates,
            auth_svc=auth_svc,
            async_job_check_time_ms=async_job_check_time_ms,
            async_job_check_time_scale_percent=async_job_check_time_scale_percent,
            async_job_check_max_time_ms=async_job_check_max_time_ms)

    def upload_expression(self, params, context=None):
        """
        Uploads the expression  *
        :param params: instance of type "UploadExpressionParams" (*   
           Required input parameters for uploading a reads expression data
           string   destination_ref        -   object reference of expression
           data. The object ref is 'ws_name_or_id/obj_name_or_id' where
           ws_name_or_id is the workspace name or id and obj_name_or_id is
           the object name or id string   source_dir             -  
           directory with the files to be uploaded string   alignment_ref    
           -   alignment workspace object reference *) -> structure:
           parameter "destination_ref" of String, parameter "source_dir" of
           String, parameter "alignment_ref" of String, parameter
           "genome_ref" of String, parameter "annotation_id" of String,
           parameter "bam_file_path" of String, parameter "transcripts" of
           type "boolean" (A boolean - 0 for false, 1 for true. @range (0,
           1)), parameter "data_quality_level" of Long, parameter
           "original_median" of Double, parameter "description" of String,
           parameter "platform" of String, parameter "source" of String,
           parameter "external_source_date" of String, parameter
           "processing_comments" of String
        :returns: instance of type "UploadExpressionOutput" (*     Output
           from upload expression    *) -> structure: parameter "obj_ref" of
           String
        """
        return self._client.run_job('ExpressionUtils.upload_expression',
                                    [params], self._service_ver, context)

    def download_expression(self, params, context=None):
        """
        Downloads expression *
        :param params: instance of type "DownloadExpressionParams" (*
           Required input parameters for downloading expression string
           source_ref         -       object reference of expression source.
           The object ref is 'ws_name_or_id/obj_name_or_id' where
           ws_name_or_id is the workspace name or id and obj_name_or_id is
           the object name or id *) -> structure: parameter "source_ref" of
           String
        :returns: instance of type "DownloadExpressionOutput" (*  The output
           of the download method.  *) -> structure: parameter
           "destination_dir" of String
        """
        return self._client.run_job('ExpressionUtils.download_expression',
                                    [params], self._service_ver, context)

    def export_expression(self, params, context=None):
        """
        Wrapper function for use by in-narrative downloaders to download expressions from shock *
        :param params: instance of type "ExportParams" (* Required input
           parameters for exporting expression string   source_ref         - 
           object reference of expression source. The object ref is
           'ws_name_or_id/obj_name_or_id' where ws_name_or_id is the
           workspace name or id and obj_name_or_id is the object name or id
           *) -> structure: parameter "source_ref" of String
        :returns: instance of type "ExportOutput" -> structure: parameter
           "shock_id" of String
        """
        return self._client.run_job('ExpressionUtils.export_expression',
                                    [params], self._service_ver, context)

    def get_expressionMatrix(self, params, context=None):
        """
        :param params: instance of type "getExprMatrixParams" (* Following
           are the required input parameters to get Expression Matrix *) ->
           structure: parameter "workspace_name" of String, parameter
           "output_obj_name" of String, parameter "expressionset_ref" of
           String
        :returns: instance of type "getExprMatrixOutput" -> structure:
           parameter "exprMatrix_FPKM_ref" of String, parameter
           "exprMatrix_TPM_ref" of String
        """
        return self._client.run_job('ExpressionUtils.get_expressionMatrix',
                                    [params], self._service_ver, context)

    def get_enhancedFilteredExpressionMatrix(self, params, context=None):
        """
        :param params: instance of type "getEnhancedFEMParams" (* Input
           parameters and method for getting the enhanced Filtered Expresion
           Matrix for viewing *) -> structure: parameter "fem_object_ref" of
           String
        :returns: instance of type "getEnhancedFEMOutput" -> structure:
           parameter "enhanced_FEM" of type "ExpressionMatrix" (A wrapper
           around a FloatMatrix2D designed for simple matricies of Expression
           data.  Rows map to features, and columns map to conditions.  The
           data type includes some information about normalization factors
           and contains mappings from row ids to features and col ids to
           conditions. description - short optional description of the
           dataset type - ? level, ratio, log-ratio scale - ? probably: raw,
           ln, log2, log10 col_normalization - mean_center, median_center,
           mode_center, zscore row_normalization - mean_center,
           median_center, mode_center, zscore feature_mapping - map from
           row_id to feature id in the genome data - contains values for
           (feature,condition) pairs, where features correspond to rows and
           conditions are columns (ie data.values[feature][condition])
           diff_expr_matrix_ref - added to connect filtered expression matrix
           to differential expression matrix used for filtering @optional
           description row_normalization col_normalization @optional
           genome_ref feature_mapping conditionset_ref condition_mapping
           report diff_expr_matrix_ref @metadata ws type @metadata ws scale
           @metadata ws row_normalization @metadata ws col_normalization
           @metadata ws genome_ref as Genome @metadata ws conditionset_ref as
           ConditionSet @metadata ws length(data.row_ids) as feature_count
           @metadata ws length(data.col_ids) as condition_count) ->
           structure: parameter "description" of String, parameter "type" of
           String, parameter "scale" of String, parameter "row_normalization"
           of String, parameter "col_normalization" of String, parameter
           "genome_ref" of type "ws_genome_id" (The workspace ID for a Genome
           data object. @id ws KBaseGenomes.Genome), parameter
           "feature_mapping" of mapping from String to String, parameter
           "conditionset_ref" of type "ws_conditionset_id" (The workspace ID
           for a ConditionSet data object (Note: ConditionSet objects do not
           yet exist - this is for now used as a placeholder). @id ws
           KBaseExperiments.ConditionSet), parameter "condition_mapping" of
           mapping from String to String, parameter "diff_expr_matrix_ref" of
           String, parameter "data" of type "FloatMatrix2D" (A simple 2D
           matrix of floating point numbers with labels/ids for rows and
           columns.  The matrix is stored as a list of lists, with the outer
           list containing rows, and the inner lists containing values for
           each column of that row.  Row/Col ids should be unique. row_ids -
           unique ids for rows. col_ids - unique ids for columns. values -
           two dimensional array indexed as: values[row][col] @metadata ws
           length(row_ids) as n_rows @metadata ws length(col_ids) as n_cols)
           -> structure: parameter "row_ids" of list of String, parameter
           "col_ids" of list of String, parameter "values" of list of list of
           Double, parameter "report" of type "AnalysisReport" (A basic
           report object used for a variety of cases to mark informational
           messages, warnings, and errors related to processing or quality
           control checks of raw data.) -> structure: parameter
           "checkTypeDetected" of String, parameter "checkUsed" of String,
           parameter "checkDescriptions" of list of String, parameter
           "checkResults" of list of type "boolean" (Indicates true or false
           values, false = 0, true = 1 @range [0,1]), parameter "messages" of
           list of String, parameter "warnings" of list of String, parameter
           "errors" of list of String
        """
        return self._client.run_job('ExpressionUtils.get_enhancedFilteredExpressionMatrix',
                                    [params], self._service_ver, context)

    def status(self, context=None):
        return self._client.run_job('ExpressionUtils.status',
                                    [], self._service_ver, context)