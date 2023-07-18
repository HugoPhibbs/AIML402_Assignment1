__author__ = "<your name>"
__organization__ = "COSC343/AIML402, University of Otago"
__email__ = "<your e-mail>"

from typing import List

import numpy as np
from itertools import product

from mastermind import evaluate_guess
import multiprocessing as mp


class MastermindAgent():
    """
             A class that encapsulates the code dictating the
             behaviour of the agent playing the game of Mastermind.

             ...

             Attributes
             ----------
             code_length: int
                 the length of the code to guess
             colours : list of char
                 a list of colours represented as characters
             num_guesses : int
                 the max. number of guesses per game

             Methods
             -------
             AgentFunction(percepts)
                 Returns the next guess of the colours on the board
             """

    def __init__(self, code_length, colours, num_guesses):
        """
      :param code_length: the length of the code to guess
      :param colours: list of letter representing colours used to play
      :param num_guesses: the max. number of guesses per game
      """

        self.possible_guesses = None
        self.code_length = code_length
        self.colours = colours
        self.num_guesses = num_guesses

    def possible_scores(self):
        scores = []
        for i in range(self.code_length+1, 0, -1):
            scores.append([0] * i)
        return scores


    def AgentFunction(self, percepts) -> List[str]:
        """Returns the next board guess given state of the game in percepts

            :param percepts: a tuple of four items: guess_counter, last_guess, in_place, in_colour

                     , where

                     guess_counter - is an integer indicating how many guesses have been made, starting with 0 for
                                     initial guess;

                     last_guess - is a num_rows x num_cols structure with the copy of the previous guess

                     in_place - is the number of character in the last guess of correct colour and position

                     in_colour - is the number of characters in the last guess of correct colour but not in the
                                 correct position

            :return: list of chars - a list of code_length chars constituting the next guess
            """

        # Extract different parts of percepts.
        guess_counter, last_guess, in_place, in_colour = percepts

        if guess_counter == 0:
            # Reset the list of possible guesses
            self.possible_guesses = set(product(self.colours, repeat=self.code_length))

            # Start of a game, assume that the last_guess is a list of zeros
            partition_length = self.code_length // 2
            return [self.colours[0]] * partition_length + [self.colours[1]] * (int(self.code_length) - partition_length)

        # Eliminate guesses that are not possible.
        self.remove_possible_guesses(last_guess, in_place, in_colour)

        # return self.find_best_guess(self.possible_guesses, 0, len(self.possible_guesses))[0]
        return self.find_best_guess_multi_core()[0]

    def find_best_guess_multi_core(self):
        """
        Finds the best guess for an answer using a multicore approach

        :return: the next best guess
        """
        possible_guesses_list = list(self.possible_guesses)
        num_parallel_processes = 5 #mp.cpu_count() # Can tweak this as need be
        partition_size = len(possible_guesses_list) // num_parallel_processes

        # Handle case where partition size is 0, i.e. number of possible guesses is less than number of processes, so just run on one process, speed effect will be negligible
        if partition_size == 0:
            return self.find_best_guess(possible_guesses_list, 0, len(possible_guesses_list))
        else:
            pool = mp.Pool(num_parallel_processes)
            results = [pool.apply_async(self.find_best_guess, args=(possible_guesses_list, i * partition_size, (i + 1) * partition_size)) for i in range(num_parallel_processes)]
            pool.close()
            pool.join()
            return min(results, key=lambda x: x.get()[1]).get()

    def find_best_guess(self, possible_guesses_list, i, j):
        """
        Finds the next best guess as per Knuth's algorithm

        Does this for a subset of the possible guesses, i.e. from indexes i to j

        :param possible_guesses_list: list of possible guesses
        :param i: start index to search possible guesses
        :param j: end index to search possible guesses
        :return: best guess and lowest overall g score in the index range i to j
        """
        lowest_overall_g_score = float('inf')
        best_guess = None

        for i in range(i, j):
            guess = possible_guesses_list[i]
            max_g_score = 0

            possible_scores = self.possible_scores()

            for second_guess in self.possible_guesses:
                score = evaluate_guess(guess, second_guess)
                possible_scores[score[0]][score[1]] += 1
                new_score = possible_scores[score[0]][score[1]]
                if new_score > max_g_score:
                    max_g_score = new_score
                if max_g_score > lowest_overall_g_score:
                    break

            if max_g_score < lowest_overall_g_score:
                best_guess = guess
                lowest_overall_g_score = max_g_score

        return list(best_guess), lowest_overall_g_score

    def remove_possible_guesses(self, last_guess: List[str], in_place: int, in_colour: int):
        """
        Remove guesses that are not possible given the last guess and the in_place and in_colour values, as per Knuth's algorithm

        :param last_guess: list of chars for last guess
        :param in_place: number of chars in last guess that are in the correct place
        :param in_colour: number of chars in last guess that are the correct colour but not in the correct place
        :return:
        """
        # TODO add docs
        # TODO figure out how this works for report!
        for guess in self.possible_guesses.copy():
            if evaluate_guess(last_guess, guess) != (in_place, in_colour):
                self.possible_guesses.remove(guess)