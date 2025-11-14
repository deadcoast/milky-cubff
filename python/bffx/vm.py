"""BFF Virtual Machine - Core execution engine for self-modifying programs."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class HaltReason(Enum):
    """Reasons why VM execution halted."""
    STEP_LIMIT = auto()
    OOB_POINTER = auto()
    UNMATCHED_BRACKET = auto()
    PC_OOB = auto()
    NORMAL = auto()


@dataclass
class RunResult:
    """Result of VM execution."""
    tape: bytearray
    steps: int
    reason: HaltReason
    oob_pointer: Optional[str] = None
    unmatched_at: Optional[int] = None


# Opcode constants
OP_HEAD0_RIGHT = ord('>')  # 0x3E
OP_HEAD0_LEFT = ord('<')   # 0x3C
OP_HEAD1_RIGHT = ord('}')  # 0x7D
OP_HEAD1_LEFT = ord('{')   # 0x7B
OP_INCREMENT = ord('+')    # 0x2B
OP_DECREMENT = ord('-')    # 0x2D
OP_COPY_TO_HEAD1 = ord('.') # 0x2E
OP_COPY_FROM_HEAD1 = ord(',') # 0x2C
OP_JUMP_FORWARD = ord('[')  # 0x5B
OP_JUMP_BACKWARD = ord(']') # 0x5D


class BFFVM:
    """BFF Virtual Machine with self-modification support."""
    
    def __init__(self, tape: bytearray, step_limit: int = 8192,
                 init_head0: int = 0, init_head1: int = 64):
        """Initialize the VM.
        
        Args:
            tape: 128-byte tape (code==data)
            step_limit: Maximum instructions to execute
            init_head0: Initial position of head0
            init_head1: Initial position of head1
            
        Raises:
            ValueError: If tape is not exactly 128 bytes
        """
        if len(tape) != 128:
            raise ValueError(f"Tape must be exactly 128 bytes, got {len(tape)}")
        
        self.tape = tape
        self.step_limit = step_limit
        self.pc = 0
        self.head0 = init_head0
        self.head1 = init_head1
        self.steps = 0

    def _find_matching_forward(self, start_pc: int) -> int:
        """Find matching ] for [ at start_pc.
        
        Args:
            start_pc: Position of [ opcode
            
        Returns:
            Position of matching ], or -1 if not found
        """
        depth = 1
        pc = start_pc + 1
        
        while pc < 128:
            if self.tape[pc] == OP_JUMP_FORWARD:
                depth += 1
            elif self.tape[pc] == OP_JUMP_BACKWARD:
                depth -= 1
                if depth == 0:
                    return pc
            pc += 1
        
        return -1
    
    def _find_matching_backward(self, start_pc: int) -> int:
        """Find matching [ for ] at start_pc.
        
        Args:
            start_pc: Position of ] opcode
            
        Returns:
            Position of matching [, or -1 if not found
        """
        depth = 1
        pc = start_pc - 1
        
        while pc >= 0:
            if self.tape[pc] == OP_JUMP_BACKWARD:
                depth += 1
            elif self.tape[pc] == OP_JUMP_FORWARD:
                depth -= 1
                if depth == 0:
                    return pc
            pc -= 1
        
        return -1
    
    def run(self) -> RunResult:
        """Execute the program until halt.
        
        Returns:
            RunResult with final state and halt reason
        """
        while True:
            # Check PC bounds
            if self.pc < 0 or self.pc >= 128:
                return RunResult(
                    tape=self.tape,
                    steps=self.steps,
                    reason=HaltReason.PC_OOB
                )
            
            # Check step limit
            if self.steps >= self.step_limit:
                return RunResult(
                    tape=self.tape,
                    steps=self.steps,
                    reason=HaltReason.STEP_LIMIT
                )
            
            # Fetch instruction
            opcode = self.tape[self.pc]
            self.steps += 1
            
            # Execute opcode
            if opcode == OP_HEAD0_RIGHT:
                self.head0 += 1
                if self.head0 < 0 or self.head0 >= 128:
                    return RunResult(
                        tape=self.tape,
                        steps=self.steps,
                        reason=HaltReason.OOB_POINTER,
                        oob_pointer="head0"
                    )
                self.pc += 1
                
            elif opcode == OP_HEAD0_LEFT:
                self.head0 -= 1
                if self.head0 < 0 or self.head0 >= 128:
                    return RunResult(
                        tape=self.tape,
                        steps=self.steps,
                        reason=HaltReason.OOB_POINTER,
                        oob_pointer="head0"
                    )
                self.pc += 1
                
            elif opcode == OP_HEAD1_RIGHT:
                self.head1 += 1
                if self.head1 < 0 or self.head1 >= 128:
                    return RunResult(
                        tape=self.tape,
                        steps=self.steps,
                        reason=HaltReason.OOB_POINTER,
                        oob_pointer="head1"
                    )
                self.pc += 1
                
            elif opcode == OP_HEAD1_LEFT:
                self.head1 -= 1
                if self.head1 < 0 or self.head1 >= 128:
                    return RunResult(
                        tape=self.tape,
                        steps=self.steps,
                        reason=HaltReason.OOB_POINTER,
                        oob_pointer="head1"
                    )
                self.pc += 1
                
            elif opcode == OP_INCREMENT:
                self.tape[self.head0] = (self.tape[self.head0] + 1) % 256
                self.pc += 1
                
            elif opcode == OP_DECREMENT:
                self.tape[self.head0] = (self.tape[self.head0] - 1) % 256
                self.pc += 1
                
            elif opcode == OP_COPY_TO_HEAD1:
                self.tape[self.head1] = self.tape[self.head0]
                self.pc += 1
                
            elif opcode == OP_COPY_FROM_HEAD1:
                self.tape[self.head0] = self.tape[self.head1]
                self.pc += 1
                
            elif opcode == OP_JUMP_FORWARD:
                if self.tape[self.head0] == 0:
                    match_pc = self._find_matching_forward(self.pc)
                    if match_pc == -1:
                        return RunResult(
                            tape=self.tape,
                            steps=self.steps,
                            reason=HaltReason.UNMATCHED_BRACKET,
                            unmatched_at=self.pc
                        )
                    self.pc = match_pc + 1
                else:
                    self.pc += 1
                    
            elif opcode == OP_JUMP_BACKWARD:
                if self.tape[self.head0] != 0:
                    match_pc = self._find_matching_backward(self.pc)
                    if match_pc == -1:
                        return RunResult(
                            tape=self.tape,
                            steps=self.steps,
                            reason=HaltReason.UNMATCHED_BRACKET,
                            unmatched_at=self.pc
                        )
                    self.pc = match_pc + 1
                else:
                    self.pc += 1
                    
            else:
                # NO-OP for unrecognized bytes
                self.pc += 1
