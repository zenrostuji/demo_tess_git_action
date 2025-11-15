# GitHub Action: TLS Scanner CI

Plugin GitHub Actions này giúp bạn chạy trình quét TLS/HTTP của dự án trực tiếp trong pipeline CI/CD. Action sẽ cài đặt Python, các dependency cần thiết và thực thi `scanner.py scan` với danh sách mục tiêu bạn cung cấp. Kết quả được in ra console và lưu thành file JSON để làm artefact hoặc phân tích tiếp.

## Cách sử dụng

1. Đảm bảo workflow check-out mã nguồn trước:

```yaml
deploy:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Chạy TLS scanner
      uses: ./scanner/check_git_action
      with:
        targets: |
          https://nginx_good:8443
          https://nginx_bad:9443
```

Mặc định action sẽ tìm `scanner.py` trong thư mục `scanner/`. Nếu dự án của bạn đặt ở vị trí khác, truyền thêm `working-directory`.

## Tham số đầu vào

| Input | Mặc định | Mô tả |
|-------|----------|-------|
| `targets` | *(bắt buộc)* | Danh sách URL/domain cần quét (mỗi dòng một giá trị). |
| `working-directory` | `scanner` | Thư mục chứa `scanner.py` và `requirements.txt`. |
| `python-version` | `3.10` | Phiên bản Python dùng cho workflow. |
| `install-playwright` | `false` | Bật `true` để tải Chromium (dùng cho crawler render JavaScript). |
| `fail-on` | `NONE` | Ngưỡng rủi ro khiến job thất bại (`NONE`, `LOW`, `MEDIUM`, `HIGH`). |
| `report-path` | `tls_scan_report.json` | File JSON report đầu ra (tương đối so với working-directory). |

## Giá trị đầu ra

| Output | Mô tả |
|--------|--------|
| `report-path` | Đường dẫn tới file JSON chứa toàn bộ kết quả quét. |

## Ví dụ nâng cao

```yaml
name: security-scan
on:
  push:
    branches: [ main ]

jobs:
  tls-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: TLS scan với Playwright và fail nếu rủi ro cao
        uses: ./scanner/check_git_action
        with:
          working-directory: scanner
          python-version: '3.11'
          install-playwright: true
          fail-on: HIGH
          targets: |
            https://example.com
            intranet.example.local
      - name: Lưu artefact báo cáo
        uses: actions/upload-artifact@v4
        with:
          name: tls-scan-report
          path: scanner/tls_scan_report.json
```

## Lưu ý

- Playwright chỉ cần thiết khi bạn muốn crawler tự động render các trang dùng JavaScript. Nếu không cần, giữ `install-playwright` ở `false` để tiết kiệm thời gian build.
- Action sử dụng `modules.reporter.print_summary` để in kết quả chi tiết; file JSON giúp bạn tích hợp tiếp với các hệ thống cảnh báo hoặc dashboard.
- Nếu bạn muốn mở rộng (ví dụ: phân tích log, upload artefact khác), hãy chỉnh sửa bước Python trong `action.yml` hoặc thêm bước mới trong workflow của bạn.
