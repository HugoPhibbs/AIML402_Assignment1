__author__ = "Hugo Phibbs"
__organization__ = "COSC343/AIML402, University of Otago"
__email__ = "phihu414@student.otago.ac.nz"

from typing import List

from itertools import product

from mastermind import evaluate_guess
import multiprocessing as mp

import numpy as np


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

	def __init__(self, code_length, colours, num_guesses, partition_divisor=33):
		"""
        :param code_length: the length of the code to guess
        :param colours: list of letter representing colours used to play
        :param num_guesses: the max. number of guesses per game
        """

		self.possible_guesses = None
		self.code_length = code_length
		self.colours = colours
		self.num_guesses = num_guesses
		self.possible_guesses_copy = set(product(self.colours, repeat=self.code_length))  # For resetting possible guesses
		self.partition_divisor = partition_divisor
		print(f"partition_divisor:{self.partition_divisor}")

	def possible_score_occurrences(self):
		"""
		Generates a matrix to count occurrences all possible scores.

		To find the number of occurrences use the following formula:

		occurrences = scores[in_place][in_colour]

		Corresponds to the map as discussed in the report - for the sake of clarity in my writing

		Matrix returned is not actually a standard n*m structure. Instead, it looks a bit like:

		[0, 0, 0, 0]
		[0, 0, 0]
		[0, 0]
		[0]

		Since you are indexing scores by the number of in place and in colour pegs, some combinations are just not possible.
		E.g. for a code length of 4, you can't have 3 in place pegs and 2 in colour pegs. Hence, the triangular structure.
		This is to save on a miniscule amount of memory, and I'm all about over-optimisation.

		:return: scores - a matrix of scores (see above)
		"""
		scores = []
		for i in range(self.code_length + 1, 0, -1):
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
			return self.handle_first_guess()

		# Eliminate guesses that is not possible.
		self.remove_possible_guesses(last_guess, in_place, in_colour)

		# return self.find_best_guess(self.possible_guesses, 0, len(self.possible_guesses))[0]
		return self.find_best_guess_multi_core()[0]

	def handle_first_guess(self) -> List[str]:
		"""
        Handles the first guess for the master mind bot

        The first guess is always the same, hence makes sense to do in a separate function, for clarity.

        :return: list of chars the first guess
        """
		# Reset the list of possible guesses, just copy the original list, no need to do expensive product calculation again
		self.possible_guesses = self.possible_guesses_copy.copy()

		# Start of a game, assume that the last_guess is a list of zeros
		partition_length = self.code_length // 2

		# Return a guess that is half the first colour and half the second colour, as per Knuth's algorithm
		return [self.colours[0]] * partition_length + [self.colours[1]] * (int(self.code_length) - partition_length)

	def find_best_guess_multi_core(self):
		"""
        Finds the best guess for an answer using a multicore approach

        Splits the possible guesses into a number of partitions equal to the number of cores on the machine. The size of
        each partition is decided by partitionDivisor, which can be tweaked to improve performance.

        :return: the next best guess
        """
		possible_guesses_list = list(self.possible_guesses) # Convert set to list
		num_parallel_processes = 5  # mp.cpu_count() # Can tweak this as need be
		partition_size = len(possible_guesses_list) // num_parallel_processes

		if partition_size == 0:
			# Handle case where partition size is 0, i.e. number of possible guesses is less than number of processes,
			# so just run on one process, speed effect will be negligible
			return self.find_best_guess(possible_guesses_list, 0, len(possible_guesses_list))
		else:
			pool = mp.Pool(num_parallel_processes)
			results = [pool.apply_async(self.find_best_guess,
										args=(possible_guesses_list, i * partition_size, (i + 1) * partition_size)) for
					   i in range(num_parallel_processes)]
			pool.close()
			pool.join()
			return min(results, key=lambda x: x.get()[1]).get() # Return the best guess, .get() returns the value of the async function

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

		# Instead of looking through the whole range, just look at a random portion of it
		portion_size = (j - i) // self.partition_divisor

		# Function to index in random amounts
		# Has an expected value of E(increment) = portion_size/2
		increment_function = lambda x: x + 1 if portion_size <= 0 else x + np.random.randint(1, portion_size + 1)

		i = 0  # 'Outer' loop index

		while i < j:
			guess = possible_guesses_list[i]
			max_g_score = 0

			possible_scores = self.possible_score_occurrences()
			k = 0  # 'Inner' loop index

			while k < j:
				second_guess = possible_guesses_list[k]
				score = evaluate_guess(guess, second_guess)
				possible_scores[score[0]][score[1]] += 1
				new_score = possible_scores[score[0]][score[1]]
				if new_score > max_g_score:
					max_g_score = new_score
				if max_g_score > lowest_overall_g_score:
					break

				k = increment_function(k)

			if max_g_score < lowest_overall_g_score:
				best_guess = guess
				lowest_overall_g_score = max_g_score

			i = increment_function(i)

		return list(best_guess), lowest_overall_g_score

	def remove_possible_guesses(self, last_guess: List[str], in_place: int, in_colour: int):
		"""
        Remove guesses that are not possible given the last guess and the in_place and in_colour values, as per Knuth's algorithm

        Done in it's own function for clarity

        :param last_guess: list of chars for last guess
        :param in_place: number of chars in last guess that are in the correct place
        :param in_colour: number of chars in last guess that are the correct colour but not in the correct place
        :return:
        """
		for guess in self.possible_guesses.copy():
			if evaluate_guess(last_guess, guess) != (in_place, in_colour):
				self.possible_guesses.remove(guess)
