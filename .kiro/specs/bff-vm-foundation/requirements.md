# Requirements Document - BFF VM Foundation (0.1.1)

## Introduction

This specification covers the implementation of the core BFF (Brainfuck-variant) Virtual Machine and supporting infrastructure that demonstrates **digital abiogenesis** - the emergence of life (self-replicating programs) from random bytes through simple interactions. This is the foundational layer upon which the M|inc economic simulation operates.

The BFF experiment shows HOW life emerges from nothing. The emergence of life is the emergence of purpose. In this case, the purpose is reproduction - programs that successfully copy themselves gain dominance in the population. The M|inc economic layer (kings, knights, mercenaries) will later operate on top of these self-replicating programs, adding incentive structures (wealth, currency, traits) to the evolutionary dynamics.

**Core Principle**: Start with millions of random 64-byte tapes → randomly pair and execute them → after millions of iterations, entropy drops dramatically → complex self-replicating programs emerge → purpose (reproduction) emerges from purposeless random bytes.

## Glossary

- **BFF VM**: Brainfuck-variant Virtual Machine with unified 128-byte tape serving as both code and data, enabling self-modification
- **Program**: A 64-byte sequence that starts as random bytes but can evolve into purposeful self-replicating code
- **Tape**: A 128-byte unified memory space where code==data, allowing programs to modify themselves during execution
- **PC**: Program Counter, indexes into the tape for instruction execution (starts at 0)
- **head0**: First data pointer for read/write operations (starts at byte 0)
- **head1**: Second data pointer for read/write operations (starts at byte 64, the second program's region)
- **Soup**: The primordial population of programs (typically millions) that interact through random pairing
- **Epoch**: One complete cycle where all programs are paired, concatenated, executed, split, and returned to the soup
- **Replication Event**: When a program successfully copies itself during interaction, demonstrating emergent purpose
- **Scheduler**: Algorithm that determines which programs interact each epoch (default: random disjoint pairing)
- **Entropy Drop**: The dramatic decrease in population randomness that signals the emergence of self-replicating structure
- **Digital Abiogenesis**: The emergence of self-replicating programs from random bytes through simple interaction rules

## Requirements

### Requirement 1: Core BFF VM Execution (Digital Substrate)

**User Story:** As a researcher studying digital abiogenesis, I want a deterministic BFF VM that executes self-modifying code with precise halt conditions, so that the emergence of self-replicating programs is reproducible and scientifically valid.

#### Acceptance Criteria

1. WHEN a 128-byte tape is provided to the BFF VM, THE System SHALL initialize PC at 0, head0 at 0, and head1 at 64
2. THE System SHALL support exactly 10 opcodes: `><+-{}.,[]` where approximately 31/32 of random bytes are NO-OPs
3. WHEN an unrecognized byte is encountered, THE System SHALL treat it as a NO-OP and advance PC
4. WHEN PC moves outside the range [0, 127], THE System SHALL halt with reason PC_OOB
5. WHEN head0 or head1 moves outside the range [0, 127], THE System SHALL halt with reason OOB_POINTER
6. WHEN a bracket `[` or `]` has no matching pair, THE System SHALL halt with reason UNMATCHED_BRACKET
7. WHEN the step limit is reached, THE System SHALL halt with reason STEP_LIMIT
8. THE System SHALL perform dynamic bracket matching at runtime by scanning the tape to support self-modification
9. THE System SHALL return a RunResult containing the final tape state, step count, and halt reason
10. THE System SHALL allow programs to modify their own code during execution through the unified tape model

### Requirement 2: Program Pairing and Interaction (The Primordial Soup Workflow)

**User Story:** As a researcher studying digital abiogenesis, I want programs to interact through the canonical soup workflow (pair → concatenate → execute → split → return), so that self-replicating programs can emerge from random bytes through millions of simple interactions.

#### Acceptance Criteria

1. THE System SHALL provide a random disjoint pairing scheduler that pairs all programs in a population
2. WHEN the population size is odd, THE System SHALL raise an error
3. WHEN two programs A and B are paired, THE System SHALL randomly choose AB or BA concatenation order
4. THE System SHALL execute the concatenated 128-byte tape using the BFF VM with a step limit (default 8192)
5. WHEN execution completes, THE System SHALL split the tape back into two 64-byte programs at the midpoint
6. THE System SHALL replace the original programs with the post-execution results in the soup
7. WHERE mutation is enabled, THE System SHALL apply per-byte mutation after splitting
8. THE System SHALL repeat this workflow for millions of epochs to allow emergence of self-replicating structure

### Requirement 3: Replication Event Detection (Emergence of Purpose)

**User Story:** As a researcher studying the emergence of purpose, I want exact replication events detected without heuristics, so that I can identify when programs have evolved the purpose of self-reproduction.

#### Acceptance Criteria

1. WHEN program A and B interact producing A' and B', THE System SHALL detect if A' == A and B' == A (A_exact_replicator)
2. WHEN program A and B interact producing A' and B', THE System SHALL detect if A' == B and B' == B (B_exact_replicator)
3. WHEN neither exact replication pattern matches, THE System SHALL classify the event as "none"
4. THE System SHALL NOT use thresholds, similarity scores, or heuristics for replication detection
5. THE System SHALL record the before and after states of both programs in the ReplicationEvent
6. THE System SHALL enable tracking of when purposeless random bytes evolve into purposeful self-replicators

### Requirement 4: Population Analytics (Detecting the Entropy Drop)

**User Story:** As a researcher, I want measurable metrics for population diversity and structure, so that I can detect the dramatic entropy drop that signals the emergence of self-replicating life.

#### Acceptance Criteria

1. THE System SHALL compute Shannon entropy in bits for the population byte distribution
2. THE System SHALL compute compression ratio using zlib level 9 compression
3. WHEN self-replicators emerge, THE System SHALL show entropy dropping and compression ratio increasing dramatically
4. THE System SHALL generate opcode histograms counting each of the 10 valid opcodes
5. THE System SHALL identify the top K most common programs with their counts
6. THE System SHALL provide a Hamming distance function for comparing programs
7. THE System SHALL compute all metrics deterministically without randomness
8. THE System SHALL enable detection of the transition from incompressible random soup to highly compressible structured population

### Requirement 5: Replicator Assay

**User Story:** As a researcher, I want to test candidate replicators against random food programs, so that I can verify replication capability.

#### Acceptance Criteria

1. WHEN a candidate program is provided, THE System SHALL test it against N random food programs
2. THE System SHALL execute both AB and BA orientations for each food program
3. THE System SHALL count a success only when BOTH orientations produce exact replication
4. THE System SHALL return the success count and total trials
5. THE System SHALL use deterministic selection when a random seed is provided
6. THE System SHALL NOT use thresholds or partial success criteria

### Requirement 6: Population Snapshots

**User Story:** As a researcher, I want to save and restore population states, so that I can checkpoint experiments and share results.

#### Acceptance Criteria

1. THE System SHALL save populations to compressed JSON format (.json.gz)
2. THE System SHALL encode programs as hexadecimal strings in the snapshot
3. THE System SHALL include optional metadata in the snapshot
4. WHEN loading a snapshot, THE System SHALL validate that all programs are exactly 64 bytes
5. THE System SHALL return both the program list and metadata when loading
6. THE System SHALL use gzip compression to minimize file size

### Requirement 7: Soup Management

**User Story:** As a simulation developer, I want a Soup class that manages population evolution, so that I can run multi-epoch experiments easily.

#### Acceptance Criteria

1. THE System SHALL initialize a Soup with an even population size
2. THE System SHALL generate random initial programs when no seed population is provided
3. THE System SHALL accept a custom random number generator for reproducibility
4. THE System SHALL execute one epoch by pairing, executing, and splitting all programs
5. THE System SHALL optionally record detailed outcomes including replication events
6. THE System SHALL apply post-split mutation when mutation probability is non-zero
7. THE System SHALL increment the epoch counter after each epoch
8. THE System SHALL provide an inject_mutation method for population-wide mutation

### Requirement 8: Command-Line Interface

**User Story:** As a researcher, I want a CLI to run BFF soup experiments, so that I can explore parameter spaces without writing code.

#### Acceptance Criteria

1. THE System SHALL accept population size as a command-line parameter
2. THE System SHALL accept epoch count as a command-line parameter
3. THE System SHALL accept step limit per interaction as a command-line parameter
4. THE System SHALL accept per-byte mutation probability as a command-line parameter
5. THE System SHALL accept a random seed for reproducibility
6. THE System SHALL accept a reporting interval for progress updates
7. THE System SHALL optionally log exact replication events when requested
8. THE System SHALL output metrics including entropy, compression ratio, and top program counts
9. THE System SHALL output opcode histograms at each reporting interval
10. THE System SHALL stream output to stdout for real-time monitoring

### Requirement 9: Foundation for M|inc Economic Layer

**User Story:** As a developer building the M|inc economic simulation, I want the BFF VM to provide a stable foundation for adding economic agents (kings, knights, mercenaries), so that incentive structures can be layered on top of the evolutionary dynamics.

#### Acceptance Criteria

1. THE System SHALL provide a clean separation between the BFF VM layer and future economic layers
2. THE System SHALL enable programs to be associated with economic agents (roles, traits, currency) in future extensions
3. THE System SHALL maintain deterministic execution to support economic simulations with reproducible outcomes
4. THE System SHALL provide hooks for future integration where program interactions can trigger economic events
5. THE System SHALL document that this is the 0.1.1 foundation layer, with M|inc economic integration coming in 0.1.2+
6. THE System SHALL preserve the core principle that self-replication (purpose) emerges first, then economic incentives are added
