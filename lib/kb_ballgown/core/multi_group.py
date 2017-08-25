

class MultiGroup:
    """
    This class breaks condition groups that are larger than size 2 into pair-wise combinations of
    condition groups so that Ballgown can be run on pair-wise conditions. This is because 
    fold-change cannot be calculated for groups sizes greater than 2.
    
    A condition group is a group of expressions generated from the replicates of a single condition.
    """

    def __init__(self, ws):
        """
        
        :param ws: workspace client reference 
        """
        self.ws = ws

    def build_pairwise_groups(self, mapped_expression_ids):
        """
        Breaks the specified mapped expressions into a list of mapped expression elements where
        each element contains a pair-wise combination of condition groups from the input data.
        :param mapped_expression_ids: mapped_expression_id element that may be obtained from the 
                 expression_object's data sub-element. 
        :return: list of mapped_expression_ids containing pair-wise combinations of condition groups
        """
        condition_list = self._get_condition_list(mapped_expression_ids)

        # initialize a list of condition to expression maps
        condition_expression_map = list()

        for ii in mapped_expression_ids:
            for alignment_ref, expression_ref in ii.items():
                wsid, objid, ver = expression_ref.split('/')
                expression_object = self.ws.get_objects([{'objid': objid, 'wsid': wsid}])[0]
                condition = expression_object['data']['condition']
                appended = False
                for jj in range(len(condition_expression_map)):
                    if condition in condition_expression_map[jj]:
                        condition_expression_map[jj][condition].append(ii)  # add the index of the expression
                        appended = True
                if not appended:
                    condition_expression_map.append({condition: [ii]})

        from pprint import pprint
        pprint(condition_expression_map)

        # initialize pairwise groups
        pairwise_groups = list()   # list of mapped_expression_ids

        for ii in range(0, len(condition_expression_map)-1):
            for jj in range(1, len(condition_expression_map)):
                if jj > ii:
                    pairwise_group = list()
                    pairwise_group.extend(condition_expression_map[ii].values()[0])  # add expression replicates from first condition
                    pairwise_group.extend(condition_expression_map[jj].values()[0])  # add expression replicates from second condition
                    pairwise_groups.append(pairwise_group)

        return pairwise_groups


    def _get_condition_list(self, mapped_expression_ids):
        """
        Extracts the condition labels from each expression in the specified mapped expressions
        and builds a list of condition labels
        :param expression_set_data: expression set data
        :return: list of condition labels whose order resembles the expression order in 
        the mapped expressions
        """
        condition_labels = list()

        for ii in mapped_expression_ids:
            for alignment_ref, expression_ref in ii.items():
                wsid, objid, ver = expression_ref.split('/')
                expression_object = self.ws.get_objects([{'objid': objid, 'wsid': wsid}])[0]
                condition_labels.append(expression_object['data']['condition'])

        return condition_labels
