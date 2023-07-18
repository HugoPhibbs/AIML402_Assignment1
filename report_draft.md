# Report Draft

## The Knuth Algorithm Explained

For the following steps, assume that the code is of length 4, and there are a 4 
colours to choose from (Pink, Blue, Green, Red). Assume the real code is "GGRR"
1. Start with an initial guess with just two colours, split down the middle. E.g. "BBRR" or "PPPBB"
TODO find why this is optimal
2. Generate a set of all possible codes that could be correct, call this set S 
   (following convention of Knuth's Algorithm)
3. From this guess. Get some initial feedback from this. For the sake of simplicity, 
   lets call the feedback function:

    F(guess, actual_code) = (num_in_place, num_in_colour)
    
   Say we got the feedback for an initial guess "BBRR" to be F("BBRR", "GGRR") = (2, 0).
   We 
   can then remove any guesses from S that would not give the same feedback if they 
   were the actual code. These are guaranteed to not be the code we are looking for. I.e. we can eliminate the 
   code "PPGG" since F("BBRR", "PPGG") = (0, 2), theres no way that "PPGG" could be 
   the real code. 
4. The next step is the crux of the algorithm. From here we use a min-max strategy. 
   You are pretty much choosing the next best guess that will at best eliminate the most 
   guesses from the set S during step 3. 

Algorithm can be called greedy

