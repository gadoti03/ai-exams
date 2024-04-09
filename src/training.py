from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Iterable

import numpy as np
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from src.exercise import Exercise


@dataclass(frozen=True)
class Leaf:
    """A Leaf in the decision tree."""
    choice: bool = field()
    examples: float = field()
    negative: float = field()

    @property
    def positive(self) -> float:
        return self.examples - self.negative

    def outcome(self, value: bool) -> float:
        return self.positive if self.choice == value else self.negative


@dataclass(frozen=True)
class Decision:
    """The decision tree opened up to the first level"""
    root: str = field()
    leaves: Dict[str, Leaf] = field(init=False, default_factory=dict)


class Training(Exercise):
    """A training set exercise instance."""

    SIZE: Tuple[int, int] = 12, 16
    """The size (lb, ub) of the training set."""

    NAN: Tuple[int, int] = 1, 3
    """The number (lb, ub) of nan values in input instances."""

    ROUND: int = 3
    """The rounding for floating point results."""

    ALIASES: Dict[Any, str] = {np.nan: '?', True: 'yes', False: 'no'}
    """The label aliases for output outcomes and nan values."""

    def text(self, doc: Document):
        doc.add_paragraph('Given the following training set:')
        doc.add_paragraph()
        # build dataset and add table
        c0, c1 = self._inputs.columns  # retrieve the two column to check that only two values were passed
        data = pd.concat([self._inputs, self._output], axis=1).map(lambda x: Training.ALIASES.get(x, x))
        table = doc.add_table(1, 3)
        cells = table.rows[0].cells
        for i, c in enumerate(data.columns):
            cells[i].text = c
            cells[i].paragraphs[0].runs[0].font.bold = True
        for _, row in data.iterrows():
            cells = table.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = v
        for row in table.rows:
            row.height = Cm(0.65)
        table.alignment = WD_ALIGN_PARAGRAPH.CENTER
        table.style = 'Table Grid'
        # add text
        doc.add_paragraph()
        p = doc.add_paragraph(' a)  Compute the entropy of the training set w.r.t. the attribute ')
        p.add_run(self._output.name).bold = True
        doc.add_paragraph(' b)  Compute the gain of the two attributes with respect to these training examples')
        doc.add_paragraph(' c)  Build the decision tree with one level for the training set'
                          ' and compute the labels of each leaf.')
        p = doc.add_paragraph(' d)  Classify the instance: [')
        p.add_run(f'{c0} = {self._value}').bold = True
        p.add_run(' | ')
        p.add_run(f'{c1} = ?').bold = True
        p.add_run(']')

    def solution(self, doc: Document):
        # build the solution by executing the four sub-exercises (entropy, gain, tree, instance)
        doc.add_paragraph(f' a)  {self._entropy(series=self._output)[1]}').alignment = WD_ALIGN_PARAGRAPH.LEFT
        doc.add_paragraph()
        p = doc.add_paragraph(f' b)\n' + '\n'.join(self._gain(feature=column)[1] for column in self._inputs.columns))
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        doc.add_paragraph(f' c)  {self._root()[1]}').alignment = WD_ALIGN_PARAGRAPH.LEFT
        doc.add_paragraph()
        doc.add_paragraph(f' d)  {self._instance()[1]}').alignment = WD_ALIGN_PARAGRAPH.LEFT
        doc.add_paragraph()

    @staticmethod
    def _sample(values: Iterable[str], size: int, nan: int) -> List[str]:
        """Samples <size> elements from values forcing exactly <nan> missing values and at least one sample per type."""
        # reduce the size by the length of the values in order to force them
        size -= len(values)
        # create the list of values by sampling <size - len(values)> elements to be prepended to the list itself
        values = list(values)
        values = list(np.random.choice(values, size=size)) + values
        # sample <nan> indices (within 0..size in order to keep the last values untouched) to be replaced with nan
        for index in np.random.choice(range(size), size=nan, replace=False):
            values[index] = np.nan
        # shuffle the list and return it
        np.random.shuffle(values)
        return values

    @staticmethod
    def _entropy(series: pd.Series, name: Optional[str] = None) -> Tuple[float, str]:
        """Computes the entropy of a series and returns it along with a string solution."""
        # use the given name if present, otherwise the series name
        message = f'info({series.name if name is None else name}) = '
        # compute the partial entropies as -N_i / N * log(N_i / N) and sum them while appending the solution
        entropy = 0.0
        for value, count in series.value_counts().items():
            entropy -= count / len(series) * np.log2(count / len(series))
            message += f'-{count}/{len(series)}*log2({count}/{len(series)}) '
        # append the final entropy and return
        entropy = round(entropy, Training.ROUND)
        message += f'= {entropy}\n'
        return entropy, message

    def __init__(self, output: str, **inputs: Iterable[str]):
        """Builds a training set instance given the name of the output class and the input values indexed by name."""
        # compute the size of the dataset as a random value between <lb> and <ub>
        size = np.random.randint(*self.SIZE)
        # map each input into a vector of given size sampled from the given list and with a random number of nan values
        self._inputs = pd.DataFrame({
            k: self._sample(values=v, size=size, nan=np.random.randint(*self.NAN)) for k, v in inputs.items()
        })
        # if there are rows with all nan values, replace a random feature with a random value at that index
        nan_indices = self._inputs.index[self._inputs.isna().all(axis=1)]
        for index in nan_indices:
            feature = np.random.choice(list(inputs.keys()))
            value = np.random.choice(list(inputs[feature]))
            self._inputs.loc[index, feature] = value
        # build the output as a series of [True, False] values, with the same size as the inputs, and the given name
        self._output: pd.Series = pd.Series(np.random.choice([True, False], size=len(self._inputs)), name=output)
        # randomly choose one value from the first input column which will be part of the final instance
        self._value: str = np.random.choice(self._inputs.iloc[:, 0].dropna().unique())

    def _gain(self, feature: str) -> Tuple[float, str]:
        """Computes the gain of the given input feature and returns it along with a string solution."""
        # retrieve the feature values build the series and the output by ignoring nan values
        values = self._inputs[feature]
        output = self._output[values.notna()]
        series = values.dropna()
        # compute the entropy of the output and assign the message as the first line of the solution
        entropy, message = Training._entropy(series=output)
        # compute the conditional entropy as the weighted sum of output entropies when the input has a certain value
        cond_entropy = 0.0
        sub_entropies = []
        for value in set(series):
            # retrieve the filtered output and compute its entropy (append the message to the solution)
            sub_output = output[series == value]
            sub_entropy, sub_message = Training._entropy(series=sub_output, name=f'{sub_output.name}: {value}')
            message += sub_message
            # increase the conditional entropy by weighting the sub_entropy depending on how many records are present
            cond_entropy += len(sub_output) / len(series) * sub_entropy
            # keep a list of textual version of this computation to be added to the solution later
            sub_entropies.append(f'{len(sub_output)}/{len(series)} * {sub_entropy}')
        # append the computation of the conditional subentropy to the solution
        cond_entropy = round(cond_entropy, Training.ROUND)
        message += f'info({output.name} | {series.name}) = '
        message += ' + '.join(sub_entropies)
        message += f' = {cond_entropy}\n'
        # compute the gain and append its computation to the solution, then return the values
        gain = len(series) / len(self._output) * (entropy - cond_entropy)
        gain = round(gain, Training.ROUND)
        message += f'gain({series.name}) = '
        message += f'{len(series)}/{len(self._output)} * ({entropy} - {cond_entropy}) = {gain}\n'
        return round(gain, Training.ROUND), message

    def _root(self) -> Tuple[Decision, str]:
        """Computes the root of the decision tree with one level and returns it along with a string solution."""
        # compute the gain for all the input features and select the optimal one
        root = pd.Series({column: self._gain(feature=column)[0] for column in self._inputs.columns}).idxmax()
        # retrieve the root series and build a Decision instance with the given root
        series = self._inputs[root]
        decision = Decision(root=root)
        message = f'The attribute chosen as tree root is: {series.name}\n'
        message += f'ROOT: {series.name}\n'
        # iterate through all the values in the series (without nan values) while keeping track of its normalized count
        for value, weight in series.dropna().value_counts(normalize=True).items():
            # retrieve the filtered output based on the value, and the filtered output based on nan values
            sub_output = self._output[series == value]
            nan_output = self._output[series.isna()]
            # the outcome of the leaf is obtained as the class (True/False) with the higher number of occurrences
            # the number of examples is obtained as the length of the output plus the (weighted) number of nan values
            # the number of misclassified examples is obtained as the number of outputs with outcome different from the
            #   computed one, plus the (weighted) number of outputs with different outcome and nan input
            outcome = sub_output.value_counts().idxmax()
            examples = len(sub_output) + weight * len(nan_output)
            examples = round(examples, Training.ROUND)
            misclassified = np.sum(sub_output != outcome) + weight * np.sum(nan_output != outcome)
            misclassified = round(misclassified, Training.ROUND)
            # assign the computed leaf in the dictionary of tree leaves and retrieve the tree label from the outcome
            decision.leaves[value] = Leaf(choice=outcome, examples=examples, negative=misclassified)
            message += f' |--> LEAF: {value} = {Training.ALIASES[outcome]} '
            message += f'(examples: {examples} / misclassified: {misclassified})\n'
        return decision, message

    def _instance(self) -> Tuple[float, str]:
        """Computes the classification probability of the given instance and returns it along with a string solution."""
        # retrieve the root node of the decision tree
        decision, _ = self._root()
        probabilities = {True: 0.0, False: 0.0}
        # if the decision is based on the first column (from which the value is obtained), compute the result from it
        if decision.root == self._inputs.columns[0]:
            # go on the branch of the instance value
            message = f'The new instance will go on the branch: {self._value}\n'
            leaf = decision.leaves[self._value]
            # retrieve the true and false probabilities based on the leaf outcome (True/False)
            for outcome in True, False:
                label = Training.ALIASES[outcome]
                outcome = leaf.outcome(value=outcome)
                probability = round(100 * outcome / leaf.examples, Training.ROUND - 2)
                message += f'  - P({label}) = {leaf.examples - outcome}/{leaf.examples} = {probability}%\n'
                probabilities[outcome] = probability
        else:
            num = len(self._output)
            message = f'Since the tree root is based on {decision.root}, the instance will weight the two results:\n'
            # iterate over the possible outcomes
            for outcome in True, False:
                label = Training.ALIASES[outcome]
                messages = []
                probability = 0.0
                # retrieve the probability as weighted sum of each leaf outcome
                for leaf in decision.leaves.values():
                    probability += leaf.outcome(value=outcome) / len(self._output)
                    msg = f'{round(leaf.examples, Training.ROUND)}/{num} * '
                    msg += f'{round(leaf.outcome(value=outcome), Training.ROUND)}/{leaf.examples}'
                    messages.append(msg)
                probability = round(100 * probability, Training.ROUND - 2)
                message += f'  - P({label}) = ' + ' + '.join(messages) + f' = {probability}%\n'
                probabilities[outcome] = probability
        # return the positive probability and the solution
        return probabilities[True], message
