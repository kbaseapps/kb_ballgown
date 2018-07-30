
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
 * alpha_cutoff: q value cutoff
 * fold_change_cutoff: fold change cutoff
 * num_threads: number of threads
 * workspace_name: the name of the workspace it gets saved to
 * optional params:
 * run_all_combinations: run all paired condition combinations
 * condition_labels: conditions for expression set object
 * maximum_num_genes: used to filter genes in the differential expression matrix
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "expressionset_ref",
    "diff_expression_matrix_set_suffix",
    "num_threads",
    "workspace_name",
    "input_type",
    "run_all_combinations",
    "condition_labels"
})
public class BallgownInput {

    @JsonProperty("expressionset_ref")
    private java.lang.String expressionsetRef;
    @JsonProperty("diff_expression_matrix_set_suffix")
    private java.lang.String diffExpressionMatrixSetSuffix;
    @JsonProperty("num_threads")
    private Long numThreads;
    @JsonProperty("workspace_name")
    private java.lang.String workspaceName;
    @JsonProperty("input_type")
    private java.lang.String inputType;
    @JsonProperty("run_all_combinations")
    private Long runAllCombinations;
    @JsonProperty("condition_labels")
    private List<String> conditionLabels;
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

    @JsonProperty("input_type")
    public java.lang.String getInputType() {
        return inputType;
    }

    @JsonProperty("input_type")
    public void setInputType(java.lang.String inputType) {
        this.inputType = inputType;
    }

    public BallgownInput withInputType(java.lang.String inputType) {
        this.inputType = inputType;
        return this;
    }

    @JsonProperty("run_all_combinations")
    public Long getRunAllCombinations() {
        return runAllCombinations;
    }

    @JsonProperty("run_all_combinations")
    public void setRunAllCombinations(Long runAllCombinations) {
        this.runAllCombinations = runAllCombinations;
    }

    public BallgownInput withRunAllCombinations(Long runAllCombinations) {
        this.runAllCombinations = runAllCombinations;
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
        return ((((((((((((((((("BallgownInput"+" [expressionsetRef=")+ expressionsetRef)+", diffExpressionMatrixSetSuffix=")+ diffExpressionMatrixSetSuffix)+", numThreads=")+ numThreads)+", workspaceName=")+ workspaceName)+", inputType=")+ inputType)+", runAllCombinations=")+ runAllCombinations)+", conditionLabels=")+ conditionLabels)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
