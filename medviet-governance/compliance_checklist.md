# NĐ13/2023 Compliance Checklist - MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data production lưu trên region/server đặt tại Việt Nam.
- [x] Backup được mã hóa và lưu trong lãnh thổ VN, có retention policy 30/90/365 ngày.
- [x] Mọi transfer data ra ngoài VN phải đi qua approval workflow và audit log.

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training.
- [x] Có API/process để user rút consent và kích hoạt Right to Erasure.
- [x] Lưu consent record với timestamp, consent version và purpose.

## C. Breach Notification (72h)
- [x] Có incident response plan với owner, severity và escalation matrix.
- [x] Alert tự động khi phát hiện breach qua SIEM/Prometheus/Alertmanager.
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h.

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer.
- [x] DPO có thể liên hệ tại: dpo@medviet.example

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio-compatible recognizers) | Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | Done | Platform Team |
| Encryption | AES-256-GCM envelope encryption at rest, TLS 1.3 in transit | Done | Infra Team |
| Audit logging | Structured API access logs with user, role, resource, action, decision, request_id and immutable daily export | Planned | Platform Team |
| Breach detection | Prometheus alerts + SIEM correlation for unusual access, bulk export, failed auth spikes and policy-denied attempts | Planned | Security Team |

## F. Remaining Implementation Detail
- Audit logging: implement FastAPI middleware that emits JSON logs for every protected endpoint, forwards logs to a WORM object store bucket in VN, and keeps searchable indexes for 1 year.
- Breach detection: add Prometheus counters for denied access, token failures and high-volume reads; configure Alertmanager thresholds and incident tickets for severity P1/P2.
- Right to Erasure: maintain a consent and deletion ledger keyed by `patient_id`; block future training jobs from loading revoked subjects.
- Key management: replace local `.vault_key` with KMS/HSM-managed KEK in production, rotate KEK quarterly and rotate DEKs per dataset export.
