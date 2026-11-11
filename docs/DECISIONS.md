# Architecture Decisions

- **Three-part architecture:** Dabao target; M5Stick operator UI; Manjaro host. USB connections are independent.
- **BIO-sim first:** establish reproducible simulation before hardware flashing.
- **Language boundaries:** C for BIO programs as upstream specifies; Rust for supported Xous apps; C/C++ for M5Stick firmware; Python host; React/TypeScript dashboard.
- **Manjaro native:** no Docker/WSL requirement; verify upstream Linux support and inspect storage before installs.
- **Safety:** flashing, erasing, update-volume writes, privileged changes and AUR require explicit approval.
