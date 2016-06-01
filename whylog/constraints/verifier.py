import itertools

from whylog.config.investigation_plan import Clue
from whylog.constraints.exceptions import TooManyConstraintsToNegate
from whylog.front.utils import FrontInput


class Verifier(object):
    UNMATCHED = Clue(None, None, None, None)

    @classmethod
    def _create_investigation_result(cls, clues_combination, constraints, linkage):
        """
        basing on clues combination and constraints,
        returns appropriate InvestigationResult object
        which collects information about lines
        (FrontInput objects) instead of Clues
        """
        return InvestigationResult(
            [FrontInput.from_clue(clue) for clue in clues_combination], constraints, linkage
        )

    @classmethod
    def _verify_constraint(cls, combination, effect, index, constraint, constraint_manager):
        """
        checks if specified clues (which represents parsers: 1,2,.. for some rule) and
        effect (which represents parser 0 from this rule) satisfy one given constraint.
        returns True if so, or False otherwise
        """
        constraint_verifier = constraint_manager.get_constraint_object(index, constraint)
        groups = []
        for group_info in constraint['clues_groups']:
            parser_num, group_num = group_info
            if parser_num == 0:
                groups.append(effect.regex_parameters[group_num - 1])
            else:
                if combination[parser_num - 1] == Verifier.UNMATCHED:
                    return False
                groups.append(combination[parser_num - 1].regex_parameters[group_num - 1])
        return constraint_verifier.verify(groups, constraint['params'])

    @classmethod
    def _clues_combinations(cls, clues_tuples, collected_subset=[]):
        """
        recursive generator that returns all permutations according to schema:
        from first pair (list, number) of clues_tuples,
        produces permutations with size 'number' from 'list's elements
        and concatenates it with _clues_combinations invoked on the rest of clues_tuples.
        example:
        >>> xs = [([1, 2, 3], 2), ([4, 5], 1)]
        >>> for l in Verifier._clues_combinations(xs):
        >>>     print l
        [1, 2, 4]
        [1, 2, 5]
        [1, 3, 4]
        [1, 3, 5]
        [2, 1, 4]
        [2, 1, 5]
        [2, 3, 4]
        [2, 3, 5]
        [3, 1, 4]
        [3, 1, 5]
        [3, 2, 4]
        [3, 2, 5]
        it always should be called with empty accumulator,
        that is collected_subset=[]
        """
        if len(clues_tuples) != 0:
            first_list, repetitions_number = clues_tuples[0]
            for clues in itertools.permutations(first_list, repetitions_number):
                for subset in cls._clues_combinations(
                    clues_tuples[1:], collected_subset + list(clues)
                ):
                    yield subset
        else:
            yield collected_subset

    @classmethod
    def _construct_proper_clues_lists(cls, original_clues_lists):
        clues_lists = []
        for clues, occurrences in original_clues_lists:
            if clues:
                clues_lists.append((clues, occurrences))
            else:
                clues_lists.append(([Verifier.UNMATCHED], occurrences))
        return clues_lists

    @classmethod
    def _pack_results_for_constraint_or(cls, combination, constraints):
        return cls._create_investigation_result(
            (clue for clue in combination if not clue == Verifier.UNMATCHED), constraints,
            InvestigationResult.OR
        )

    @classmethod
    def constraints_and(cls, clues_lists, effect, constraints, constraint_manager):
        """
        for each combination of clues (they are generated by _clues_combinations)
        checks if for all given constraints their requirements are satisfied
        and for each such combination produces InvestigationResult object.
        returns list of all produced InvestigationResults
        """
        clues_lists = cls._construct_proper_clues_lists(clues_lists)
        causes = []
        for combination in cls._clues_combinations(clues_lists):
            if all(
                cls._verify_constraint(combination, effect, idx, constraint, constraint_manager)
                for idx, constraint in enumerate(constraints)
            ):
                causes.append(
                    cls._create_investigation_result(
                        combination, constraints, InvestigationResult.AND
                    )
                )
        return causes

    @classmethod
    def constraints_or(cls, clues_lists, effect, constraints, constraint_manager):
        """
        for each combination of clues (they are generated by _clues_combinations)
        checks if for any of given constraints their requirements are satisfied
        and for each such combination produces InvestigationResult object.
        returns list of all produced InvestigationResults
        """
        if not constraints:
            # when there is lack of constraints, but there are existing clues combinations,
            # each of them should be returned
            return [
                cls._pack_results_for_constraint_or(combination, constraints)
                for combination in cls._clues_combinations(clues_lists)
            ]
        causes = []
        clues_lists = cls._construct_proper_clues_lists(clues_lists)
        for combination in cls._clues_combinations(clues_lists):
            verified_constraints = [
                constraint
                for idx, constraint in enumerate(constraints)
                if cls._verify_constraint(combination, effect, idx, constraint, constraint_manager)
            ]  # yapf: disable
            if verified_constraints:
                causes.append(
                    cls._pack_results_for_constraint_or(combination, verified_constraints)
                )
        return causes

    @classmethod
    def constraints_not(cls, clues_lists, effect, constraints, constraint_manager):
        """
        provide investigation if there is zero or one constraint,
        because only in such cases NOT linkage has sense
        """
        if len(constraints) > 1:
            raise TooManyConstraintsToNegate()
        if constraints:
            if clues_lists:
                return cls.single_constraint_not(
                    clues_lists, effect, constraints[0], constraint_manager
                )
        else:
            if clues_lists:
                # if all parsers found their matched logs, the NOT requirement isn't satisfied
                return []
        return [cls._create_investigation_result([], [], InvestigationResult.NOT)]

    @classmethod
    def single_constraint_not(cls, clues_lists, effect, constraint, constraint_manager):
        """
        for each combination of clues (they are generated by _clues_combinations)
        checks for given constraint if its requirements are not satisfied
        and if they are not, it produces InvestigationResult object.
        returns list of all produced InvestigationResults
        """
        clues_lists = cls._construct_proper_clues_lists(clues_lists)
        for combination in cls._clues_combinations(clues_lists):
            if cls._verify_constraint(combination, effect, 0, constraint, constraint_manager):
                # called with constraint index = 0, because this function assumes that there is one constraint
                return []
        return [cls._create_investigation_result([], [constraint], InvestigationResult.NOT)]


class InvestigationResult(object):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    def __init__(self, lines, constraints, cons_linkage):
        self.lines = lines
        self.constraints = constraints
        self.constraints_linkage = cons_linkage

    def __repr__(self):
        if self.constraints_linkage in [self.AND, self.OR]:
            return "\n(\n    result lines: %s;\n    due to '%s' constraints: %s\n)" % (
                self.lines, self.constraints_linkage, self.constraints
            )
        else:
            return "\n(\n    no result lines due to NOT;\n    constraints: %s\n)" % (
                self.constraints
            )

    def __eq__(self, other):
        return all((
            self.lines == other.lines,
            self.constraints == other.constraints,
            self.constraints_linkage == other.constraints_linkage
        ))  # yapf: disable
