# Sudoku Demo

Bộ demo Sudoku dùng cho việc minh họa chạy unit test trong GitHub Actions.

## Sử dụng

```bash
python -m pytest demo_tess_git_action/sudoku_demo -q
```

Các tệp chính:

- `sudoku.py`: Bộ giải Sudoku bằng backtracking đơn giản.
- `test_sudoku.py`: Bộ test xác nhận solver hoạt động và báo lỗi nếu Sudoku vô nghiệm.
