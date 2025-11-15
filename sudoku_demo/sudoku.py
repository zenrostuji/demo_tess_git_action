"""Minimal Sudoku solver used for GitHub Actions demo tests."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

Board = List[List[int]]


def parse_puzzle(puzzle: Sequence[str]) -> Board:
    """Convert a flat iterable of characters into a 9x9 board."""
    digits = []
    for ch in puzzle:
        if ch.isdigit():
            digits.append(int(ch))
        elif ch in {".", "_", "-"}:
            digits.append(0)
    if len(digits) != 81:
        raise ValueError("Sudoku puzzle must yield 81 cells")
    board = [digits[i : i + 9] for i in range(0, 81, 9)]
    return board


def serialize_board(board: Board) -> str:
    """Return board as a single string for easy comparison."""
    return "".join(str(cell) for row in board for cell in row)


def find_empty(board: Board) -> Optional[Tuple[int, int]]:
    for row_idx, row in enumerate(board):
        for col_idx, value in enumerate(row):
            if value == 0:
                return row_idx, col_idx
    return None


def _row_numbers(board: Board, row: int) -> set[int]:
    return {value for value in board[row] if value}


def _column_numbers(board: Board, col: int) -> set[int]:
    return {board[r][col] for r in range(9) if board[r][col]}


def _box_numbers(board: Board, row: int, col: int) -> set[int]:
    start_row = (row // 3) * 3
    start_col = (col // 3) * 3
    numbers = set()
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            value = board[r][c]
            if value:
                numbers.add(value)
    return numbers


def valid_numbers(board: Board, row: int, col: int) -> set[int]:
    used = _row_numbers(board, row) | _column_numbers(board, col) | _box_numbers(board, row, col)
    return {n for n in range(1, 10) if n not in used}


def is_solved(board: Board) -> bool:
    return all(cell != 0 for row in board for cell in row)


def solve(board: Board) -> bool:
    """Solve the puzzle in-place using backtracking."""
    empty = find_empty(board)
    if not empty:
        return True
    row, col = empty
    for candidate in sorted(valid_numbers(board, row, col)):
        board[row][col] = candidate
        if solve(board):
            return True
        board[row][col] = 0
    return False


def solve_puzzle(puzzle: Sequence[str]) -> Board:
    board = parse_puzzle(puzzle)
    if not solve(board):
        raise ValueError("Sudoku puzzle cannot be solved")
    return board


def pretty_board(board: Board) -> str:
    lines = []
    for r, row in enumerate(board):
        if r % 3 == 0 and r:
            lines.append("------+-------+------")
        chunks = []
        for c, value in enumerate(row):
            if c % 3 == 0 and c:
                chunks.append("|")
            chunks.append(str(value) if value else ".")
        lines.append(" ".join(chunks))
    return "\n".join(lines)


__all__ = [
    "Board",
    "parse_puzzle",
    "serialize_board",
    "solve",
    "solve_puzzle",
    "pretty_board",
]
