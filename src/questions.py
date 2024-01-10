from typing import List, Optional

import numpy as np


class Questions:
    NUM: int = 3
    """The number of questions to select from the list of options."""

    FAIKR: List[str] = [
        'What are the main features of iterative deepening?',
        'What are the main features of a local search algorithm?',
        'What are the main features of a swarm intelligence algorithm?',
        'What are the main approaches of deductive planning. Explain the main differences.',
        'What are metaheuristics? Describe the main algorithms that have been presented during the course.',
        'What are non-informed search strategies? Describe the strategies that have been presented during the course.',
        'What is ant colony optimization?',
        'What is modal truth criterion and why it has been defined.',
        'What is conditional planning and which are its main features?',
        'What is Particle Swarm Optimization and which are its main features?',
        'What is hierarchical planning and explain the method presented during the course.',
        'What is Breadth-First Search? Describe this search strategy and discuss its completeness.',
        'What is arc-consistency? Describe the algorithm to achieve it. Explain the properties of values that are'
        ' removed from constraints and of values that are left in the domains.'
    ]
    """The list of options for faikr questions."""

    INTSYS: List[str] = [
        'How do top down ILP algorithms work?',
        'Which is the model of a neural network that enables competitive learning?',
        'What are the hierarchical planning approaches seen during the course?',
        'What are the main features of decision trees compared to neural networks?',
        'What is backpropagation?',
        'What is the theta-subsumption lattice?',
        'What is conditional planning and which are its main features.',
        'What is reinforcement learning and which tasks it solves best?',
        'What is the ant colony algorithm and which are its main features?',
        'What is the modal truth criterion and for what reason it has been defined.',
        'What is the difference between sensing and causal actions? Why and in which type of planners are they used?'
    ]
    """The list of options for intsys questions."""

    @staticmethod
    def faikr(action: str, folder: Optional[str] = None):
        """Selects questions from the list of options and stores the result in the given folder (or prints if None).
        Additionally, the name of the action to be modelled with Kowalsky formulation must be passed."""
        questions = [
            f'Model the action {action} (preconditions, effects and frame axioms),'
            ' and the initial state of the exercise 4 using the Kowalsky formulation,',
            'Build two levels of graph plan for the exercise 4.'
        ]
        questions += list(np.random.choice(Questions.FAIKR, size=Questions.NUM, replace=False))
        Questions._save(questions, folder=folder, name='faikr')

    @staticmethod
    def intsys(folder: Optional[str] = None):
        """Selects questions from the list of options and stores the result in the given folder (or prints if None)."""
        questions = ['Build two levels of graph plan for the exercise 3.']
        questions += list(np.random.choice(Questions.INTSYS, size=Questions.NUM, replace=False))
        Questions._save(questions, folder=folder, name='intsys')

    @staticmethod
    def _save(questions: List[str], folder: Optional[str], name: str):
        """Stores the output in the given folder (or prints it if None)."""
        if folder is None:
            print(name.upper())
            for i, question in enumerate(questions):
                print(f'{i + 1})  {question}')
            print()
        else:
            with open(file=f'{folder}/{name}.txt', mode='w') as f:
                for i, question in enumerate(questions):
                    f.write(f'{i + 1})  {question}\n')
