
package us.kbase.kbballgown;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: BallgownInput</p>
 * <pre>
 * required params:
 * expressionset_ref: ExpressionSet object reference
 * diff_expression_matrix_set_name: KBaseSets.DifferetialExpressionMatrixSet name
 * condition_labels: conditions for expression set object
 * alpha_cutoff: q value cutoff
 * fold_change_cutoff: fold change cutoff
 * num_threads: number of threads
 * workspace_name: the name of the workspace it gets saved to
 * optional params:
 * maximum_num_genes: used to filter genes in the differential expression matrix
 * fold_scale_type: one of ["linear", "log2+1", "log10+1"]
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "expressionset_ref",
    "diff_expression_matrix_set_suffix",
    "condition_labels",
    "alpha_cutoff",
    "fold_change_cutoff",
    "num_threads",
    "workspace_name",
    "maximum_num_genes",
    "fold_scale_type"
})
public class BallgownInput {

    @JsonProperty("expressionset_ref")
    private java.lang.String expressionsetRef;
    @JsonProperty("diff_expression_matrix_set_suffix")
    private java.lang.String diffExpressionMatrixSetSuffix;
    @JsonProperty("condition_labels")
    private List<String> conditionLabels;
    @JsonProperty("alpha_cutoff")
    private Double alphaCutoff;
    @JsonProperty("fold_change_cutoff")
    private Double foldChangeCutoff;
    @JsonProperty("num_threads")
    private Long numThreads;
    @JsonProperty("workspace_name")
    private java.lang.String workspaceName;
    @JsonProperty("maximum_num_genes")
    private Long maximumNumGenes;
    @JsonProperty("fold_scale_type")
    private java.lang.String foldScaleType;
    private Map<java.lang.String, Object> additionalProperties = new HashMap<java.lang.String, Object>();

    @JsonProperty("expressionset_ref")
    public java.lang.String getExpressionsetRef() {
        return expressionsetRef;
    }

    @JsonProperty("expressionset_ref")
    public void setExpressionsetRef(java.lang.String expressionsetRef) {
        this.expressionsetRef = expressionsetRef;
    }

    public BallgownInput withExpressionsetRef(java.lang.String expressionsetRef) {
        this.expressionsetRef = expressionsetRef;
        return this;
    }

    @JsonProperty("diff_expression_matrix_set_suffix")
    public java.lang.String getDiffExpressionMatrixSetSuffix() {
        return diffExpressionMatrixSetSuffix;
    }

    @JsonProperty("diff_expression_matrix_set_suffix")
    public void setDiffExpressionMatrixSetSuffix(java.lang.String diffExpressionMatrixSetSuffix) {
        this.diffExpressionMatrixSetSuffix = diffExpressionMatrixSetSuffix;
    }

    public BallgownInput withDiffExpressionMatrixSetSuffix(java.lang.String diffExpressionMatrixSetSuffix) {
        this.diffExpressionMatrixSetSuffix = diffExpressionMatrixSetSuffix;
        return this;
    }

    @JsonProperty("condition_labels")
    public List<String> getConditionLabels() {
        return conditionLabels;
    }

    @JsonProperty("condition_labels")
    public void setConditionLabels(List<String> conditionLabels) {
        this.conditionLabels = conditionLabels;
    }

    public BallgownInput withConditionLabels(List<String> conditionLabels) {
        this.conditionLabels = conditionLabels;
        return this;
    }

    @JsonProperty("alpha_cutoff")
    public Double getAlphaCutoff() {
        return alphaCutoff;
    }

    @JsonProperty("alpha_cutoff")
    public void setAlphaCutoff(Double alphaCutoff) {
        this.alphaCutoff = alphaCutoff;
    }

    public BallgownInput withAlphaCutoff(Double alphaCutoff) {
        this.alphaCutoff = alphaCutoff;
        return this;
    }

    @JsonProperty("fold_change_cutoff")
    public Double getFoldChangeCutoff() {
        return foldChangeCutoff;
    }

    @JsonProperty("fold_change_cutoff")
    public void setFoldChangeCutoff(Double foldChangeCutoff) {
        this.foldChangeCutoff = foldChangeCutoff;
    }

    public BallgownInput withFoldChangeCutoff(Double foldChangeCutoff) {
        this.foldChangeCutoff = foldChangeCutoff;
        return this;
    }

    @JsonProperty("num_threads")
    public Long getNumThreads() {
        return numThreads;
    }

    @JsonProperty("num_threads")
    public void setNumThreads(Long numThreads) {
        this.numThreads = numThreads;
    }

    public BallgownInput withNumThreads(Long numThreads) {
        this.numThreads = numThreads;
        return this;
    }

    @JsonProperty("workspace_name")
    public java.lang.String getWorkspaceName() {
        return workspaceName;
    }

    @JsonProperty("workspace_name")
    public void setWorkspaceName(java.lang.String workspaceName) {
        this.workspaceName = workspaceName;
    }

    public BallgownInput withWorkspaceName(java.lang.String workspaceName) {
        this.workspaceName = workspaceName;
        return this;
    }

    @JsonProperty("maximum_num_genes")
    public Long getMaximumNumGenes() {
        return maximumNumGenes;
    }

    @JsonProperty("maximum_num_genes")
    public void setMaximumNumGenes(Long maximumNumGenes) {
        this.maximumNumGenes = maximumNumGenes;
    }

    public BallgownInput withMaximumNumGenes(Long maximumNumGenes) {
        this.maximumNumGenes = maximumNumGenes;
        return this;
    }

    @JsonProperty("fold_scale_type")
    public java.lang.String getFoldScaleType() {
        return foldScaleType;
    }

    @JsonProperty("fold_scale_type")
    public void setFoldScaleType(java.lang.String foldScaleType) {
        this.foldScaleType = foldScaleType;
    }

    public BallgownInput withFoldScaleType(java.lang.String foldScaleType) {
        this.foldScaleType = foldScaleType;
        return this;
    }

    @JsonAnyGetter
    public Map<java.lang.String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(java.lang.String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public java.lang.String toString() {
        return ((((((((((((((((((((("BallgownInput"+" [expressionsetRef=")+ expressionsetRef)+", diffExpressionMatrixSetSuffix=")+ diffExpressionMatrixSetSuffix)+", conditionLabels=")+ conditionLabels)+", alphaCutoff=")+ alphaCutoff)+", foldChangeCutoff=")+ foldChangeCutoff)+", numThreads=")+ numThreads)+", workspaceName=")+ workspaceName)+", maximumNumGenes=")+ maximumNumGenes)+", foldScaleType=")+ foldScaleType)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
