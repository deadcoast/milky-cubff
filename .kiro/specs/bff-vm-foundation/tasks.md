# Implementation Plan - BFF VM Foundation (0.1.1)

- [x] 1. Set up bffx package structure and core constants





  - Create `python/bffx/` directory structure
  - Create `__init__.py` with package exports
  - Define core constants (PROGRAM_SIZE=64, TAPE_SIZE=128, DEFAULT_STEP_LIMIT=8192)
  - _Requirements: 1.1, 1.2_

- [x] 2. Implement BFF Virtual Machine (vm.py)





  - [x] 2.1 Create HaltReason enum and RunResult dataclass


    - Define all halt reasons (STEP_LIMIT, OOB_POINTER, UNMATCHED_BRACKET, PC_OOB, NORMAL)
    - Create RunResult with tape, steps, reason, oob_pointer, unmatched_at fields
    - _Requirements: 1.4, 1.5, 1.6, 1.7, 1.9_
  
  - [x] 2.2 Implement BFFVM class initialization

    - Accept 128-byte tape, step_limit, init_head0, init_head1 parameters
    - Initialize PC=0, head0=0, head1=64, steps=0
    - Validate tape size is exactly 128 bytes
    - _Requirements: 1.1_
  

  - [x] 2.3 Implement opcode execution logic

    - Define all 10 opcodes as byte constants (><+-{}.,[] )
    - Implement NO-OP fast path for unrecognized bytes
    - Implement pointer movement opcodes (>, <, }, {)
    - Implement data manipulation opcodes (+, -)
    - Implement copy opcodes (., ,)
    - _Requirements: 1.2, 1.3, 1.10_
  
  - [x] 2.4 Implement dynamic bracket matching

    - Create _find_matching_forward method for [ opcode
    - Create _find_matching_backward method for ] opcode
    - Handle nested brackets with depth counter
    - Return -1 if no match found
    - _Requirements: 1.8_
  
  - [x] 2.5 Implement main execution loop with halt conditions

    - Check PC bounds before each instruction
    - Check head0/head1 bounds for data operations
    - Detect unmatched brackets and record PC
    - Halt on step limit reached
    - Return RunResult with final state
    - _Requirements: 1.4, 1.5, 1.6, 1.7, 1.9_

- [x] 3. Implement scheduler (scheduler.py)




  - [x] 3.1 Create random_disjoint_pairs function


    - Accept population size n and random.Random instance
    - Validate n is even, raise ValueError if odd
    - Shuffle indices and create disjoint pairs
    - Return list of (i, j) tuples
    - _Requirements: 2.1, 2.2_

- [x] 4. Implement replication detection (detectors.py)






  - [x] 4.1 Create ReplicationEvent dataclass

    - Define kind field with Literal type (A_exact_replicator, B_exact_replicator, none)
    - Store A_before, B_before, A_after, B_after as bytes
    - _Requirements: 3.5_
  

  - [x] 4.2 Implement detect_exact_replication function

    - Validate all programs are exactly 64 bytes
    - Check A_exact_replicator pattern (A' == A and B' == A)
    - Check B_exact_replicator pattern (A' == B and B' == B)
    - Return "none" if neither pattern matches
    - Use exact byte-for-byte comparison (no thresholds)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_

- [x] 5. Implement analytics (analytics.py)





  - [x] 5.1 Implement shannon_entropy_bits function


    - Concatenate all programs into single byte sequence
    - Count byte frequencies using Counter
    - Calculate Shannon entropy: -Σ(p * log2(p))
    - Return entropy in bits
    - _Requirements: 4.1, 4.7_
  

  - [x] 5.2 Implement compress_ratio function

    - Concatenate all programs into single byte sequence
    - Compress using zlib.compress with level 9
    - Return compressed_size / original_size ratio
    - _Requirements: 4.2, 4.7_
  

  - [x] 5.3 Implement opcode_histogram function

    - Iterate through all bytes in all programs
    - Count occurrences using Counter
    - Return Counter object
    - _Requirements: 4.4_
  

  - [x] 5.4 Implement top_programs function

    - Convert programs to bytes for hashing
    - Count occurrences using Counter
    - Return most_common(k) as list of (program, count) tuples
    - _Requirements: 4.5_
  
  - [x] 5.5 Implement hamming distance function


    - Validate both inputs have same length
    - Count positions where bytes differ
    - Return count
    - _Requirements: 4.6_

