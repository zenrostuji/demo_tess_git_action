"""Tests for the Sudoku demo used in CI examples."""

from . import sudoku

PUZZLE = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


def test_solver_finds_solution():
    board = sudoku.parse_puzzle(PUZZLE)
    solved = sudoku.solve(board)
    assert solved, "Solver should resolve the sample puzzle"
    assert sudoku.serialize_board(board) == SOLUTION


def test_solve_puzzle_wrapper_returns_board():
    board = sudoku.solve_puzzle(PUZZLE)
    assert sudoku.serialize_board(board) == SOLUTION


def test_pretty_board_formatting_contains_grid_lines():
    board = sudoku.solve_puzzle(PUZZLE)
    pretty = sudoku.pretty_board(board)
    assert "------" in pretty
    assert pretty.count("\n") == 10


def test_unsolvable_puzzle_raises_value_error():
    bad_puzzle = list(PUZZLE)
    bad_puzzle[-1] = "1"
    try:
        sudoku.solve_puzzle(bad_puzzle)
    except ValueError:
        return
    raise AssertionError("Unsolvable puzzle should raise ValueError")

