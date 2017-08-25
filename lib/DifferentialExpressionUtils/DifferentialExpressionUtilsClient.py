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
except:
    # no they aren't
    from baseclient import BaseClient as _BaseClient  # @Reimport
import time


class DifferentialExpressionUtils(object):

    def __init__(
            self, url=None, timeout=30 * 60, user_id=None,
            password=None, token=None, ignore_authrc=False,
            trust_all_ssl_certificates=False,
            auth_svc='https://kbase.us/services/authorization/Sessions/Login',
            service_ver='dev',
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

    def _check_job(self, job_id):
        return self._client._check_job('DifferentialExpressionUtils', job_id)

    def _upload_differentialExpression_submit(self, params, context=None):
        return self._client._submit_job(
             'DifferentialExpressionUtils.upload_differentialExpression', [params],
             self._service_ver, context)

    def upload_differentialExpression(self, params, context=None):
        """
        Uploads the differential expression  *
        :param params: instance of type "UploadDifferentialExpressionParams"
           (*    Required input parameters for uploading Differential
           expression data string   destination_ref        -   object
           reference of Differential expression data. The object ref is
           'ws_name_or_id/obj_name_or_id' where ws_name_or_id is the
           workspace name or id and obj_name_or_id is the object name or id
           string   diffexpr_filepath      -   file path of the differential
           expression data file created by cuffdiff, deseq or ballgown string
           tool_used              -   cufflinks, ballgown or deseq string  
           tool_version           -   version of the tool used string  
           genome_ref             -   genome object reference *) ->
           structure: parameter "destination_ref" of String, parameter
           "diffexpr_filepath" of String, parameter "tool_used" of String,
           parameter "tool_version" of String, parameter "genome_ref" of
           String, parameter "description" of String, parameter "type" of
           String, parameter "scale" of String
        :returns: instance of type "UploadDifferentialExpressionOutput" (*   
           Output from upload differential expression    *) -> structure:
           parameter "diffExprMatrixSet_ref" of String
        """
        job_id = self._upload_differentialExpression_submit(params, context)
        async_job_check_time = self._client.async_job_check_time
        while True:
            time.sleep(async_job_check_time)
            async_job_check_time = (async_job_check_time *
                self._client.async_job_check_time_scale_percent / 100.0)
            if async_job_check_time > self._client.async_job_check_max_time:
                async_job_check_time = self._client.async_job_check_max_time
            job_state = self._check_job(job_id)
            if job_state['finished']:
                return job_state['result'][0]

    def _save_differential_expression_matrix_set_submit(self, params, context=None):
        return self._client._submit_job(
             'DifferentialExpressionUtils.save_differential_expression_matrix_set', [params],
             self._service_ver, context)

    def save_differential_expression_matrix_set(self, params, context=None):
        """
        Uploads the differential expression  *
        :param params: instance of type "SaveDiffExprMatrixSetParams" (*   
           Required input parameters for saving Differential expression data
           string   destination_ref         -  object reference of
           Differential expression data. The object ref is
           'ws_name_or_id/obj_name_or_id' where ws_name_or_id is the
           workspace name or id and obj_name_or_id is the object name or id
           list<DiffExprFile> diffexpr_data -  list of DiffExprFiles
           (condition pair & file) string   tool_used               - 
           cufflinks, ballgown or deseq string   tool_version            - 
           version of the tool used string   genome_ref              - 
           genome object reference *) -> structure: parameter
           "destination_ref" of String, parameter "diffexpr_data" of list of
           type "DiffExprFile"
           (------------------------------------------------------------------
           ---------------) -> structure: parameter "condition_mapping" of
           mapping from String to String, parameter "diffexpr_filepath" of
           String, parameter "delimiter" of String, parameter "tool_used" of
           String, parameter "tool_version" of String, parameter "genome_ref"
           of String, parameter "description" of String, parameter "type" of
           String, parameter "scale" of String
        :returns: instance of type "SaveDiffExprMatrixSetOutput" (*    
           Output from upload differential expression    *) -> structure:
           parameter "diffExprMatrixSet_ref" of String
        """
        job_id = self._save_differential_expression_matrix_set_submit(params, context)
        async_job_check_time = self._client.async_job_check_time
        while True:
            time.sleep(async_job_check_time)
            async_job_check_time = (async_job_check_time *
                self._client.async_job_check_time_scale_percent / 100.0)
            if async_job_check_time > self._client.async_job_check_max_time:
                async_job_check_time = self._client.async_job_check_max_time
            job_state = self._check_job(job_id)
            if job_state['finished']:
                return job_state['result'][0]

    def _download_differentialExpression_submit(self, params, context=None):
        return self._client._submit_job(
             'DifferentialExpressionUtils.download_differentialExpression', [params],
             self._service_ver, context)

    def download_differentialExpression(self, params, context=None):
        """
        Downloads expression *
        :param params: instance of type
           "DownloadDifferentialExpressionParams" (* Required input
           parameters for downloading Differential expression string 
           source_ref   -      object reference of expression source. The
           object ref is 'ws_name_or_id/obj_name_or_id' where ws_name_or_id
           is the workspace name or id and obj_name_or_id is the object name
           or id *) -> structure: parameter "source_ref" of String
        :returns: instance of type "DownloadDifferentialExpressionOutput" (* 
           The output of the download method.  *) -> structure: parameter
           "destination_dir" of String
        """
        job_id = self._download_differentialExpression_submit(params, context)
        async_job_check_time = self._client.async_job_check_time
        while True:
            time.sleep(async_job_check_time)
            async_job_check_time = (async_job_check_time *
                self._client.async_job_check_time_scale_percent / 100.0)
            if async_job_check_time > self._client.async_job_check_max_time:
                async_job_check_time = self._client.async_job_check_max_time
            job_state = self._check_job(job_id)
            if job_state['finished']:
                return job_state['result'][0]

    def _export_differentialExpression_submit(self, params, context=None):
        return self._client._submit_job(
             'DifferentialExpressionUtils.export_differentialExpression', [params],
             self._service_ver, context)

    def export_differentialExpression(self, params, context=None):
        """
        Wrapper function for use by in-narrative downloaders to download expressions from shock *
        :param params: instance of type "ExportParams" (* Required input
           parameters for exporting expression string   source_ref         - 
           object reference of Differential expression. The object ref is
           'ws_name_or_id/obj_name_or_id' where ws_name_or_id is the
           workspace name or id and obj_name_or_id is the object name or id
           *) -> structure: parameter "source_ref" of String
        :returns: instance of type "ExportOutput" -> structure: parameter
           "shock_id" of String
        """
        job_id = self._export_differentialExpression_submit(params, context)
        async_job_check_time = self._client.async_job_check_time
        while True:
            time.sleep(async_job_check_time)
            async_job_check_time = (async_job_check_time *
                self._client.async_job_check_time_scale_percent / 100.0)
            if async_job_check_time > self._client.async_job_check_max_time:
                async_job_check_time = self._client.async_job_check_max_time
            job_state = self._check_job(job_id)
            if job_state['finished']:
                return job_state['result'][0]

    def status(self, context=None):
        job_id = self._client._submit_job('DifferentialExpressionUtils.status', 
            [], self._service_ver, context)
        async_job_check_time = self._client.async_job_check_time
        while True:
            time.sleep(async_job_check_time)
            async_job_check_time = (async_job_check_time *
                self._client.async_job_check_time_scale_percent / 100.0)
            if async_job_check_time > self._client.async_job_check_max_time:
                async_job_check_time = self._client.async_job_check_max_time
            job_state = self._check_job(job_id)
            if job_state['finished']:
                return job_state['result'][0]