- [x] 6. Implement snapshot management (snapshot.py)





  - [x] 6.1 Implement save_population_json_gz function


    - Convert programs to hex strings
    - Create JSON payload with meta and programs_hex
    - Write to gzip-compressed file
    - _Requirements: 6.1, 6.2, 6.3, 6.6_
  
  - [x] 6.2 Implement load_population_json_gz function

    - Read gzip-compressed JSON file
    - Parse programs_hex and convert from hex to bytearray
    - Validate all programs are exactly 64 bytes
    - Return (programs, metadata) tuple
    - _Requirements: 6.1, 6.4, 6.5_

- [x] 7. Implement Soup class (soup.py)





  - [x] 7.1 Create Soup class initialization


    - Validate size is even and >= 2
    - Accept optional random.Random instance
    - Generate random initial programs (64 bytes each)
    - Initialize epoch_index to 0
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 7.2 Create PairOutcome dataclass


    - Store i, j (program indices)
    - Store order ("AB" or "BA")
    - Store RunResult from VM execution
    - Store ReplicationEvent from detection
    - _Requirements: 7.5_
  
  - [x] 7.3 Implement epoch method


    - Call scheduler to get disjoint pairs
    - Pre-allocate next_gen array
    - For each pair: concatenate (random AB/BA), execute VM, split, optionally mutate
    - Replace programs in population
    - Increment epoch_index
    - Optionally record outcomes with replication events
    - Return list of PairOutcome
    - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.8, 7.4, 7.5, 7.6, 7.7_
  
  - [x] 7.4 Implement inject_mutation method



    - Iterate through all programs
    - For each byte, apply mutation with given probability
    - Replace byte with random value if mutation occurs
    - _Requirements: 7.8_

- [x] 8. Implement replicator assay (assay.py)





  - [x] 8.1 Implement assay_candidate function


    - Validate candidate is exactly 64 bytes
    - Validate foods list is not empty
    - For each trial: pick random food, test AB and BA orientations
    - Count success only if BOTH orientations show exact replication
    - Return (successes, total_trials) tuple
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 9. Implement CLI (cli.py)





  - [x] 9.1 Create argument parser


    - Add --pop argument (population size, default 1024)
    - Add --epochs argument (epoch count, default 10000)
    - Add --step-limit argument (instruction limit, default 8192)
    - Add --mutate argument (mutation probability, default 0.0)
    - Add --seed argument (random seed, optional)
    - Add --report-every argument (reporting interval, default 100)
    - Add --log-events flag (track replication events)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_
  
  - [x] 9.2 Implement main simulation loop


    - Create seeded RNG
    - Initialize Soup with specified size
    - Run epochs with scheduler
    - Compute and output metrics at reporting intervals
    - Output entropy, compression ratio, top program counts
    - Output opcode histograms
    - Optionally output replication event counts
    - Stream output to stdout
    - _Requirements: 8.8, 8.9, 8.10_

- [ ]* 10. Create integration test for emergence
  - Run small soup (128 programs) for 1000 epochs with mutation
  - Verify entropy decreases over time
  - Verify compression ratio increases over time
  - Verify replication events occur
  - _Requirements: 4.3, 4.8_

- [ ]* 11. Create reproducibility test
  - Run same experiment with same seed twice
  - Verify populations are byte-for-byte identical at each epoch
  - Verify metrics are identical
  - _Requirements: 9.3_

- [ ]* 12. Add documentation and examples
  - Create README.md for bffx package
  - Document the digital abiogenesis workflow
  - Provide example CLI commands
  - Document connection to future M|inc economic layer
  - _Requirements: 9.5, 9.6_
